
import logging
import json
import time
import common
import pandas
import multiprocessing
import traceback
import os

from django.db.utils import IntegrityError
from .mapper import JSON_to_single_kafka_plan_df
from .adjudicate import run_traditional_plan, get_query_result
from django.conf import settings
from .models import ExistingPlan, Message
from common import getTradtionalPlanResponse
from kafka.producer import get_producer
from multiprocessing import Queue, Process


logger = logging.getLogger('control_panel')


def trad_wrapper(arg_list, queue):
    processId = str(os.getpid())
    arg_list = arg_list + (processId,)
    logger.info("processId=%s status=intitalizing" % (processId))
    queue.put(run_traditional_plan(*arg_list))
    logger.info("processId=%s status=finished" % (processId))
    return


def getProcessorData():
    count = settings.PROCESS_COUNT
    mod = settings.MOD
    queueSize = settings.BLOCK_QUEUE_SIZE
    if mod is None:
        mod = 100
    else:
        mod = int(mod)
    if queueSize is None:
        queueSize = 2
    else:
        queueSize = int(queueSize)
    return count, mod, queueSize


def analyze_plan(plan_data, opportunity, messageId):
    try:
        # for message in consumer:
        if plan_data is not None:
            clients_json = plan_data
            caseNumber = clients_json['caseNumber']
            # validation if required
            plan_list = clients_json['currentPlans']
            # always expect only one plan -- this is will read the first plan
            # only
            plan_dict = plan_list[0]
            opportunityId = plan_dict['opportunityId']
            benefitPlanId = plan_dict['benefitPlanId']
            tstart = time.time()
            logger.info(
                'message_id=%s status=mapping-inprocess opportunity_id=%s benefitPlan_id=%s' %
                (messageId, opportunityId, benefitPlanId))
            out = JSON_to_single_kafka_plan_df(clients_json)
            out['item'] = out.index
            t2 = time.time()
            logger.info(
                'message_id=%s status=mapping-done time_elapsed(sec)=%s' %
                (messageId, (str(
                    t2 - tstart))))
            if out is not None:
                t3 = time.time()
                logger.info(
                    'message_id=%s status=adjudication-start' %
                    (messageId))
                logger.debug(
                    'message_id=%s status=adjudication-start opportunity_id=%s benefitPlan_id=%s' %
                    (messageId, opportunityId, benefitPlanId))
                table = 'model_adjudication_table_45_v2'
                logger.info(
                    'message_id=%s status=adjudication-inprocess' %
                    (messageId))
                '''
            set up parameters required by the task
            '''
                table = 'model_adjudication_table_45_v2'
                Q_cov_fam = 'SELECT DISTINCT(cov_fam) FROM model_adjudication_cov_fam_table_45;'
                cov_fams = get_query_result(Q_cov_fam)
                logger.debug(
                    'Number of CPUs=%s' %
                    (multiprocessing.cpu_count()))
                process_count, mod, blockQueueSize = getProcessorData()
                if process_count == 1:
                    logger.debug('message_id=%s status=Starting %s process' %
                                (messageId, process_count))
                else:
                    logger.debug('message_id=%s status=Starting %s parallel process' %
                                (messageId, process_count))
                '''
            pass the task function, followed by the parameters to processors
            '''
                main_queue = Queue(maxsize=process_count)
                mod2 = mod * process_count

                processes = []
                for i in range(process_count):
                    p = Process(
                        target=trad_wrapper,
                        args=(
                            (out,
                             cov_fams,
                             table,
                             blockQueueSize,
                             mod,
                             mod2,
                             i * mod),
                            main_queue))
                    p.start()
                    processes.append(p)
                for p in processes:
                    p.join()

                t30 = time.time()

                logger.debug(
                    'message_id=%s status=adjudication-done time_elapsed(min)=%s' %
                    (messageId, str(
                        (t30 - t2) / 60)))
                logger.info(
                    'message_id=%s status=concatinating-dataframes' %
                    (messageId))
                results = []
                while len(results) < process_count:
                    if main_queue.empty():
                        time.sleep(10)
                    else:
                        results.append(main_queue.get())

                # getting the two values for [CASH000]['pay_ind'] and []
                data = pandas.concat(results)
                value = data.groupby(data.index).sum()
                cashValue_payInd = data['pay_ind'].iloc[0]
                cashValue_payFam = data['pay_fam'].iloc[0]

                value.iloc[0, value.columns.get_loc(
                    'pay_ind')] = cashValue_payInd
                value.iloc[0, value.columns.get_loc(
                    'pay_fam')] = cashValue_payFam

                t1 = time.time()
                logger.info(
                    'message_id=%s status=concatinating-dataframes-done time_elapsed(sec)=%s' %
                    (messageId, (t1 - t30)))
                stringValue = value.to_csv(index=True, header=True)
                if value is not None:
                    opportunity.save()
                    plan_model = ExistingPlan(
                        id=messageId,
                        opportunity_id=opportunityId,
                        benefitplan_id=benefitPlanId,
                        message=opportunity)
                    plan_model.analysis_results = stringValue
                    plan_model.analysis_finished = True
                    opportunity.status = 'processed'
                    try:
                        plan_model.save(force_insert=True)
                    except IntegrityError:
                        plan_model.benefitplan_id = benefitPlanId
                        plan_model.message = opportunity
                        plan_model.save(force_update=True)
                    t4 = time.time()
                    error_objects = None
                    logger.debug(
                        'message_id=%s status=adjudication-done opportunity_id=%s benefitPlan_id=%s time_elapsed=%s' %
                        (messageId, opportunityId, benefitPlanId, str(
                            t4 - t3)))
                    logger.debug('message_id=%s opportunity_id=%s benefitPlan_id=%s result=%s' %
                                 (messageId, opportunityId, benefitPlanId, stringValue))
                    logger.info(
                        'message_id=%s status=plan-saved' %
                        (messageId))
                else:
                    errorMessage = 'No result from adjudication'
                    logger.info(
                        'message_id=%s status=error-adjudicated error_code=%s error_message=%s' %
                        (messageId, common.Errorcode.SYSTEM_ERROR_E00.name, errorMessage))
                    error_objects.append(
                        common.ResponseError(
                            common.Errorcode.SYSTEM_ERROR_E00.name,
                            errorMessage))
            else:
                errorMessage = 'Unable to process incoming request.'
                logger.info(
                    'message_id=%s status=error-mapping error_message=%s' %
                    (messageId, common.Errorcode.SYSTEM_ERROR_E00.name, errorMessage))
                error_objects.append(
                    common.ResponseError(
                        common.Errorcode.SYSTEM_ERROR_E00.name,
                        errorMessage))
        else:
            logger.info(
                'message_id=null status=No-message to process at this moment......')

        m, json_data = getTradtionalPlanResponse(
            '200', opportunityId, benefitPlanId, messageId, caseNumber, 'true', error_objects)

        outgoingProducer = get_producer()
        resposne = json.dumps(json_data).encode('utf-8')
        message = Message.objects.get(message_id=messageId)
        message.status = 'sent'
        message.output_data = json_data
        message.save()
        data = json.dumps(json_data).encode('utf-8')
        outgoingProducer.produce(resposne)
        t6 = time.time()
        logger.info(
            'message_id=%s status=response-sent time_execution(min)=%s' %
            (messageId, str(
                (t6 - tstart) / 60)))
        logger.debug(
            'message_id=%s status=response-sent response=%s' %
            (messageId, json_data))

    except Exception as e:
        # Just print traceback
        error_objects = []
        t6 = time.time()
        logger.debug(
            'message_id=%s status=all-processing-done time_elapsed=%s' %
            (messageId, (str(
                t6 - tstart))))
        errorMessage = common.Errorcode.SYSTEM_ERROR_E00.value + str(e)
        error_objects.append(
            common.ResponseError(
                common.Errorcode.SYSTEM_ERROR_E00.name,
                errorMessage))
        m, json_data = getTradtionalPlanResponse(
            '400', opportunityId, benefitPlanId, messageId, caseNumber, 'false', error_objects)
        # Get traceback as a string and do something with it
        error = traceback.format_exc()
        logger.info(
            'message_id=%s status=not-Processed error=internal error error-message=%s' %
            (messageId, str(error)))
        opportunity.status = 'not-processed'
        opportunity.output_data = json_data
        opportunity.save()
        outgoingProducer = get_producer()
        resposne = json.dumps(json_data).encode('utf-8')
        outgoingProducer.produce(resposne)
