import logging
import json

logger = logging.getLogger('control_panel')


class Tiers:

    def __init__(self, tier1, tier2, tier3, tier4, tier5):
        """ Tiers class represents. """
        self.tier1 = tier1
        self.tier2 = tier2
        self.tier3 = tier3
        self.tier4 = tier4
        self.tier5 = tier5

class Range:

    def __init__(self, min, max):
        self.min = min
        self.max = max

class ResponseObject:
    """ Response class represents final response for rest api. """

    def __init__(self, request, result, retailVisit, therapiesVisitMin, therapiesVisitMax):
        """ Compute response """

        for plan in request['currentPlans']:
            planName = plan['planName']
            self.planName = planName
            logger.info(
                'reqtype=bindplan JSONResponse status=inprocess planName=%s' %
                (self.planName))
            result_data = json.loads(result)
            value = result_data[planName]
            if value is not None:
                w_behav = result_data['w_behav']
                if w_behav is not None:
                    self.allowedCorePEPM = w_behav['allowed_core_PEPM']
                    self.allowedAddInsPEPM = w_behav['allowed_addins_PEPM']
                    self.paidCorePEPM = w_behav['paid_core_PEPM']
                    self.paidAddInsPEPM = w_behav['paid_addins_PEPM']
                    self.paidRemainingCashPEPM = w_behav['paid_remaining_cash_exp_PEPM']
                    self.coreAV = w_behav['core_AV']
                    self.addInsAV = w_behav['addin_AV']
                    self.retailVisit = retailVisit
                    _therapiesVisitRange = Range(therapiesVisitMin, therapiesVisitMax)
                    self.therapiesVisit = _therapiesVisitRange
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
                    logger.info('type=JSONResponse status=created')

    def createResponse(self, request, result_data, retailVisit, therapiesVisitMin, therapiesVisitMax):
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
                    self.retailVisit = retailVisit
                    _therapiesVisitRange = Range(therapiesVisitMin, therapiesVisitMax)
                    self.therapiesVisit = _therapiesVisitRange
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
