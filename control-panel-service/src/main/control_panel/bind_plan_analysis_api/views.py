
from common import getBindPlanResponse
from .models import Message
from .bque_wrapper import PlanCombiner
from .adjudicate import BindEvaluator
from .bindResponse import ResponseObject, BindResponse, obj_to_dict
from django.http import JsonResponse
from .mapper import BindPlanJSON, getRefTable
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view

from django.http import HttpResponse
from trad_plan_analysis.models import ExistingPlan

import logging
import json
import pandas
import time
import common
import sys
import traceback


if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO


# Create your views here.

logger = logging.getLogger('control_panel')


@api_view(['POST'])
def bind_plan(request):
    if request.method == 'GET':
        resp = do_get(request)
    elif request.method == 'POST':
        resp = do_post(request)
    return resp


@csrf_exempt
def isAlive(request):
    if request.method == 'GET':
        resp = do_getSvc(request)
    elif request.method == 'POST':
        resp = do_getSvc(request)
    return resp


def do_getSvc(request):
    return HttpResponse("Service is up and running")


def do_get(request):
    return HttpResponse("Get method not supported. Try Post")


def getValueByKey(key, ls):
    for item in ls:
        if item[0] == key:
            return item[1]


def getValueByKeyUUID(key, ls):
    for item in ls:
        if item[0] == key:
            return item[1]


def do_post(request):
    response = JsonResponse({}, safe=False)
    opportunityId = ''
    benefitPlanId = ''
    caseNumber = ''
    error_objects = []
    messageId = ''
    try:
        t1 = time.time()
        value = json.loads(request.body)
        messageId = value['requestId']
        opportunityId = value['opportunityId']
        benefitPlanId = value['currentPlans'][0]['benefitPlanId']
        caseNumber = value['caseNumber']
        message = Message(
            message_id=messageId,
            opportunity_id=opportunityId,
            input_data=value,
            output_data='',
            status='recieved')
        message.save()
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=recieved' %
            (messageId, opportunityId))
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=bindplan type=api status=recieved req=%s' %
            (messageId, opportunityId, value))
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=db-call process=getting additional pricing from db' %
            (messageId, opportunityId))
        # this can be cached and kept as dictionary
        addin_costs_df = getRefTable('public.adj_model_addin_pricing')
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=mapping' %
            (messageId, opportunityId))
        BP = BindPlanJSON(value, addin_costs_df)

        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=mapping-done' %
            (messageId, opportunityId))
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=api status=mapping-done json=%s' %
            (messageId, opportunityId, BP))
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=adjudication' %
            (messageId, opportunityId))
        bind_df = BP.to_raw_df()
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=api status=adjudication bind_df=%s' %
            (messageId, opportunityId, bind_df))
        global_stats = BP.get_global_stats()
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=api status=adjudication global_stats=%s' %
            (messageId, opportunityId, global_stats))
        plan_stats = BP.get_plan_stats_list()
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=api status=adjudication plan_stats=%s' %
            (messageId, opportunityId, plan_stats))

        listOfKeys = list()
        for item in plan_stats:
            listOfKeys.append(item[0])
        existingPlans = ExistingPlan.objects.filter(
            opportunity_id=opportunityId
        )
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=processing process=found matching traditional_plan' %
            (messageId, opportunityId))
        # Iterating over keys
        summary_stats_dict = {}

        BE = BindEvaluator()

        if existingPlans is not None:
            for existingPlan in existingPlans:
                trad_df = existingPlan.analysis_results
                exitingPlanData = StringIO(trad_df)
                data = pandas.read_csv(exitingPlanData, sep=",")
                df = pandas.DataFrame(data)
                logger.info(
                    'message_id=%s opportunity_id=%s reqType=api status=processing process=Trad plan to dataframe' %
                    (messageId, opportunityId))
                pid = str(existingPlan.benefitplan_id)
                logger.info("PID======== %s" % (pid))
                BE.intake_bind_raw_df(bind_df)
                BE.intake_trad_df(df)
                summary_stat = BE.get_summary_stats()
                logger.info(
                    'message_id=%s opportunity_id=%s reqType=api status=processing process=generate summary stats' %
                    (messageId, opportunityId))
                summary_stats_dict[pid] = summary_stat
        else:
            errorMessage = common.INVALID_REQUEST_E03
            error_objects.append(
                common.ResponseError(
                    common.INVALID_REQUEST_E03,
                    errorMessage))
            m, json_data = getBindPlanResponse(
                '400', opportunityId, benefitPlanId, messageId, caseNumber, 'false', error_objects)
            json_string_response = json.loads(json_data)
            response = JsonResponse(
                json_string_response, safe=False, status=204)
            logger.info(
                'message_id=%s and opportunity_id= %s type=api status=error-sent error=%s' %
                (messageId, opportunityId, str(errorMessage)))
            return response

        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=adjudication-done' %
            (messageId, opportunityId))
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=bque-wrapper' %
            (messageId, opportunityId))
        PC = PlanCombiner(global_stats)
        if len(summary_stats_dict) > 0:
            for key in listOfKeys:
                pepy_df = pandas.DataFrame(summary_stats_dict.get(key))
                plan_stats_df = pandas.DataFrame(
                    getValueByKey(key, plan_stats))
                PC.load_plan(pepy_df, plan_stats_df)

        PC.run_plans()
        combined_results = PC.get_combined_results()
        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=bque-wrapper-done process=getting combined result' %
            (messageId, opportunityId))
        # double precison allowed maximum in pandas = 15
        resultData = combined_results.to_json(double_precision=15)
        logger.debug(
            'message_id=%s opportunity_id=%s reqType=api status=bque-wrapper-done result_json=%s' %
            (messageId, opportunityId, combined_results))

        logger.info(
            'message_id=%s opportunity_id=%s reqType=api status=response-create' %
            (messageId, opportunityId))
        responseDataObject = ResponseObject(value, resultData, BP)
        responseData = BindResponse(responseDataObject, None, None)
        json_string = json.dumps(responseData.__dict__, default=obj_to_dict)
        json_string_response = json.loads(json_string)
        message.output_data = json_string_response
        message.status = 'sent'
        message.save()
        response = JsonResponse(json_string_response, safe=False)
        t2 = time.time()
        logger.info(
            'message_id=%s opportunity_id=%s type=api status=response-sent Time-Elapsed=%s ' %
            (messageId, opportunityId, str(
                t2 - t1)))
    except Exception:
        # handling exception
        errorMessage = common.Errorcode.SYSTEM_ERROR_E00.value
        error_objects.append(
            common.ResponseError(
                common.Errorcode.SYSTEM_ERROR_E00.name,
                errorMessage))
        m, json_data = getBindPlanResponse(
            '400', opportunityId, benefitPlanId, messageId, caseNumber, 'false', error_objects)
        response = JsonResponse(json_data, safe=False, status=500)
        error = traceback.format_exc()

        logger.info(
            'message_id=%s and opportunity_id= %s type=api status=error-sent error=%s' %
            (messageId, opportunityId, str(error)))
    return response
