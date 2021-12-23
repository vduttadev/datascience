"""
BindResponse - Rest Api Response
"""
import logging
import json
from .adjudicate import intake_bind_plan_raw_df


logger = logging.getLogger('control_panel')


class BindResponse:

    def __init__(self, data, meta, message):
        self.data = data
        self.meta = meta
        self.message = message


class Range:

    def __init__(self, min, max):
        self.min = min
        self.max = max


class Tiers:

    def __init__(self, tier1, tier2, tier3, tier4, tier5):
        """ Tiers class represents. """
        self.tier1 = tier1
        self.tier2 = tier2
        self.tier3 = tier3
        self.tier4 = tier4
        self.tier5 = tier5


class GenericTiers:

    def __init__(self, tier1, tier2, tier3, tier4, tier5, tier6, tier7, tier8, tier9, tier10):
        self.tier1 = tier1
        self.tier2 = tier2
        self.tier3 = tier3
        self.tier4 = tier4
        self.tier5 = tier5
        self.tier6 = tier6
        self.tier7 = tier7
        self.tier8 = tier8
        self.tier9 = tier9
        self.tier10 = tier10


class BindPlan:

    def __init__(self, bindPlan, allowedCorePEPM, allowedAddInsPEPM, paidCorePEPM, paidAddInsPEPM,
                 paidRemainingCashPEPM, coreAV, addInsAV, deductible, coinsurance, singleOopMaximum,
                 familyOopMaximum, primaryCareVisit, specialistVisit, virtualVisit, diagnosticTest,
                 imaging, tier1DrugCopay, tier2DrugCopay, tier3DrugCopay, specialtyDrugTier1Copay,
                 specialtyDrugTier2Copay, specialtyDrugTier3Copay, outpatientSurgery, emergencyRoom,
                 urgentCare, inpatientHospitalStay, addInCopayMaximum, savingsPEPMPct, savingsPEPM,
                 savingsAllowedClaimsPEPMPct, savingsAllowedClaimsPEPM, currentCostPEPM, utilizationChangeOnCore,
                 utilizationChangeOnAddIns, subsidyChangeOnCore, subsidyChangeOnAddIns, bindCostPEPM,
                 bindFee, bindSavingsGross, employerSavings, employeeSavings,
                 employerSavingsPct, employeeSavingsPct, costShareTiers, differenceTiersPct, differenceTiers,
                 enrollmentTiers, projectedFIEContribution, projectedEmployerContribution,
                 projectedEmployeeContribution, totalEnrollment, totalSelfInsuredRatesSQ, totalSelfInsuredRatesBind,
                 totalSelfInsuredRatesDifference, totalEmployerCostSQ,
                 totalEmployerCostBind, totalEmployerCostDifference, totalEmployerCostPct, totalEmployeeCostSQ,
                 totalEmployeeCostBind, totalEmployeeCostDifference, totalEmployeeCostDifferencePct,
                 totalSelfInsuredRatesPEPYSQ, totalSelfInsuredRatesBindPEPY, totalSelfInsuredRatesDifferencePEPY,
                 totalSelfInsuredRatesDifferencePEPYPct, totalEmployerCostSQPEPY, totalEmployerCostBindPEPY,
                 totalEmployerCostDifferencePEPY, totalEmployerCostPEPYPct, totalEmployeeCostSQPEPY,
                 totalEmployeeCostBindPEPY, totalEmployeeCostDifferencePEPY, totalEmployeeCostDifferencePEPYPct,
                 therapiesVisit, retailVisit, maternityStay):
        self.bindPlan = bindPlan
        self.allowedCorePEPM = allowedCorePEPM
        self.allowedAddInsPEPM = allowedAddInsPEPM
        self.paidCorePEPM = paidCorePEPM
        self.paidAddInsPEPM = paidAddInsPEPM
        self.paidRemainingCashPEPM = paidRemainingCashPEPM
        self.coreAV = coreAV
        self.addInsAV = addInsAV
        self.deductible = deductible
        self.coinsurance = coinsurance
        self.singleOopMaximum = singleOopMaximum
        self.familyOopMaximum = familyOopMaximum
        self.primaryCareVisit = primaryCareVisit
        self.specialistVisit = specialistVisit
        self.virtualVisit = virtualVisit
        self.diagnosticTest = diagnosticTest
        self.imaging = imaging
        self.tier1DrugCopay = tier1DrugCopay
        self.tier2DrugCopay = tier2DrugCopay
        self.tier3DrugCopay = tier3DrugCopay
        self.specialtyDrugTier1Copay = specialtyDrugTier1Copay
        self.specialtyDrugTier2Copay = specialtyDrugTier2Copay
        self.specialtyDrugTier3Copay = specialtyDrugTier3Copay
        self.outpatientSurgery = outpatientSurgery
        self.emergencyRoom = emergencyRoom
        self.urgentCare = urgentCare
        self.inpatientHospitalStay = inpatientHospitalStay
        self.addInCopayMaximum = addInCopayMaximum
        self.savingsPEPMPct = savingsPEPMPct
        self.savingsPEPM = savingsPEPM
        self.savingsAllowedClaimsPEPMPct = savingsAllowedClaimsPEPMPct
        self.savingsAllowedClaimsPEPM = savingsAllowedClaimsPEPM
        self.currentCostPEPM = currentCostPEPM
        self.utilizationChangeOnCore = utilizationChangeOnCore
        self.utilizationChangeOnAddIns = utilizationChangeOnAddIns
        self.subsidyChangeOnCore = subsidyChangeOnCore
        self.subsidyChangeOnAddIns = subsidyChangeOnAddIns
        self.bindCostPEPM = bindCostPEPM
        self.bindFee = bindFee
        self.bindSavingsGross = bindSavingsGross
        self.employerSavings = employerSavings
        self.employeeSavings = employeeSavings
        self.employerSavingsPct = employerSavingsPct
        self.employeeSavingsPct = employeeSavingsPct
        self.costShareTiers = costShareTiers
        self.differenceTiersPct = differenceTiersPct
        self.differenceTiers = differenceTiers
        self.enrollmentTiers = enrollmentTiers
        self.projectedFIEContribution = projectedFIEContribution
        self.projectedEmployerContribution = projectedEmployerContribution
        self.projectedEmployeeContribution = projectedEmployeeContribution
        self.totalEnrollment = totalEnrollment
        self.totalSelfInsuredRatesSQ = totalSelfInsuredRatesSQ
        self.totalSelfInsuredRatesBind = totalSelfInsuredRatesBind
        self.totalSelfInsuredRatesDifference = totalSelfInsuredRatesDifference
        self.totalSelfInsuredRatesDifference = totalSelfInsuredRatesDifference
        self.totalEmployerCostSQ = totalEmployerCostSQ
        self.totalEmployerCostBind = totalEmployerCostBind
        self.totalEmployerCostDifference = totalEmployerCostDifference
        self.totalEmployerCostPct = totalEmployerCostPct
        self.totalEmployeeCostSQ = totalEmployeeCostSQ
        self.totalEmployeeCostBind = totalEmployeeCostBind
        self.totalEmployeeCostDifference = totalEmployeeCostDifference
        self.totalEmployeeCostDifferencePct = totalEmployeeCostDifferencePct
        self.totalSelfInsuredRatesPEPYSQ = totalSelfInsuredRatesPEPYSQ
        self.totalSelfInsuredRatesBindPEPY = totalSelfInsuredRatesBindPEPY
        self.totalSelfInsuredRatesDifferencePEPY = totalSelfInsuredRatesDifferencePEPY
        self.totalSelfInsuredRatesDifferencePEPYPct = totalSelfInsuredRatesDifferencePEPYPct
        self.totalEmployerCostSQPEPY = totalEmployerCostSQPEPY
        self.totalEmployerCostBindPEPY = totalEmployerCostBindPEPY
        self.totalEmployerCostDifferencePEPY = totalEmployerCostDifferencePEPY
        self.totalEmployerCostPEPYPct = totalEmployerCostPEPYPct
        self.totalEmployeeCostSQPEPY = totalEmployeeCostSQPEPY
        self.totalEmployeeCostBindPEPY = totalEmployeeCostBindPEPY
        self.totalEmployeeCostDifferencePEPY = totalEmployeeCostDifferencePEPY
        self.totalEmployeeCostDifferencePEPYPct = totalEmployeeCostDifferencePEPYPct
        self.therapiesVisit = therapiesVisit
        self.retailVisit = retailVisit
        self.maternityStay = maternityStay

class CurrentSummaryFinancial:
    """

    """

    def __init__(self, benefitPlanId, currentPlanName, allowedCorePEPM,
                 allowedAddInsPEPM, paidCorePEPM, paidAddInsPEPM,
                 paidRemainingCashPEPM, coreAV, etier1, etier2, etier3, etier4, etier5,
                 etier6, etier7, etier8, etier9, etier10,
                 pFIEtier1, pFIEtier2, pFIEtier3, pFIEtier4, pFIEtier5, pFIEtier6,
                 pFIEtier7, pFIEtier8, pFIEtier9, pFIEtier10,
                 pEmployertier1, pEmployertier2, pEmployertier3, pEmployertier4,
                 pEmployertier5, pEmployertier6, pEmployertier7, pEmployertier8,
                 pEmployertier9, pEmployertier10,
                 pEmployeetier1, pEmployeetier2, pEmployeetier3, pEmployeetier4,
                 pEmployeetier5, pEmployeetier6, pEmployeetier7, pEmployeetier8,
                 pEmployeetier9, pEmployeetier10):
        self.benefitPlanId = benefitPlanId
        self.currentPlanName = currentPlanName
        self.allowedCorePEPM = allowedCorePEPM
        self.allowedAddInsPEPM = allowedAddInsPEPM
        self.paidCorePEPM = paidCorePEPM
        self.paidAddInsPEPM = paidAddInsPEPM
        self.paidRemainingCashPEPM = paidRemainingCashPEPM
        self.coreAV = coreAV
        enrollmentTier = GenericTiers(etier1, etier2, etier3, etier4, etier5, etier6,
                                      etier7, etier8, etier9, etier10)
        self.enrollmentTier = enrollmentTier
        projectedFIEContribution = GenericTiers(pFIEtier1, pFIEtier2, pFIEtier3, pFIEtier4, pFIEtier5, pFIEtier6,
                                                pFIEtier7, pFIEtier8, pFIEtier9, pFIEtier10)
        self.projectedFIEContribution = projectedFIEContribution
        projectedEmployerContribution = GenericTiers(pEmployertier1, pEmployertier2, pEmployertier3, pEmployertier4,
                                                     pEmployertier5, pEmployertier6, pEmployertier7, pEmployertier8,
                                                     pEmployertier9, pEmployertier10)
        self.projectedEmployerContribution = projectedEmployerContribution
        projectedEmployeeContribution = GenericTiers(pEmployeetier1, pEmployeetier2, pEmployeetier3, pEmployeetier4,
                                                     pEmployeetier5, pEmployeetier6, pEmployeetier7, pEmployeetier8,
                                                     pEmployeetier9, pEmployeetier10)
        self.projectedEmployeeContribution = projectedEmployeeContribution


class ResponseObject:
    """ Response class represents final response for rest api. """

    def __init__(self, request, result, BP):
        """ Compute response """
        self.opportunityId = request['opportunityId']
        self.caseNumber = request['caseNumber']
        self.success = 'true'
        self.groupName = request['groupName']
        self.sqComparisonBasis = 'null'
        if 'bindPlansNbr' in request:
            self.bindPlansNbr = request['bindPlansNbr']
        else:
            self.bindPlansNbr = 1
        self.currentSummaryFinancials = []
        result_data = json.loads(result)
        for plan in request['currentPlans']:
            benefitPlanId = plan['benefitPlanId']
            currentPlanName = plan['planName']
            planName = plan['planName']
            self.planName = planName
            logger.info(
                'reqtype=bindplan JSONResponse status=inprocess planName=%s' %
                (self.planName))

            value = result_data[planName]
            if value is not None:
                w_behav = result_data['w_behav']
                if w_behav is not None:
                    allowedCorePEPM = w_behav['allowed_core_PEPM']
                    allowedAddInsPEPM = w_behav['allowed_addins_PEPM']
                    paidCorePEPM = w_behav['paid_core_PEPM']
                    if 'paidAddInsPEPM' in w_behav:
                        paidAddInsPEPM = w_behav['paid_addins_PEPM']
                    else:
                        paidAddInsPEPM = 0.00
                    paidRemainingCashPEPM = w_behav['paid_remaining_cash_exp_PEPM']
                    coreAV = w_behav['core_AV']
                    etier1 = w_behav['t1_enroll']
                    etier2 = w_behav['t2_enroll']
                    etier3 = w_behav['t3_enroll']
                    etier4 = w_behav['t4_enroll']
                    etier5 = w_behav['t5_enroll']
                    etier6 = w_behav['t6_enroll']
                    etier7 = w_behav['t7_enroll']
                    etier8 = w_behav['t8_enroll']
                    etier9 = w_behav['t9_enroll']
                    etier10 = w_behav['t10_enroll']

                    pFIEtier1 = w_behav['t1_FIE']
                    pFIEtier2 = w_behav['t2_FIE']
                    pFIEtier3 = w_behav['t3_FIE']
                    pFIEtier4 = w_behav['t4_FIE']
                    pFIEtier5 = w_behav['t5_FIE']
                    pFIEtier6 = w_behav['t6_FIE']
                    pFIEtier7 = w_behav['t7_FIE']
                    pFIEtier8 = w_behav['t8_FIE']
                    pFIEtier9 = w_behav['t9_FIE']
                    pFIEtier10 = w_behav['t10_FIE']

                    pEmployertier1 = w_behav['t1_ER_cont']
                    pEmployertier2 = w_behav['t2_ER_cont']
                    pEmployertier3 = w_behav['t3_ER_cont']
                    pEmployertier4 = w_behav['t4_ER_cont']
                    pEmployertier5 = w_behav['t5_ER_cont']
                    pEmployertier6 = w_behav['t6_ER_cont']
                    pEmployertier7 = w_behav['t7_ER_cont']
                    pEmployertier8 = w_behav['t8_ER_cont']
                    pEmployertier9 = w_behav['t9_ER_cont']
                    pEmployertier10 = w_behav['t10_ER_cont']

                    pEmployeetier1 = w_behav['t1_EE_cont']
                    pEmployeetier2 = w_behav['t2_EE_cont']
                    pEmployeetier3 = w_behav['t3_EE_cont']
                    pEmployeetier4 = w_behav['t4_EE_cont']
                    pEmployeetier5 = w_behav['t5_EE_cont']
                    pEmployeetier6 = w_behav['t6_EE_cont']
                    pEmployeetier7 = w_behav['t7_EE_cont']
                    pEmployeetier8 = w_behav['t8_EE_cont']
                    pEmployeetier9 = w_behav['t9_EE_cont']
                    pEmployeetier10 = w_behav['t10_EE_cont']

            currentSummaryFinancial = CurrentSummaryFinancial(benefitPlanId, currentPlanName, allowedCorePEPM,
                                                              allowedAddInsPEPM, paidCorePEPM, paidAddInsPEPM,
                                                              paidRemainingCashPEPM, coreAV, etier1, etier2, etier3,
                                                              etier4, etier5, etier6, etier7, etier8, etier9, etier10,
                                                              pFIEtier1, pFIEtier2, pFIEtier3, pFIEtier4, pFIEtier5,
                                                              pFIEtier6, pFIEtier7, pFIEtier8, pFIEtier9, pFIEtier10,
                                                              pEmployertier1, pEmployertier2, pEmployertier3,
                                                              pEmployertier4, pEmployertier5, pEmployertier6,
                                                              pEmployertier7, pEmployertier8, pEmployertier9,
                                                              pEmployertier10, pEmployeetier1, pEmployeetier2,
                                                              pEmployeetier3, pEmployeetier4, pEmployeetier5,
                                                              pEmployeetier6, pEmployeetier7, pEmployeetier8,
                                                              pEmployeetier9, pEmployeetier10)
            self.currentSummaryFinancials.append(currentSummaryFinancial)
            desiredBindPlan = request['desiredBindPlan']
            for plan in request['desiredBindPlan']:
                if 'bindStandardModel' in desiredBindPlan:
                    bindPlan = desiredBindPlan['bindStandardModel']['description']
                else:
                    bindPlan = 'Bind Plan'
                w_behav = result_data['w_behav']
                if w_behav is not None:
                    allowedCorePEPM = w_behav['allowed_core_PEPM']
                    allowedAddInsPEPM = w_behav['allowed_addins_PEPM']
                    paidCorePEPM = w_behav['paid_core_PEPM']
                    paidRemainingCashPEPM = w_behav['paid_remaining_cash_exp_PEPM']
                    if 'addin_AV' in w_behav:
                        addInsAV = w_behav['addin_AV']
                    else:
                        addInsAV = 0
                    if 'chart_metric_$_savings_paid_PEPM' in w_behav:
                        savingsPEPM = w_behav['chart_metric_$_savings_paid_PEPM']
                    else:
                        savingsPEPM = 0
                    deductible = 0  # Fixed value
                    coinsurance = 100  # fixed value
                    bind_plan_raw_df = BP.to_raw_df()
                    (global_vals, std_copay, smart_copay_df) = intake_bind_plan_raw_df(bind_plan_raw_df)
                    singleOopMaximum = float(global_vals['oopm_ind'])
                    familyOopMaximum = float(global_vals['oopm_fam'])
                    primaryCareVisit = Range(
                        smart_copay_df['copay_min']['XX00001'],
                        smart_copay_df['copay_max']['XX00001'])
                    retailVisit = bind_plan_raw_df.loc[bind_plan_raw_df['item'] == 'XX00009', 'copay_min'].iat[0]

                    specialistVisit = Range(
                        smart_copay_df['copay_min']['XX00001'],
                        smart_copay_df['copay_max']['XX00001'])

                    virtualVisit = 0  # Fixed Value
                    diagnosticTest = 0  # Fixed Value
                    therapiesVisit = Range(
                        smart_copay_df['copay_min']['SMRT001'],
                        smart_copay_df['copay_max']['SMRT001'])
                    maternityStay = Range(
                        smart_copay_df['copay_min']['SMRT003'],
                        smart_copay_df['copay_max']['SMRT003'])
                    imaging = Range(
                        smart_copay_df['copay_min']['SMRT004'],
                        smart_copay_df['copay_max']['SMRT004'])
                    tier1DrugCopay = float(std_copay['Rx30001'])
                    tier2DrugCopay = float(std_copay['Rx30002'])
                    tier3DrugCopay = float(std_copay['Rx30003'])
                    if 'Rx30SP1' in std_copay:
                        specialtyDrugTier1Copay = float(std_copay['Rx30SP1'])
                    else:
                        specialtyDrugTier1Copay = None
                    if 'Rx30SP2' in std_copay:
                        specialtyDrugTier2Copay = float(std_copay['Rx30SP2'])
                    else:
                        specialtyDrugTier2Copay = None
                    if 'Rx30SP3' in std_copay:
                        specialtyDrugTier3Copay = float(std_copay['Rx30SP3'])
                    else:
                        specialtyDrugTier3Copay = None
                    if 'XX00003' in std_copay:
                        outpatientSurgery = float(std_copay['XX00003'])
                    else:
                        outpatientSurgery = None
                    if 'XX00006' in std_copay:
                        emergencyRoom = float(std_copay['XX00006'])
                    else:
                        emergencyRoom = None
                    if 'XX00008' in std_copay:
                        urgentCare = float(std_copay['XX00008'])
                    else:
                        urgentCare = None
                    if 'XX00005' in std_copay:
                        inpatientHospitalStay = float(std_copay['XX00005'])
                    else:
                        inpatientHospitalStay = None

                    addInCopayMaximum = desiredBindPlan['addinCopayMax']
                    if 'chart_metric_$_savings_paid_PEPM' in w_behav:
                        savingsPEPMPct = w_behav['chart_metric_$_savings_paid_PEPM']
                    else:
                        savingsPEPM = 0
                    if 'chart_metric_%_savings_paid_PEPM' in w_behav:
                        savingsAllowedClaimsPEPMPct = w_behav['chart_metric_%_savings_paid_PEPM']
                    else:
                        savingsAllowedClaimsPEPMPct = 0
                    if 'chart_metrics_WF_current' in w_behav:
                        currentCostPEPM = w_behav['chart_metrics_WF_current']
                    else:
                        currentCostPEPM = 0
                    if 'chart_metrics_WF_util_change_core' in w_behav:
                        utilizationChangeOnCore = w_behav['chart_metrics_WF_util_change_core']
                    else:
                        utilizationChangeOnCore = 0

                    if 'chart_metrics_WF_util_change_addins' in w_behav:
                        utilizationChangeOnAddIns = w_behav['chart_metrics_WF_util_change_addins']
                    else:
                        utilizationChangeOnAddIns = 0

                    if 'subsidyChangeOnCore' in w_behav:
                        subsidyChangeOnCore = w_behav['subsidyChangeOnCore']
                    else:
                        subsidyChangeOnCore = 0
                    if 'chart_metrics_WF_subs_change_addin' in w_behav:
                        subsidyChangeOnAddIns = w_behav['chart_metrics_WF_subs_change_addin']
                    else:
                        subsidyChangeOnAddIns = 0
                    if 'chart_metrics_WF_bind' in w_behav:
                        bindCostPEPM = w_behav['chart_metrics_WF_bind']
                    else:
                        bindCostPEPM = 0
                    if 'bindFee' in w_behav:
                        bindFee = w_behav['bindFee']
                    else:
                        bindFee = 0
                    if 'bindSavingsGross' in w_behav:
                        bindSavingsGross = w_behav['bindSavingsGross']
                    else:
                        bindSavingsGross = None
                    if 'ER-$_savings' in w_behav:
                        employerSavings = w_behav['ER-$_savings']
                    else:
                        employerSavings = 0
                    if 'ER-%_savings' in w_behav:
                        employerSavingsPct = w_behav['ER-%_savings']
                    else:
                        employerSavingsPct = 0
                    if 'EE-%_savings' in w_behav:
                        employeeSavingsPct = w_behav['EE-%_savings']
                    else:
                        employeeSavingsPct = 0
                    if 'EE-$_savings' in w_behav:
                        employeeSavings = w_behav['EE-$_savings']
                    else:
                        employeeSavings = 0

                    costShareTiers = GenericTiers(w_behav['t1_cost_share'],
                                                  w_behav['t2_cost_share'],
                                                  w_behav['t3_cost_share'],
                                                  w_behav['t4_cost_share'],
                                                  w_behav['t5_cost_share'],
                                                  w_behav['t6_cost_share'],
                                                  w_behav['t7_cost_share'],
                                                  w_behav['t8_cost_share'],
                                                  w_behav['t9_cost_share'],
                                                  w_behav['t10_cost_share'])

                    #  Mapped to Null -- Kept for Future change -- These fields are needed
                    # to compare or a reference to the base plan
                    differenceTiersPct = None

                    #  Mapped to Null -- Kept Future change -- These fields are needed
                    # to compare or a reference to the base plan
                    differenceTiers = None

                    # migrationAssumptionPct = w_behav['migrationAssumptionPct']
                    enrollmentTiers = GenericTiers(w_behav['t1_enroll'],
                                                   w_behav['t2_enroll'],
                                                   w_behav['t3_enroll'],
                                                   w_behav['t4_enroll'],
                                                   w_behav['t5_enroll'],
                                                   w_behav['t6_enroll'],
                                                   w_behav['t7_enroll'],
                                                   w_behav['t8_enroll'],
                                                   w_behav['t9_enroll'],
                                                   w_behav['t10_enroll'])
                    projectedFIEContribution = GenericTiers(w_behav['t1_FIE'],
                                                            w_behav['t2_FIE'],
                                                            w_behav['t3_FIE'],
                                                            w_behav['t4_FIE'],
                                                            w_behav['t5_FIE'],
                                                            w_behav['t6_FIE'],
                                                            w_behav['t7_FIE'],
                                                            w_behav['t8_FIE'],
                                                            w_behav['t9_FIE'],
                                                            w_behav['t10_FIE'])

                    projectedEmployerContribution = GenericTiers(w_behav['t1_ER_cont'],
                                                                 w_behav['t2_ER_cont'],
                                                                 w_behav['t3_ER_cont'],
                                                                 w_behav['t4_ER_cont'],
                                                                 w_behav['t5_ER_cont'],
                                                                 w_behav['t6_ER_cont'],
                                                                 w_behav['t7_ER_cont'],
                                                                 w_behav['t8_ER_cont'],
                                                                 w_behav['t9_ER_cont'],
                                                                 w_behav['t10_ER_cont'])

                    projectedEmployeeContribution = GenericTiers(w_behav['t1_EE_cont'],
                                                                 w_behav['t2_EE_cont'],
                                                                 w_behav['t3_EE_cont'],
                                                                 w_behav['t4_EE_cont'],
                                                                 w_behav['t5_EE_cont'],
                                                                 w_behav['t6_EE_cont'],
                                                                 w_behav['t7_EE_cont'],
                                                                 w_behav['t8_EE_cont'],
                                                                 w_behav['t9_EE_cont'],
                                                                 w_behav['t10_EE_cont'])
                    totalEnrollment = w_behav['total_enrollment']
                    totalSelfInsuredRatesSQ = w_behav['agg_tot_self_funded_rates_SQ']
                    totalSelfInsuredRatesBind = w_behav['agg_tot_self_funded_rates_bind']
                    totalSelfInsuredRatesDifference = w_behav['agg_tot_$_diff_self_funded_rate']
                    totalSelfInsuredRatesDifferencePEPYPct = w_behav['PEPY_%_diff_self_funded_rates']
                    totalEmployerCostSQ = w_behav['agg_tot_ER_cost_SQ']
                    totalEmployeeCostSQ = w_behav['agg_tot_EE_cost_SQ']
                    totalEmployeeCostBind = w_behav['agg_tot_EE_cost_bind']
                    totalEmployeeCostDifference = w_behav['agg_tot_$_diff_EE_cost']
                    totalEmployeeCostDifferencePct = w_behav['agg_tot_%_diff_EE_cost']
                    totalSelfInsuredRatesPEPYSQ = w_behav['PEPY_self_funded_rates_SQ']
                    totalSelfInsuredRatesBindPEPY = w_behav['PEPY_self_funded_rates_bind']
                    totalSelfInsuredRatesDifferencePEPY = w_behav['PEPY_$_diff_self_funded_rates']
                    totalSelfInsuredRatesDifferencePEPYPct = w_behav['PEPY_%_diff_self_funded_rates']
                    totalEmployerCostSQPEPY = w_behav['PEPY_ER_cost_SQ']
                    totalEmployerCostBindPEPY = w_behav['PEPY_ER_cost_bind']
                    totalEmployerCostDifferencePEPY = w_behav['PEPY_$_diff_ER_cost']
                    totalEmployerCostPEPYPct = w_behav['PEPY_%_diff_ER_cost']
                    totalEmployeeCostSQPEPY = w_behav['PEPY_EE_cost_SQ']
                    totalEmployeeCostBindPEPY = w_behav['PEPY_EE_cost_bind']
                    totalEmployeeCostDifferencePEPY = w_behav['PEPY_$_diff_EE_cost']
                    totalEmployeeCostDifferencePEPYPct = w_behav['PEPY_%_diff_EE_cost']
                    savingsAllowedClaimsPEPM = w_behav['chart_metric_%_savings_allowed_PEPM']
                    totalEmployerCostBind = w_behav['agg_tot_ER_cost_bind']
                    totalEmployerCostDifference = w_behav['agg_tot_$_diff_ER_cost']
                    totalEmployerCostPct = w_behav['agg_tot_%_diff_ER_cost']

                self.bindPlan = BindPlan(bindPlan, allowedCorePEPM, allowedAddInsPEPM, paidCorePEPM, paidAddInsPEPM,
                                         paidRemainingCashPEPM, coreAV, addInsAV, deductible, coinsurance,
                                         singleOopMaximum, familyOopMaximum, primaryCareVisit, specialistVisit,
                                         virtualVisit, diagnosticTest, imaging, tier1DrugCopay, tier2DrugCopay,
                                         tier3DrugCopay, specialtyDrugTier1Copay, specialtyDrugTier2Copay,
                                         specialtyDrugTier3Copay, outpatientSurgery, emergencyRoom,
                                         urgentCare, inpatientHospitalStay, addInCopayMaximum, savingsPEPMPct,
                                         savingsPEPM, savingsAllowedClaimsPEPMPct, savingsAllowedClaimsPEPM,
                                         currentCostPEPM, utilizationChangeOnCore, utilizationChangeOnAddIns,
                                         subsidyChangeOnCore, subsidyChangeOnAddIns, bindCostPEPM,
                                         bindFee, bindSavingsGross, employerSavings,
                                         employeeSavings, employerSavingsPct, employeeSavingsPct, costShareTiers,
                                         differenceTiersPct, differenceTiers, enrollmentTiers,
                                         projectedFIEContribution, projectedEmployerContribution,
                                         projectedEmployeeContribution, totalEnrollment, totalSelfInsuredRatesSQ,
                                         totalSelfInsuredRatesBind, totalSelfInsuredRatesDifference, totalEmployerCostSQ,
                                         totalEmployerCostBind, totalEmployerCostDifference, totalEmployerCostPct,
                                         totalEmployeeCostSQ, totalEmployeeCostBind, totalEmployeeCostDifference,
                                         totalEmployeeCostDifferencePct, totalSelfInsuredRatesPEPYSQ,
                                         totalSelfInsuredRatesBindPEPY, totalSelfInsuredRatesDifferencePEPY,
                                         totalSelfInsuredRatesDifferencePEPYPct, totalEmployerCostSQPEPY,
                                         totalEmployerCostBindPEPY, totalEmployerCostDifferencePEPY,
                                         totalEmployerCostPEPYPct, totalEmployeeCostSQPEPY, totalEmployeeCostBindPEPY,
                                         totalEmployeeCostDifferencePEPY, totalEmployeeCostDifferencePEPYPct, therapiesVisit,
                                         retailVisit, maternityStay)
            #    logger.info('type=JSONResponse status=created')

    def createResponse(self, request, result_data):
        """ Compute Response  """
        for plan in request['currentPlans']:
            planName = plan['planName']
            self.planName = planName
            values = result_data[planName]
            if values is not None:
                w_behav = result_data['w_behav']
                if w_behav is not None:
                    self.allowedCorePEPM = w_behav['allowed_core_PEPM']
                    self.allowedAddInsPEPM = w_behav['allowed_addins_PEPM']
                    self.paidCorePEPM = w_behav['paid_core_PEPM']
                    self.paidAddInsPEPM = w_behav['paid_addins_PEPM']
                    self.paidRemainingCashPEPM = w_behav['paid_remaining_cash_exp_PEPM']
                    self.coreAV = w_behav['core_AV']
                    self.addInsAV = w_behav['addin_AV']
                    # self.deductible =
                    self.savingsPEPMPct = w_behav['chart_metric_%_savings_paid_PEPM']
                    self.savingsPEPM = w_behav['chart_metric_$_savings_paid_PEPM']
                    self.savingsAllowedClaimsPEPM = w_behav['chart_metric_$_savings_allowed_PEPM']
                    self.savingsAllowedClaimsPEPMPct = w_behav['chart_metric_%_savings_allowed_PEPM']
                    self.currentCostPEPM = w_behav['chart_metrics_WF_current']
                    self.utilizationChangeOnCore = w_behav['chart_metrics_WF_util_change_core']
                    self.utlizationChangeOnAddIns = w_behav['chart_metrics_WF_util_change_addins']
                    self.subsidyChangeOnCore = w_behav['chart_metrics_WF_subs_change_core']
                    self.subsidyChangeOnAddIns = w_behav['chart_metrics_WF_subs_change_addin']
                    self.bindCostPEPM = w_behav['chart_metrics_WF_bind']
                    self.tradReplacedMonthlyCost = w_behav['trad_replaced_monthly_plan_cost']
                    self.tradReplacedMonthlyCostER = w_behav['trad_replaced_monthly_ER_cost']
                    self.bindFee = w_behav['bind_fee']
                    # self.stopLossISL = ''
                    # self.stopLossASL = ''

                    self.bindSavingsGross = w_behav['bind_savings_gross']
                    self.employerSavings = w_behav['ER-$_savings']
                    self.employeeSavings = w_behav['EE-$_savings']
                    self.employerSavingsPct = w_behav['ER-%_savings']
                    self.employeeSavingsPct = w_behav['EE-%_savings']
                    _costShareTiers = Tiers(
                        w_behav['t1_cost_share'],
                        w_behav['t2_cost_share'],
                        w_behav['t3_cost_share'],
                        w_behav['t4_cost_share'],
                        w_behav['t5_cost_share'])
                    self.costShareTiers = _costShareTiers
                    self.differenceTiersPct = ''  # todo
                    self.differenceTiers = ''  # todo

                    self.migrationAssumptionPct = ''  # TODO
                    _enrollmentTiers = Tiers(
                        w_behav['t1_enroll'],
                        w_behav['t2_enroll'],
                        w_behav['t3_enroll'],
                        w_behav['t4_enroll'],
                        w_behav['t5_enroll'])
                    self.enrollmentTiers = _enrollmentTiers

                    _projectedFIEContribution = Tiers(
                        w_behav['t1_FIE'],
                        w_behav['t2_FIE'],
                        w_behav['t3_FIE'],
                        w_behav['t4_FIE'],
                        w_behav['t5_FIE'])
                    self.projectedFIEContribution = _projectedFIEContribution

                    _projectedEmployerContribution = Tiers(
                        w_behav['t1_ER_cont'],
                        w_behav['t2_ER_cont'],
                        w_behav['t3_ER_cont'],
                        w_behav['t4_ER_cont'],
                        w_behav['t5_ER_cont'])
                    self.projectedEmployerContribution = _projectedEmployerContribution

                    _projectedEmployeeContribution = Tiers(
                        w_behav['t1_EE_cont'],
                        w_behav['t2_EE_cont'],
                        w_behav['t3_EE_cont'],
                        w_behav['t4_EE_cont'],
                        w_behav['t5_EE_cont'])
                    self.projectedEmployeeContribution = _projectedEmployeeContribution

                    self.totalEnrollment = w_behav['total_enrollment']
                    self.totalSelfInsuredRatesSQ = w_behav['agg_tot_self_funded_rates_SQ']

                    self.totalSelfInsuredRatesBind = w_behav['agg_tot_self_funded_rates_bind']

                    self.totalSelfInsuredRatesDifference = w_behav['agg_tot_$_diff_self_funded_rate']
                    self.totalSelfInsuredRatesDifferencePEPYPct = w_behav[
                        'agg_tot_%_diff_self_funded_rate']
                    self.totalEmployerCostSQ = w_behav['agg_tot_ER_cost_SQ']
                    self.totalEmployerCostBind = w_behav['agg_tot_ER_cost_bind']
                    self.totalEmployerCostDifference = w_behav['agg_tot_$_diff_ER_cost']
                    self.totalEmployerCostPct = w_behav['agg_tot_%_diff_ER_cost']
                    self.totalEmployeeCostSQ = w_behav['agg_tot_EE_cost_SQ']
                    self.totalEmployeeCostBind = w_behav['agg_tot_EE_cost_bind']
                    self.totalEmployeeCostDifference = w_behav['agg_tot_$_diff_EE_cost']
                    self.totalEmployeeCostDifferencePct = w_behav['agg_tot_%_diff_EE_cost']
                    self.totalSelfInsuredRatesPEPYSQ = w_behav['PEPY_self_funded_rates_SQ']
                    self.totalSelfInsuredRatesBindPEPY = w_behav['PEPY_self_funded_rates_bind']
                    self.totalSelfInsuredRatesDifferencePEPY = w_behav['PEPY_$_diff_self_funded_rates']
                    self.totalSelfInsuredRatesDifferencePEPYPct = w_behav[
                        'PEPY_%_diff_self_funded_rates']
                    self.totalEmployerCostSQPEPY = w_behav['PEPY_ER_cost_SQ']
                    self.totalEmployerCostDifferencePEPY = w_behav['PEPY_$_diff_ER_cost']
                    self.totalEmployerCostPEPYPct = w_behav['PEPY_%_diff_ER_cost']
                    self.totalEmployeeCostSQPEPY = w_behav['PEPY_EE_cost_SQ']
                    self.totalEmployeeCostBindPEPY = w_behav['PEPY_EE_cost_bind']
                    self.totalEmployeeCostDifferencePEPY = w_behav['PEPY_$_diff_EE_cost']
                    self.totalEmployeeCostDifferencePEPYPct = w_behav['PEPY_%_diff_EE_cost']
                    logger.info('type=bindplanApi-JSONResponse status=created')


def obj_to_dict(obj):
    return obj.__dict__
