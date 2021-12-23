import pandas as pd
import numpy as np
import datetime
import psycopg2
import logging
import array as arr
from django.conf import settings

logger = logging.getLogger('control_panel')


def get_date(t):
    return datetime.datetime.strptime(t, '%Y-%m-%d')


def get_date_from_array(t):
    dateStr = arr.array('i', t)
    dateObject = str(dateStr[0])+'-'+str(dateStr[1])+'-'+str(dateStr[2])
    return datetime.datetime.strptime(dateObject, '%Y-%m-%d')


def none_to_zero(x):
    if x is None:
        y = 0
    else:
        y = int(x)
    return y


def bounded_interpolate(x, x_a, x_b, y_a, y_b):
    x = np.minimum(x, x_b)
    x = np.maximum(x, x_a)

    w = (x - x_a) / (x_b - x_a)

    y = w * y_b + (1 - w) * y_a
    return y


def mround(x, base=5):
    return base * round(x / base)


class BindPlanJSON:

    def __init__(
            self,
            j,
            addin_costs_df,
            truven_dtstart='2017-01-01',
            truven_dtend='2017-12-31',
            trend=0.06,
            high_target_AV=0.7,
            low_target_AV=0.9,
            bind_fee=60,
            slice_threshold=1000,
            EE_shared_savings=0.5):

        self.bind_dict = j['desiredBindPlan']

        exp_dtstart = get_date(truven_dtstart)
        exp_dtend = get_date(truven_dtend)
        exp_dtmid = exp_dtstart + (exp_dtend - exp_dtstart) / 2

        proj_dtstart = get_date_from_array(j['desiredBindEffectiveDate'])
        proj_dtend = get_date_from_array(j['desiredBindEndDate'])
        #proj_dtstart = get_date(j['desiredBindEffectiveDate'])
        #proj_dtend = get_date(j['desiredBindEndDate'])
        proj_dtmid = proj_dtstart + (proj_dtend - proj_dtstart) / 2

        eff_trend = (1 + trend)**((proj_dtmid - exp_dtmid).days / 365)

        self.global_dict = {'oopm_ind': self.bind_dict['inNetworkOopLimits']['individualOop'],
                            'oopm_fam': self.bind_dict['inNetworkOopLimits']['familyOop'],
                            'global_max_paycheck': self.bind_dict['globalMaximumAddinDeduction'],
                            'pay_period': int(j['payPeriodFrequency'][-2:]),
                            'trend': eff_trend}

        self.lines_df = pd.DataFrame(
            columns=[
                'copay_min',
                'copay_max',
                'copay_step',
                'payroll_min',
                'payroll_max',
                'payroll_step',
                'payroll_count_min',
                'payroll_count_max',
                'benefit_slope_from',
                'benefit_slope_to',
                'alpha_factor',
                'beta_factor'])

        self.trad_plan_info = pd.DataFrame(
            columns=[
                'enroll',
                'ee_tier',
                'other_tiers',
                'eff_date',
                'pay_freq',
                'name'])
        self.trad_plan_info.index.name = 'plan_id'

        for plan in j['currentPlans']:
            pid = plan['benefitPlanId']
            self.trad_plan_info.loc[pid, 'enroll'] = 0
            self.trad_plan_info.loc[pid, 'ee_tier'] = []
            self.trad_plan_info.loc[pid, 'other_tiers'] = []
            self.trad_plan_info.loc[pid, 'eff_date'] = get_date_from_array(plan['effectiveDate'])
            #self.trad_plan_info.loc[pid, 'eff_date'] = get_date(plan['effectiveDate'])
            self.trad_plan_info.loc[pid, 'name'] = plan['planName']
            self.trad_plan_info.loc[pid, 'pay_freq'] = int(
                j['employeeContributionsFrequency'][-2:])
            for tier in plan['planTiers']:
                self.trad_plan_info.loc[pid,
                                        'enroll'] += tier['currentEnrollment']
                if tier['tier']['code'] == 'EMP':
                    self.trad_plan_info.loc[pid, 'ee_tier'].append(tier)
                else:
                    self.trad_plan_info.loc[pid, 'other_tiers'].append(tier)

        self.bque_global_dict = {
            'trend': trend,
            'bind_year_start': get_date_from_array(j['desiredBindEffectiveDate']),
            # 'bind_year_start': get_date(j['desiredBindEffectiveDate']),
            'bind_fee': bind_fee,
            'EE_share_savings': EE_shared_savings}

        top_enroll_pid = self.trad_plan_info.loc[self.trad_plan_info['enroll'] == max(
            self.trad_plan_info['enroll']), :].index[0]

        for i in range(10):
            idx = i + 1
            if idx == 1:
                rate_rel = 1
                cont_rel = 1
            elif idx <= len(self.trad_plan_info.loc[top_enroll_pid, 'other_tiers']) + 1:
                ee_tier = self.trad_plan_info.loc[top_enroll_pid, 'ee_tier']
                if ee_tier:
                    rate_rel = (self.trad_plan_info.loc[top_enroll_pid, 'other_tiers'][idx - 2]['cobraRate'] /
                                self.trad_plan_info.loc[top_enroll_pid, 'ee_tier'][0]['cobraRate'])

                    cont_rel = (self.trad_plan_info.loc[top_enroll_pid, 'other_tiers'][idx -
                                                                                       2]['employeeContributions'] /
                                self.trad_plan_info.loc[top_enroll_pid, 'ee_tier'][0]['employeeContributions'])
                else:
                    rate_rel = self.trad_plan_info.loc[top_enroll_pid, 'other_tiers'][idx - 2]['cobraRate']

                    cont_rel = self.trad_plan_info.loc[top_enroll_pid, 'other_tiers'][idx - 2]['employeeContributions']
            else:
                rate_rel = 0
                cont_rel = 0
            self.bque_global_dict['rate_rel_t' + str(idx)] = rate_rel
            self.bque_global_dict['cont_rel_t' + str(idx)] = cont_rel

        if self.trad_plan_info['enroll'].sum() < slice_threshold:
            migration_main = 1
            migration_other = 1
        else:
            migration_main = .5  # NOTE THIS
            migration_other = 0

        self.plan_stats_list = []
        for i in range(len(self.trad_plan_info)):
            pid = self.trad_plan_info.index[i]
            if pid == top_enroll_pid:
                migration = migration_main
            else:
                migration = migration_other
            ee_tiers = self.trad_plan_info.loc[pid, 'ee_tier']
            if ee_tiers:
                ee_tier = ee_tiers[0]
            else:
                ee_tier = ee_tiers
            df = self.get_trad_plan_stats_df(ee_tier,
                                             self.trad_plan_info.loc[pid,
                                                                     'other_tiers'],
                                             migration,
                                             base_year=self.trad_plan_info.loc[pid,
                                                                               'eff_date'],
                                             pepm_aso=40,
                                             premium_freq=12,
                                             contribution_freq=self.trad_plan_info.loc[pid,
                                                                                       'pay_freq'],
                                             plan_name=self.trad_plan_info.loc[pid,
                                                                               'name'])

            self.plan_stats_list.append((pid, df))

        for cov_fam in self.get_not_covered_list():
            line = self.get_copay_line(cov_fam, 999999)
            self.lines_df = pd.concat([self.lines_df, line])

        for cov_fam in self.get_covered_100_list():
            line = self.get_copay_line(cov_fam, 0)
            self.lines_df = pd.concat([self.lines_df, line])

        self.high_target_AV = high_target_AV
        self.low_target_AV = low_target_AV

        json_copays = {}
        for d in self.bind_dict['bindCopays']:
            json_copays[d['treatmentTypeCode']] = d['copay']
        for d in self.bind_dict['rxCopays']:
            json_copays[d['treatmentTypeCode']] = d['copay']
        dme_list = self.get_dme_copays(to_1000=(json_copays['Z002112'] == 1000))
        for (cov_fam, copay) in dme_list:
            self.lines_df = pd.concat(
                [self.lines_df, self.get_copay_line(cov_fam, copay)])
            self.lines_df = pd.concat([self.lines_df, self.get_copay_line(
                cov_fam.replace('DME0', 'DMER'), copay / 10)])

        for cov_fam in json_copays.keys():
            if cov_fam in self.get_direct_faux_cov_fam_mapping():
                line = self.get_copay_line(
                    self.get_direct_faux_cov_fam_mapping()[cov_fam],
                    json_copays[cov_fam])
                self.lines_df = pd.concat([self.lines_df, line])

        rx_SP1_line = self.get_copay_line('Rx30SP1', json_copays['Z000904']-50)
        rx_SP3_line = self.get_copay_line('Rx30SP3', json_copays['Z000904']+50)

        rx_90_SP1_line = self.get_copay_line('Rx90SP1', mround((json_copays['Z000904']-50)*3, 5))
        rx_90_SP2_line = self.get_copay_line('Rx90SP2', mround(json_copays['Z000904']*3, 5))
        rx_90_SP3_line = self.get_copay_line('Rx90SP3', mround((json_copays['Z000904']+50)*3, 5))

        pcp_line = self.get_copay_line(
            'XX00001',
            json_copays['Z000100_MIN'],
            json_copays['Z000100_MAX'],
            5,
            0,
            1,
            1,
            1)
        scp_line = self.get_copay_line(
            'XX00002',
            json_copays['Z000100_MIN'],
            json_copays['Z000100_MAX'],
            5,
            0,
            1,
            1,
            1)

        pt_line = self.get_copay_line(
            'SMRT001',
            round(
                json_copays['Z000100'] / 2),
            json_copays['Z000200'] * 2)
        colon_line = self.get_copay_line(
            'SMRT002',
            mround(
                json_copays['Z001000'] / 3,
                50),
            json_copays['Z001000'])
        delivery_line = self.get_copay_line('SMRT003', mround(
            json_copays['Z001000'] / 2, 50), json_copays['Z001401'])
        img_line = self.get_copay_line(
            'SMRT004',
            mround(
                json_copays['Z000100'] * 2.5,
                5),
            mround(
                json_copays['Z001000'] * .75,
                25))

        high_cost_ov_line = self.get_copay_line(
            'XX00004', mround(json_copays['Z000200'] * 2.5, 5))
        amb_line = self.get_copay_line(
            'XX00007', np.minimum(
                json_copays['Z001100'] + 100, 650))
        retail_line = self.get_copay_line('XX00009', json_copays['Z000100'])
        chiro_line = self.get_copay_line('XX00011', json_copays['Z000100'])

        self.lines_df = pd.concat([self.lines_df,
                                   pcp_line,
                                   scp_line,
                                   pt_line,
                                   colon_line,
                                   delivery_line,
                                   img_line,
                                   high_cost_ov_line,
                                   amb_line,
                                   retail_line,
                                   chiro_line,
                                   rx_SP1_line,
                                   rx_SP3_line,
                                   rx_90_SP1_line,
                                   rx_90_SP2_line,
                                   rx_90_SP3_line])

        for i in range(len(addin_costs_df)):
            line = self.get_addin_line(addin_costs_df.loc[i, 'cov_fam'],
                                       addin_costs_df.loc[i, 'ptile_20'], addin_costs_df.loc[i, 'ptile_80'])
            self.lines_df = pd.concat([self.lines_df, line])


        for item in self.bind_dict['addInExclusions']:
            if item['treatmentTypeCode'] == 'E000100' and not item['includeAsAddIn']:
                self.lines_df.loc['E000100'] = self.get_copay_line(
                    'E000100', 999999).loc['E000100']

    def get_trad_plan_stats_df(
            self,
            ee_tier,
            other_tiers,
            migration,
            base_year,
            pepm_aso,
            premium_freq,
            contribution_freq,
            plan_name):
        plan_stats_df = pd.DataFrame(
            columns=[
                'value',
                'enrollment',
                'fam_flg',
                'prem_rate',
                'contribution',
                'migration'],
            index=[
                'base_year',
                'pepm_aso',
                'premium_freq',
                'contribution_freq',
                'plan_name'])

        plan_stats_df.loc['base_year', 'value'] = base_year
        plan_stats_df.loc['pepm_aso', 'value'] = pepm_aso
        plan_stats_df.loc['premium_freq', 'value'] = premium_freq
        plan_stats_df.loc['contribution_freq', 'value'] = contribution_freq
        plan_stats_df.loc['plan_name', 'value'] = plan_name

        for i in range(10):
            idx = i + 1
            if idx == 1:
                if ee_tier:
                    plan_stats_df.loc['t' + str(idx),
                                      'enrollment'] = ee_tier['currentEnrollment']

                    plan_stats_df.loc['t' + str(idx),
                                      'prem_rate'] = ee_tier['cobraRate']
                    plan_stats_df.loc['t' + str(idx),
                                      'contribution'] = ee_tier['employeeContributions']
                else:
                    plan_stats_df.loc['t' + str(idx),
                                       'enrollment'] = 0
                    plan_stats_df.loc['t' + str(idx),
                                       'prem_rate'] = 0
                    plan_stats_df.loc['t' + str(idx),
                                       'contribution'] = 0
                plan_stats_df.loc['t' + str(idx), 'fam_flg'] = 0
                plan_stats_df.loc['t' + str(idx), 'migration'] = migration
            elif idx <= len(other_tiers) + 1:
                plan_stats_df.loc['t' +
                                  str(idx), 'enrollment'] = other_tiers[idx -
                                                                        2]['currentEnrollment']
                plan_stats_df.loc['t' + str(idx), 'fam_flg'] = 1
                plan_stats_df.loc['t' +
                                  str(idx), 'prem_rate'] = other_tiers[idx -
                                                                       2]['cobraRate']
                plan_stats_df.loc['t' +
                                  str(idx), 'contribution'] = other_tiers[idx -
                                                                          2]['employeeContributions']
                plan_stats_df.loc['t' + str(idx), 'migration'] = migration
            else:
                plan_stats_df.loc['t' + str(idx), 'enrollment'] = 0
                plan_stats_df.loc['t' + str(idx), 'fam_flg'] = 1
                plan_stats_df.loc['t' + str(idx), 'prem_rate'] = 0
                plan_stats_df.loc['t' + str(idx), 'contribution'] = 0
                plan_stats_df.loc['t' + str(idx), 'migration'] = migration

        return plan_stats_df

    def get_not_covered_list(self):
        return ['NC     ', 'XX00012', 'XX00013', 'XX00014', 'XX00015']

    def get_covered_100_list(self):
        return [
            'Rx00000',
            'XX00000',
            'XX00010',
            'XX00016',
            'XX00017',
            'UNKNOWN']

    def get_dme_copays(self, to_1000=False):
        base = [('DME0001', 0), ('DME0002', 20), ('DME0003', 40), ('DME0004', 60),
                ('DME0005', 80), ('DME0006', 100), ('DME0007', 150), ('DME0008', 200),
                ('DME0009', 250)]
        if to_1000:
            end = [('DME0010', 350), ('DME0011', 500), ('DME0012', 1000)]
        else:
            end = [('DME0010', 300), ('DME0011', 400), ('DME0012', 500)]

        return base + end

    def get_direct_faux_cov_fam_mapping(self):
        mapping = {
            'Z001000': 'XX00003',
            'Z001100': 'XX00006',
            'Z001300': 'XX00008',
            'Z001401': 'XX00005',
            'Z000903': 'Rx30001',
            'Z000801_90': 'Rx90001',
            'Z000802': 'Rx30002',
            'Z000802_90': 'Rx90002',
            'Z000803': 'Rx30003',
            'Z000803_90': 'Rx90003',
            'Z000904': 'Rx30SP2'}
        return mapping

    def get_copay_line(
            self,
            cov_fam,
            copay,
            copay_max=None,
            copay_step=5,
            benefit_slope_from=0.2,
            benefit_slope_to=0.8,
            alpha_factor=1,
            beta_factor=1):

        df = pd.DataFrame(
            columns=[
                'copay_min',
                'copay_max',
                'copay_step',
                'payroll_min',
                'payroll_max',
                'payroll_step',
                'payroll_count_min',
                'payroll_count_max',
                'benefit_slope_from',
                'benefit_slope_to',
                'alpha_factor',
                'beta_factor'],
            index=[cov_fam])
        logger.info('inside get copay line')
        logger.info(df)
        logger.info(df.loc[cov_fam])
        if not copay_max:  # regular flat copay
            logger.info('here3')
            logger.info(copay)
            df.loc[cov_fam, 'copay_min'] = copay
            df.loc[cov_fam, 'copay_max'] = copay
            logger.info('final df')
            logger.info(df)
        else:  # smart copay
            logger.info('here4')
            df.loc[cov_fam, 'copay_min'] = copay
            df.loc[cov_fam, 'copay_max'] = copay_max
            df.loc[cov_fam, 'copay_step'] = copay_step
            df.loc[cov_fam, 'benefit_slope_from'] = benefit_slope_from
            df.loc[cov_fam, 'benefit_slope_to'] = benefit_slope_to
            df.loc[cov_fam, 'alpha_factor'] = alpha_factor
            df.loc[cov_fam, 'beta_factor'] = beta_factor
        return df

    def get_addin_line(
            self,
            cov_fam,
            ptile_20,
            ptile_80,
            benefit_slope_from=0.2,
            benefit_slope_to=0.8,
            alpha_factor=1,
            beta_factor=1):

        ptile_20 = float(ptile_20)
        ptile_80 = float(ptile_80)

        copay_step = self.bind_dict['addinCopayStep']
        copay_min_min = 0
        copay_max_max = self.bind_dict['addinCopayMax']

        payroll_step = self.bind_dict['addInPerPaycheckStep']
        payroll_max = self.bind_dict['addInPerPaycheckMax']
        payroll_min = self.bind_dict['addInPerPaycheckMin']

        payroll_count_max = self.bind_dict['addInPerPaycheckCountMax']
        payroll_count_min = self.bind_dict['addInPerPaycheckCountMin']

        global_max_addin = copay_max_max + payroll_count_max * payroll_max
        global_min_addin = copay_min_min + payroll_count_min * payroll_min

        high_cost_threshold = global_max_addin / (1 - self.high_target_AV)
        low_cost_threshold = global_min_addin / (1 - self.low_target_AV)

        copay_min_max = mround(
            min(copay_max_max * (2 / 3), low_cost_threshold * 0.5), copay_step)

        range_20_80_low = 6000
        range_20_80_high = 30000

        low_range = payroll_step * payroll_count_min
        high_range = 5000

        low_target_oop = (1 - self.low_target_AV) * ptile_20

        ideal_payroll_low = mround(
            low_target_oop /
            payroll_count_max,
            payroll_step)
        ideal_payroll_low = np.maximum(
            np.minimum(
                ideal_payroll_low,
                payroll_max),
            payroll_min)

        ideal_count_low = round(low_target_oop / ideal_payroll_low)
        ideal_count_low = np.maximum(
            np.minimum(
                ideal_count_low,
                payroll_count_max),
            payroll_count_min)

        copay_max = mround(
            bounded_interpolate(
                ptile_80,
                low_cost_threshold,
                high_cost_threshold,
                copay_min_max,
                copay_max_max),
            copay_step)

        high_target_oop = (1 - self.high_target_AV) * ptile_80 - copay_max

        ideal_payroll_high = mround(
            high_target_oop /
            payroll_count_min,
            payroll_step)
        ideal_payroll_high = np.maximum(
            np.minimum(
                ideal_payroll_high,
                payroll_max),
            payroll_min)

        ideal_count_high = round(high_target_oop / ideal_payroll_high)
        ideal_count_high = np.maximum(
            np.minimum(
                ideal_count_high,
                payroll_count_max),
            payroll_count_min)

        count = round(ideal_count_low * (1 / 2) + ideal_count_high * (1 / 2))

        revised_payroll_low = mround(low_target_oop / count, payroll_step)
        revised_payroll_low = np.maximum(
            np.minimum(
                revised_payroll_low,
                payroll_max),
            payroll_min)

        revised_payroll_high = mround(high_target_oop / count, payroll_step)
        revised_payroll_high = np.maximum(
            np.minimum(
                revised_payroll_high,
                payroll_max),
            payroll_min)

        desired_range = mround(
            bounded_interpolate(
                (ptile_80 - ptile_20),
                range_20_80_low,
                range_20_80_high,
                low_range,
                high_range),
            payroll_step)

        extra_range_needed = np.maximum(
            0, desired_range - ((revised_payroll_high - revised_payroll_low) * count))
        expand_down = revised_payroll_low - extra_range_needed / count / 2
        expand_down = np.maximum(payroll_min, expand_down)

        expand_up = revised_payroll_high + desired_range / count / 2
        expand_up = np.minimum(payroll_max, expand_up)

        df = pd.DataFrame(
            columns=[
                'copay_min',
                'copay_max',
                'copay_step',
                'payroll_min',
                'payroll_max',
                'payroll_step',
                'payroll_count_min',
                'payroll_count_max',
                'benefit_slope_from',
                'benefit_slope_to',
                'alpha_factor',
                'beta_factor'],
            index=[cov_fam])

        df.loc[cov_fam, 'copay_min'] = copay_min_min
        df.loc[cov_fam, 'copay_max'] = copay_max
        df.loc[cov_fam, 'copay_step'] = copay_step
        df.loc[cov_fam, 'payroll_min'] = mround(expand_down, payroll_step)
        df.loc[cov_fam, 'payroll_max'] = mround(
            (revised_payroll_high + expand_up) / 2, payroll_step)
        df.loc[cov_fam, 'payroll_step'] = payroll_step
        df.loc[cov_fam, 'payroll_count_min'] = count
        df.loc[cov_fam, 'payroll_count_max'] = count

        df.loc[cov_fam, 'benefit_slope_from'] = benefit_slope_from
        df.loc[cov_fam, 'benefit_slope_to'] = benefit_slope_to
        df.loc[cov_fam, 'alpha_factor'] = alpha_factor
        df.loc[cov_fam, 'beta_factor'] = beta_factor
        return df

    def to_raw_df(self):
        global_vals = pd.DataFrame.from_dict(
            self.global_dict, orient='index', columns=['global_val'])
        global_vals.index.name = 'item'
        self.lines_df.index.name = 'item'
        df = pd.concat([global_vals, self.lines_df], sort=False)
        return df.reset_index()

    def get_global_stats(self):
        df = pd.DataFrame.from_dict(
            self.bque_global_dict,
            orient='index',
            columns=['value'])
        df.index.name = 'item'
        df = df.reindex(['item',
                         'trend',
                         'bind_year_start',
                         'bind_fee',
                         'EE_share_savings',
                         'rate_rel_t1',
                         'rate_rel_t2',
                         'rate_rel_t3',
                         'rate_rel_t4',
                         'rate_rel_t5',
                         'rate_rel_t6',
                         'rate_rel_t7',
                         'rate_rel_t8',
                         'rate_rel_t9',
                         'rate_rel_t10',
                         'cont_rel_t1',
                         'cont_rel_t2',
                         'cont_rel_t3',
                         'cont_rel_t4',
                         'cont_rel_t5',
                         'cont_rel_t6',
                         'cont_rel_t7',
                         'cont_rel_t8',
                         'cont_rel_t9',
                         'cont_rel_t10'])
        return df

    def get_plan_stats_list(self):
        return self.plan_stats_list


def get_conn():
    endpoint = settings.REFDB_HOST
    user = settings.REFDB_USER
    password = settings.REFDB_PASSWORD
    port = settings.REFDB_PORT
    dbname = settings.REFDB_DB
    conn = psycopg2.connect(
        host=endpoint,
        user=user,
        port=port,
        password=password,
        dbname=dbname)
    return conn

# get results of a single (small) query and close the connection right away


def getRefTable(table, user=None, pw=None):
    conn = get_conn()
    cur = conn.cursor('PD')
    cur.execute('SELECT * FROM ' + table)
    results = cur.fetchall()
    colnames = [desc[0] for desc in cur.description]
    results_df = pd.DataFrame(results, columns=colnames)
    cur.close()
    conn.close()
    return results_df
