import common
from common import getTradtionalPlanResponse


def main1():
    error_objects = []
    errorMessage = common.Errorcode.SYSTEM_ERROR_E00.value + str(e)
    error_objects.append(
        common.ResponseError(
            common.Errorcode.SYSTEM_ERROR_E00.name,
            errorMessage))
    opportunityId = 'f16dcd26-0c02-4bbb-a4f7-061b28e30cbd'
    benefitPlanId = '45f11ca5-499b-4054-a85f-d595c0fd96da'
    messageId = 'c51f1818-b0aa-4aa0-b4fc-7e176285f3dd'
    caseNumber = 'null'
    m, json_data = getTradtionalPlanResponse(
        '400', opportunityId, benefitPlanId, messageId, caseNumber, 'false', error_objects)


if __name__ == '__main__':
    main1()
