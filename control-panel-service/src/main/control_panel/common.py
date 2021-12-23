#!/usr/bin/env python
"""common functionality to generate the response for apps."""
import logging
import json
import datetime
import array as arr
from json import JSONEncoder
from uuid import UUID

# define all common objects here
from enum import Enum


LOGGER = logging.getLogger('control_panel')


def get_date(t):
    return datetime.datetime.strptime(t, '%Y-%m-%d')


def get_date_from_array(t):
    dateObject = get_datestr_from_array(t)
    return datetime.datetime.strptime(dateObject, '%Y-%m-%d')


def get_datestr_from_array(t):
    dateStr = arr.array('i', t)
    dateObject = str(dateStr[0])+'-'+str(dateStr[1])+'-'+str(dateStr[2])
    return str(dateObject)


"""Generate the Bindplan response for rest api."""


def getBindPlanResponse(
        statusCode,
        opportunityID,
        benefitPlanId,
        messageID,
        caseNumber,
        success,
        errors):
    response = ResponseDTO(
        opportunityID,
        caseNumber,
        benefitPlanId,
        success,
        errors)
    json_data = json.dumps(response, default=lambda o: o.__dict__, indent=4)
    json_string_response = json.loads(json_data)
    message = Messenger(info=statusCode, data=json_data)
    return message, json_string_response


"""Generate the Trational response for rest api."""


def getTradtionalPlanResponse(
        statusCode,
        opportunityID,
        benefitPlanId,
        messageID,
        caseNumber,
        success,
        errors):
    json_data = createMsg(
        opportunityID,
        benefitPlanId,
        messageID,
        caseNumber,
        success,
        errors)
    message = Messenger(info=statusCode, data=json_data)
    return message, json_data


def createMsg(
        opportunityID,
        benefitPlanId,
        messageId,
        caseNumber,
        success,
        errors):
    msg = {}
    msg['opportunityId'] = opportunityID
    msg['benefitPlanId'] = benefitPlanId
    msg['caseNumber'] = caseNumber
    msg['messageId'] = messageId
    msg['success'] = success
    if errors is not None:
        msg['errors'] = errors
    return msg

# Response objects


class Messenger:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


"""Generate the Error response for rest api."""


class ResponseError(object):

    """__init__() functions as the class constructor"""

    def __init__(self, errorId, errorMsg):
        self.error_id = errorId
        self.error_message = errorMsg

    @classmethod
    def from_json(cls, data):
        return cls(**data)


class ResponseDTO(object):

    """__init__() functions as the class constructor"""

    def __init__(self, opportunity_id, caseNumber, benefitPlan_id,
                 success, errors):
        self.opportunity_id = opportunity_id
        self.case_number = caseNumber
        self.success = success
        if errors is not None:
            self.errors = errors
        self.benefitplan_id = benefitPlan_id


class Errorcode(Enum):
    # Unable to process request System error: e.message
    SYSTEM_ERROR_E00 = 'Unable to process request System error:'
    DB_ERROR_E01 = 'Unable to access database:'  # Unable to reach database
    # Kafka Error : Unable to reach Kafka host
    KAFKA_ERROR_E00 = 'Kafka Error : Unable to reach Kafka host'
    # Kafka Error : Unable to connect to Kafka or invalid topic for consumer
    KAFKA_ERROR_E01 = 'Kafka Error : Invalid topic for consumer:'
    # Kafka Error : Unable to connect to Kafka or invalid topic for producer
    KAFKA_ERROR_E02 = 'Kafka Error : Invalid topic for producer:'
    INVALID_REQUEST_E01 = 'Unable to map request json:'
    # Unable to adjudicate : e.messages
    INVALID_REQUEST_E02 = 'Unable to adjudicate:'
    INVALID_REQUEST_E03 = 'No traditional plan exist for this opportunity'


JSONEncoder_olddefault = JSONEncoder.default


def JSONEncoder_newdefault(self, o):
    if isinstance(o, UUID):
        return str(o)
    return JSONEncoder_olddefault(self, o)


JSONEncoder.default = JSONEncoder_newdefault
