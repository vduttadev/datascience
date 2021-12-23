import numpy as np
import pandas as pd
import datetime
import logging

logger = logging.getLogger('control_panel')


def try_parsing_date(text):
    for fmt in ('%Y-%m-%d', '%m/%d/%Y'):
        try:
            return datetime.datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError('no valid date format found')


# full value of funding assumed to be in PE rate. Scaling plan paid to match rates
# trend here only applied to the FIE rate target - underlying pepy data
# assumed to already be at correct year
def get_scaling_factors(pepy, plan_stats, trend):
    try:
        target_ind_pepy = ((plan_stats.loc['t1':'t10',
                                           'prem_rate'].loc[plan_stats['fam_flg'] == 0] *
                            plan_stats.loc['t1':'t10', 'enrollment'].loc[plan_stats['fam_flg'] == 0]).sum() /
                           plan_stats.loc['t1':'t10', 'enrollment'].loc[plan_stats['fam_flg'] == 0].sum())
    except ZeroDivisionError as e:
        logger.info('Warning- there is only family tier selected by subscriber')
        logger.info(e)
        target_ind_pepy = 1

    target_ind_pepy = (target_ind_pepy * float(plan_stats.loc['premium_freq', 'value'])) - (
        float(plan_stats.loc['pepm_aso', 'value']) * 12.0)
    target_ind_pepy = target_ind_pepy * trend


    start_ind_pepy = (pepy.loc['allowed_core':'allowed_addin', 'trad_ind'].sum() -
                      pepy.loc['mbr_oop_core':'mbr_oop_addin', 'trad_ind'].sum() +
                      pepy.loc['fund_applied_core':'fund_remaining', 'trad_ind'].sum())

    start_fam_pepy = (pepy.loc['allowed_core':'allowed_addin', 'trad_fam'].sum() -
                      pepy.loc['mbr_oop_core':'mbr_oop_addin', 'trad_fam'].sum() +
                      pepy.loc['fund_applied_core':'fund_remaining', 'trad_fam'].sum())
    try:
        target_fam_pepy = ((plan_stats.loc['t1':'t10',
                                                   'prem_rate'].loc[plan_stats['fam_flg'] == 1] *
                                    plan_stats.loc['t1':'t10',
                                                   'enrollment'].loc[plan_stats['fam_flg'] == 1]).sum() /
                                   plan_stats.loc['t1':'t10',
                                                  'enrollment'].loc[plan_stats['fam_flg'] == 1].sum())
        target_fam_pepy = (target_fam_pepy * float(plan_stats.loc['premium_freq', 'value'])) - (float(plan_stats.loc['pepm_aso', 'value']) * 12.0)

        target_fam_pepy = target_fam_pepy * trend

        return [target_ind_pepy / start_ind_pepy, target_fam_pepy / start_fam_pepy]

    except ZeroDivisionError as e:
        logger.info('Warning- there is no family just the subscriber')
        logger.info(e)
        return [target_ind_pepy / start_ind_pepy, 1]


# adjust the pepy DataFrame to match the implied paid amounts given by trended FIE rates
# if scale_bind_util is false - then only unit cost trend is assumed for the bind case.
# approprite for annual trend, but not for scaling to match ER
# - this should generally always be True, as trending is now handled in prior steps
def scale_pepy(pepy_orig, scaling_ind, scaling_fam=None, scale_bind_util=True):

    pepy = pepy_orig.copy()

    if not scaling_fam:
        scaling_fam = scaling_ind

    scaling = pd.Series([scaling_ind, scaling_fam],
                        index=['trad_ind', 'trad_fam'])
    target = (pepy.loc['allowed_core':'allowed_addin', 'trad_ind':'trad_fam'].sum() -
              pepy.loc['mbr_oop_core':'mbr_oop_addin', 'trad_ind':'trad_fam'].sum() +
              pepy.loc['fund_applied_core':'fund_remaining', 'trad_ind':'trad_fam'].sum()) * scaling

    fund = pepy.loc['fund_applied_core':'fund_remaining',
                    'trad_ind':'trad_fam'].sum()

    pepy.loc['allowed_core':'allowed_addin', 'trad_ind':'trad_fam'] = \
        pepy.loc['allowed_core':'allowed_addin',
                 'trad_ind':'trad_fam'] * scaling

    capped_funding_scaling = np.minimum(
        scaling, fund / pepy.loc['fund_applied_core':'fund_applied_addin', 'trad_ind':'trad_fam'].sum())

    pepy.loc['fund_applied_core':'fund_applied_addin',
             'trad_ind':'trad_fam'] = pepy.loc['fund_applied_core':'fund_applied_addin',
                                               'trad_ind':'trad_fam'] * capped_funding_scaling

    pepy.loc['fund_remaining', 'trad_ind':'trad_fam'] = \
        fund - pepy.loc['fund_applied_core':'fund_applied_addin',
                        'trad_ind':'trad_fam'].sum()

    split = pepy.loc['mbr_oop_core':'mbr_oop_addin', 'trad_ind':'trad_fam'] / \
        pepy.loc['mbr_oop_core':'mbr_oop_addin', 'trad_ind':'trad_fam'].sum()

    pepy.loc['mbr_oop_core':'mbr_oop_addin',
             'trad_ind':'trad_fam'] += ((pepy.loc['allowed_core':'allowed_addin',
                                                  'trad_ind':'trad_fam'].sum() -
                                         pepy.loc['mbr_oop_core':'mbr_oop_addin',
                                                  'trad_ind':'trad_fam'].sum() +
                                         pepy.loc['fund_applied_core':'fund_remaining',
                                                  'trad_ind':'trad_fam'].sum()) - target) * split

    pepy.loc['allowed_core':'allowed_addin',
             'bind_no_behav_ind':'bind_final_ind'] = pepy.loc['allowed_core':'allowed_addin',
                                                              'bind_no_behav_ind':'bind_final_ind'] * scaling_ind

    pepy.loc['allowed_core':'allowed_addin',
             'bind_no_behav_fam':'bind_final_fam'] = pepy.loc['allowed_core':'allowed_addin',
                                                              'bind_no_behav_fam':'bind_final_fam'] * scaling_fam

    if scale_bind_util:
        pepy.loc['mbr_oop_core':'prem',
                 'bind_no_behav_ind':'bind_final_ind'] = pepy.loc['mbr_oop_core':'prem',
                                                                  'bind_no_behav_ind':'bind_final_ind'] * scaling_ind

        pepy.loc['mbr_oop_core':'prem',
                 'bind_no_behav_fam':'bind_final_fam'] = pepy.loc['mbr_oop_core':'prem',
                                                                  'bind_no_behav_fam':'bind_final_fam'] * scaling_fam

    return pepy

# return effective trend from FIE rate effective date to projection date


def get_eff_tred(plan_stats, global_df):
    dt_base = plan_stats.loc['base_year', 'value']
    dt_base = dt_base + datetime.timedelta(days=365 / 2)

    dt_bind = global_df.loc['bind_year_start', 'value']
    dt_bind = dt_bind + datetime.timedelta(days=365 / 2)

    y = (dt_bind - dt_base).days / 365
    trend = (1 + float(global_df.loc['trend', 'value']))**y
    return trend

# apply scaling to PEPY to match trended FIE rate implied plan paid amount


def adjust_pepy(pepy, plan_stats, global_df):

    trend = get_eff_tred(plan_stats, global_df)
    [ind_factor, fam_factor] = get_scaling_factors(pepy, plan_stats, trend)
    pepy_scaled = scale_pepy(pepy, ind_factor, fam_factor, True)

    return pepy_scaled

# return enrollments remaining in a trad plan, and moving out, along with
# single/family indicator (0/1)


def get_enrollments(plan_stats):
    trad_enroll_prior = plan_stats.loc[plan_stats['enrollment']
                                       == plan_stats['enrollment'], 'enrollment']

    trad_enroll = (plan_stats.loc[plan_stats['enrollment'] == plan_stats['enrollment'], 'enrollment'] * (
        1 - plan_stats.loc[plan_stats['enrollment'] == plan_stats['enrollment'], 'migration']))

    bind_enroll = (plan_stats.loc[plan_stats['enrollment'] == plan_stats['enrollment'], 'enrollment']
                   * plan_stats.loc[plan_stats['enrollment'] == plan_stats['enrollment'], 'migration'])

    fam_flg = plan_stats.loc[plan_stats['enrollment']
                             == plan_stats['enrollment'], 'fam_flg']
    return [trad_enroll_prior, trad_enroll, bind_enroll, fam_flg]

# return PEPY results, weighted by single and family enrollment


def get_trad_stats(adjusted_pepy, enroll_prior, enroll, fam_flg):
    sgl_enroll = enroll[fam_flg == 0].sum()
    fam_enroll = enroll[fam_flg == 1].sum()
    if sgl_enroll + fam_enroll == 0:
        sgl_enroll = enroll_prior[fam_flg == 0].sum()
        fam_enroll = enroll_prior[fam_flg == 1].sum()

    trad_pepy = (adjusted_pepy['trad_ind'] * sgl_enroll +
                 adjusted_pepy['trad_fam'] * fam_enroll) / (sgl_enroll + fam_enroll)

    return trad_pepy

# return relativity factors (to single coverage) given a set of FIE rates,
# along with % contributions observed


def get_FIE_shape(plan_stats):
    FIE = plan_stats.loc[plan_stats['enrollment'] ==
                         plan_stats['enrollment'], ['prem_rate', 'contribution']]
    FIE.loc[FIE['prem_rate'] == 0, 'prem_rate'] = 0.001
    FIE.loc[:, 'contribution'] = FIE.loc[:,
                                         'contribution'] / FIE.loc[:, 'prem_rate']
    FIE.loc[FIE['contribution'] != FIE['contribution'], 'contribution'] = 0
    FIE.loc[:, 'prem_rate'] = FIE.loc[:, 'prem_rate'] / \
        FIE.loc['t1', 'prem_rate']
    FIE.columns = ['FIE_Rel', 'pct_contrib']
    return FIE

# calculate control panel output items for traditional plans


def get_trad_full_stats(
        trad_results,
        plan_stats,
        trad_enroll_prior,
        trad_enroll,
        global_df):
    r = pd.Series(
        index=[
            'allowed_core_PEPM',
            'allowed_addins_PEPM',
            'paid_core_PEPM',
            'paid_addins_PEPM',
            'paid_remaining_cash_exp_PEPM',
            'core_AV',
            'addin_AV',
            't1_enroll_prior',
            't2_enroll_prior',
            't3_enroll_prior',
            't4_enroll_prior',
            't5_enroll_prior',
            't6_enroll_prior',
            't7_enroll_prior',
            't8_enroll_prior',
            't9_enroll_prior',
            't10_enroll_prior',
            't1_enroll',
            't2_enroll',
            't3_enroll',
            't4_enroll',
            't5_enroll',
            't6_enroll',
            't7_enroll',
            't8_enroll',
            't9_enroll',
            't10_enroll',
            't1_FIE',
            't2_FIE',
            't3_FIE',
            't4_FIE',
            't5_FIE',
            't6_FIE',
            't7_FIE',
            't8_FIE',
            't9_FIE',
            't10_FIE',
            't1_ER_cont',
            't2_ER_cont',
            't3_ER_cont',
            't4_ER_cont',
            't5_ER_cont',
            't6_ER_cont',
            't7_ER_cont',
            't8_ER_cont',
            't9_ER_cont',
            't10_ER_cont',
            't1_EE_cont',
            't2_EE_cont',
            't3_EE_cont',
            't4_EE_cont',
            't5_EE_cont',
            't6_EE_cont',
            't7_EE_cont',
            't8_EE_cont',
            't9_EE_cont',
            't10_EE_cont'])
    r['allowed_core_PEPM'] = trad_results['allowed_core'] / 12
    r['allowed_addins_PEPM'] = trad_results['allowed_addin'] / 12
    r['paid_core_PEPM'] = r['allowed_core_PEPM'] - \
        (trad_results['mbr_oop_core'] - trad_results['fund_applied_core']) / 12
    r['paid_addins_PEPM'] = r['allowed_addins_PEPM'] - \
        (trad_results['mbr_oop_addin'] -
         trad_results['fund_applied_addin']) / 12
    r['paid_remaining_cash_exp_PEPM'] = trad_results['fund_remaining'] / 12
    r['core_AV'] = r['paid_core_PEPM'] / r['allowed_core_PEPM']
    r['addin_AV'] = r['paid_addins_PEPM'] / r['allowed_addins_PEPM']
    r['t1_enroll_prior':'t10_enroll_prior'] = trad_enroll_prior.tolist()
    r['t1_enroll':'t10_enroll'] = trad_enroll.tolist()

    FIE_shape = get_FIE_shape(plan_stats)
    if trad_enroll.sum() == 0:
        trad_enroll = trad_enroll_prior
    monthly_risk_units = (FIE_shape['FIE_Rel'] * trad_enroll).sum()
    agg_monthly_cost = r['paid_core_PEPM':'paid_remaining_cash_exp_PEPM'].sum(
    ) * trad_enroll.sum()
    agg_monthly_cost += trad_enroll.sum() * \
        float(plan_stats.loc['pepm_aso', 'value'])
    per_risk_unit = agg_monthly_cost / monthly_risk_units
    rates = FIE_shape['FIE_Rel'] * per_risk_unit
    contrib = rates * FIE_shape['pct_contrib']
    r['t1_FIE':'t10_FIE'] = rates
    r['t1_ER_cont':'t10_ER_cont'] = rates - contrib
    r['t1_EE_cont':'t10_EE_cont'] = contrib
    return r

# calculate base bind stats weighing the individual and family
# enrollments/experience migrated from
# ALL traditional plans in each list of trad plan results


def get_bind_stats(pepy_list, enroll_list, fam_flg_list):
    pepy = pd.DataFrame(index=pepy_list[0].index, columns=[
                        'no_behav', 'w_behav'])
    pepy.loc[:, :] = 0
    grand_tot_enroll = 0

    for i in range(len(pepy_list)):
        ind_enroll = enroll_list[i][fam_flg_list[i] == 0].sum()
        fam_enroll = enroll_list[i][fam_flg_list[i] == 1].sum()

        pepy.loc[:, 'no_behav'] += (pepy_list[i]['bind_no_behav_ind'] * ind_enroll +
                                    pepy_list[i]['bind_no_behav_fam'] * fam_enroll)
        pepy.loc[:, 'w_behav'] += (pepy_list[i]['bind_final_ind'] * ind_enroll +
                                   pepy_list[i]['bind_final_fam'] * fam_enroll)

        grand_tot_enroll += ind_enroll + fam_enroll

    pepy = pepy / grand_tot_enroll

    return pepy

# helper function to clean index


def get_clean_csv(path):
    df = pd.read_csv(path)
    df = df.set_index(df.columns[0])
    df.index.name = 'index'
    return df

# class to load up async results from trad plans one by one, then 'consume'
# those results to produce various final results


class PlanCombiner:
    def __init__(self, global_df):
        self.global_df = global_df
        self.pepy_list = []
        self.adj_pepy_list = []
        self.plan_stats_list = []
        self.bind_enroll_list = []
        self.fam_flg_list = []
        self.trad_results = pd.DataFrame(
            index=[
                'allowed_core_PEPM',
                'allowed_addins_PEPM',
                'paid_core_PEPM',
                'paid_addins_PEPM',
                'paid_remaining_cash_exp_PEPM',
                'core_AV',
                'addin_AV',
                't1_enroll_prior',
                't2_enroll_prior',
                't3_enroll_prior',
                't4_enroll_prior',
                't5_enroll_prior',
                't6_enroll_prior',
                't7_enroll_prior',
                't8_enroll_prior',
                't9_enroll_prior',
                't10_enroll_prior',
                't1_enroll',
                't2_enroll',
                't3_enroll',
                't4_enroll',
                't5_enroll',
                't6_enroll',
                't7_enroll',
                't8_enroll',
                't9_enroll',
                't10_enroll',
                't1_FIE',
                't2_FIE',
                't3_FIE',
                't4_FIE',
                't5_FIE',
                't6_FIE',
                't7_FIE',
                't8_FIE',
                't9_FIE',
                't10_FIE',
                't1_ER_cont',
                't2_ER_cont',
                't3_ER_cont',
                't4_ER_cont',
                't5_ER_cont',
                't6_ER_cont',
                't7_ER_cont',
                't8_ER_cont',
                't9_ER_cont',
                't10_ER_cont',
                't1_EE_cont',
                't2_EE_cont',
                't3_EE_cont',
                't4_EE_cont',
                't5_EE_cont',
                't6_EE_cont',
                't7_EE_cont',
                't8_EE_cont',
                't9_EE_cont',
                't10_EE_cont'])

    def set_ee_share_savings(self, share):
        self.global_df['EE_share_savings', 'value'] = share

    def load_plan(self, pepy_df, plan_stats_df):
        self.pepy_list.append(pepy_df)
        self.plan_stats_list.append(plan_stats_df)

    def run_plans(self):
        for (i, pepy_df) in enumerate(self.pepy_list):
            plan_stats_df = self.plan_stats_list[i]
            adj_pepy = adjust_pepy(pepy_df, plan_stats_df, self.global_df)
            [trad_enroll_prior, trad_enroll, bind_enroll,
                fam_flg] = get_enrollments(plan_stats_df)
            self.adj_pepy_list.append(adj_pepy)
            self.bind_enroll_list.append(bind_enroll)
            self.fam_flg_list.append(fam_flg)
            trad_stats = get_trad_stats(
                adj_pepy, trad_enroll_prior, trad_enroll, fam_flg)
            trad_stats[trad_stats != trad_stats] = 0
            trad_stats_full = get_trad_full_stats(
                trad_stats,
                plan_stats_df,
                trad_enroll_prior,
                trad_enroll,
                self.global_df)
            self.trad_results.loc[:,
                                  plan_stats_df.loc['plan_name',
                                                    'value']] = trad_stats_full
        self.pepy_list = []
        self.plan_stats_list = []
        return

    # return control panel outputs for trad plans only
    def get_trad_results(self):
        return self.trad_results

    # generally should not be called outside this class. returns
    # subset of control panel results for bind plan
    def get_intermediate_bind_results(self):
        bind_df = get_bind_stats(
            self.adj_pepy_list, self.bind_enroll_list, self.fam_flg_list)
        bind_enroll = pd.DataFrame(
            index=[
                't1',
                't2',
                't3',
                't4',
                't5',
                't6',
                't7',
                't8',
                't9',
                't10'],
            columns=[
                'no_behav',
                'w_behav'])
        bind_enroll.loc[:, :] = 0
        for enroll in self.bind_enroll_list:
            bind_enroll.loc[:,
                            'no_behav'] = bind_enroll.loc[:,
                                                          'no_behav'] + enroll
            bind_enroll.loc[:, 'w_behav'] = bind_enroll.loc[:,
                                                            'w_behav'] + enroll
        return pd.concat([bind_df, bind_enroll])

    # return control panel outputs for bind plan only. split into versions
    # with and without behavior change
    # 'behavior change' includes the utilization change from cov_fam specific
    # cost share, and effect of smart copays
    def get_bind_results(self):
        r = pd.DataFrame(
            index=[
                'allowed_core_PEPM',
                'allowed_addins_PEPM',
                'paid_core_PEPM',
                'paid_addins_PEPM',
                'paid_remaining_cash_exp_PEPM',
                'core_AV',
                'addin_AV',
                't1_enroll_prior',
                't2_enroll_prior',
                't3_enroll_prior',
                't4_enroll_prior',
                't5_enroll_prior',
                't6_enroll_prior',
                't7_enroll_prior',
                't8_enroll_prior',
                't9_enroll_prior',
                't10_enroll_prior',
                't1_enroll',
                't2_enroll',
                't3_enroll',
                't4_enroll',
                't5_enroll',
                't6_enroll',
                't7_enroll',
                't8_enroll',
                't9_enroll',
                't10_enroll',
                't1_FIE',
                't2_FIE',
                't3_FIE',
                't4_FIE',
                't5_FIE',
                't6_FIE',
                't7_FIE',
                't8_FIE',
                't9_FIE',
                't10_FIE',
                't1_ER_cont',
                't2_ER_cont',
                't3_ER_cont',
                't4_ER_cont',
                't5_ER_cont',
                't6_ER_cont',
                't7_ER_cont',
                't8_ER_cont',
                't9_ER_cont',
                't10_ER_cont',
                't1_EE_cont',
                't2_EE_cont',
                't3_EE_cont',
                't4_EE_cont',
                't5_EE_cont',
                't6_EE_cont',
                't7_EE_cont',
                't8_EE_cont',
                't9_EE_cont',
                't10_EE_cont'],
            columns=[
                'no_behav',
                'w_behav'])
        int_results = self.get_intermediate_bind_results()
        r.loc['allowed_core_PEPM'] = int_results.loc['allowed_core'] / 12
        r.loc['allowed_addins_PEPM'] = int_results.loc['allowed_addin'] / 12
        r.loc['paid_core_PEPM'] = r.loc['allowed_core_PEPM'] - \
            (int_results.loc['mbr_oop_core']) / 12
        r.loc['paid_addins_PEPM'] = r.loc['allowed_addins_PEPM'] - \
            (int_results.loc['mbr_oop_addin'] + int_results.loc['prem']) / 12
        r.loc['core_AV'] = r.loc['paid_core_PEPM'] / r.loc['allowed_core_PEPM']
        r.loc['addin_AV'] = r.loc['paid_addins_PEPM'] / \
            r.loc['allowed_addins_PEPM']
        r.loc['t1_enroll':'t10_enroll'] = int_results.loc['t1':'t10'].values
        shape = self.global_df.loc['rate_rel_t1':'rate_rel_t10', 'value'].astype(
            float)
        cont_shape = self.global_df.loc['cont_rel_t1':'cont_rel_t10', 'value'].astype(
            float)
        monthly_risk_units = (pd.concat(
            [shape, shape], axis=1) * r.loc['t1_enroll':'t10_enroll'].values).sum()
        monthly_risk_units.index = ['no_behav', 'w_behav']
        monthly_cont_units = (pd.concat(
            [cont_shape, cont_shape], axis=1) * r.loc['t1_enroll':'t10_enroll'].values).sum()
        monthly_cont_units.index = ['no_behav', 'w_behav']

        agg_monthly_cost = r['paid_core_PEPM':'paid_addins_PEPM'].sum(
        ) * r['t1_enroll':'t10_enroll'].sum()
        agg_monthly_cost += r['t1_enroll':'t10_enroll'].sum() * \
            float(self.global_df.loc['bind_fee', 'value'])
        per_risk_unit = agg_monthly_cost / monthly_risk_units
        rates = np.dot(shape.values.reshape(10, 1),
                       per_risk_unit.values.reshape(1, 2))
        r.loc['t1_FIE':'t10_FIE'] = rates

        bind_enroll_by_trad_plan = pd.DataFrame(
            index=self.bind_enroll_list[0].index)
        for l in self.bind_enroll_list:
            bind_enroll_by_trad_plan = pd.concat(
                [bind_enroll_by_trad_plan, l], axis=1)
        bind_enroll_by_trad_plan.columns = self.trad_results.columns.tolist()

        trad_agg_monthly_cost = (
            bind_enroll_by_trad_plan['t1':'t10'] * self.trad_results.loc['t1_FIE':'t10_FIE'].values).sum().sum()
        trad_agg_ER_cost = (bind_enroll_by_trad_plan['t1':'t10'] *
                            self.trad_results.loc['t1_ER_cont':'t10_ER_cont'].values).sum().sum()
        agg_target_ER = trad_agg_ER_cost + ((agg_monthly_cost - trad_agg_monthly_cost) * (
            1 - float(self.global_df.loc['EE_share_savings', 'value'])))
        agg_target_EE = agg_monthly_cost - agg_target_ER
        per_cont_unit = agg_target_EE / monthly_cont_units
        contrib = np.dot(cont_shape.values.reshape(10, 1),
                         per_cont_unit.values.reshape(1, 2))
        r.loc['t1_EE_cont':'t10_EE_cont'] = contrib
        r.loc['t1_ER_cont':'t10_ER_cont'] = r.loc['t1_FIE':'t10_FIE'].values - \
            r.loc['t1_EE_cont':'t10_EE_cont'].values

        ER_contrib_bind = (r['t1_enroll':'t10_enroll'] *
                           r['t1_ER_cont':'t10_ER_cont'].values).sum()
        EE_contrib_bind = (r['t1_enroll':'t10_enroll'] *
                           r['t1_EE_cont':'t10_EE_cont'].values).sum()

        for idx in ['no_behav', 'w_behav']:
            r.loc['bind_fee', idx] = float(
                self.global_df.loc['bind_fee', 'value'])
            r.loc['bind_savings_gross', idx] = (
                trad_agg_monthly_cost - agg_monthly_cost[idx]) / r.loc['t1_enroll':'t10_enroll', idx].sum()
            r.loc['ER-$_savings', idx] = (trad_agg_ER_cost - ER_contrib_bind[idx]) / \
                r.loc['t1_enroll':'t10_enroll', idx].sum()
            r.loc['EE-$_savings', idx] = ((trad_agg_monthly_cost - trad_agg_ER_cost) -
                                          EE_contrib_bind[idx]) / r.loc['t1_enroll':'t10_enroll', idx].sum()
            r.loc['ER-%_savings', idx] = 1 - \
                float(self.global_df.loc['EE_share_savings', 'value'])
            r.loc['EE-%_savings',
                  idx] = float(self.global_df.loc['EE_share_savings', 'value'])

        for i in range(10):
            if r.loc['t' + str(i + 1) + '_FIE', 'no_behav'] == 0:
                r.loc['t' + str(i + 1) + '_cost_share'] = 0
            else:
                r.loc['t' + str(i + 1) + '_cost_share'] = r.loc['t' + str(i + 1) +
                                                                '_EE_cont'] / r.loc['t' + str(i + 1) + '_FIE']

        r.loc['allowed_prior_core', :] = (bind_enroll_by_trad_plan.sum(
        ) * self.trad_results.loc['allowed_core_PEPM']).sum() / bind_enroll_by_trad_plan.sum().sum()
        r.loc['allowed_prior_addins', :] = (bind_enroll_by_trad_plan.sum(
        ) * self.trad_results.loc['allowed_addins_PEPM']).sum() / bind_enroll_by_trad_plan.sum().sum()

        r.loc['paid_prior_core', :] = (bind_enroll_by_trad_plan.sum(
        ) * self.trad_results.loc['paid_core_PEPM']).sum() / bind_enroll_by_trad_plan.sum().sum()
        r.loc['paid_prior_addins', :] = (bind_enroll_by_trad_plan.sum(
        ) * self.trad_results.loc['paid_addins_PEPM']).sum() / bind_enroll_by_trad_plan.sum().sum()
        r.loc['paid_prior_cash_remain', :] = (bind_enroll_by_trad_plan.sum(
        ) * self.trad_results.loc['paid_remaining_cash_exp_PEPM']).sum() / bind_enroll_by_trad_plan.sum().sum()

        r.loc['chart_metric_%_savings_paid_PEPM'] = ((r.loc['paid_core_PEPM', :] + r.loc['paid_addins_PEPM', :]) / (
            r.loc['paid_prior_core', :] + r.loc['paid_prior_addins', :] + r.loc['paid_prior_cash_remain', :]) - 1)
        r.loc['chart_metric_$_savings_paid_PEPM'] = ((r.loc['paid_prior_core', :] + r.loc['paid_prior_addins', :] +
                                                      r.loc['paid_prior_cash_remain', :]) -
                                                     (r.loc['paid_core_PEPM', :] +
                                                      r.loc['paid_addins_PEPM', :]))
        r.loc['chart_metric_%_savings_allowed_PEPM'] = ((r.loc['allowed_core_PEPM', :] +
                                                         r.loc['allowed_addins_PEPM', :]) / (
            r.loc['allowed_prior_core', :] + r.loc['allowed_prior_addins', :]) - 1)
        r.loc['chart_metric_$_savings_allowed_PEPM'] = ((r.loc['allowed_prior_core', :] +
                                                         r.loc['allowed_prior_addins', :]) -
                                                        (r.loc['allowed_core_PEPM', :] +
                                                         r.loc['allowed_addins_PEPM', :]))

        r.loc['chart_metrics_WF_current', :] = r.loc['paid_prior_core', :] + \
            r.loc['paid_prior_addins', :] + r.loc['paid_prior_cash_remain', :]
        r.loc['chart_metrics_WF_util_change_core',
              :] = r.loc['allowed_core_PEPM',
                         :] - r.loc['allowed_prior_core',
                                    :]
        r.loc['chart_metrics_WF_util_change_addins',
              :] = r.loc['allowed_addins_PEPM',
                         :] - r.loc['allowed_prior_addins',
                                    :]
        r.loc['chart_metrics_WF_subs_change_core',
              :] = ((r.loc['paid_core_PEPM',
                           :] - (r.loc['paid_prior_core',
                                       :] + r.loc['paid_prior_cash_remain',
                                                  :])) - r.loc['chart_metrics_WF_util_change_core',
                                                               :])
        r.loc['chart_metrics_WF_subs_change_addin',
              :] = ((r.loc['paid_addins_PEPM',
                           :] - (r.loc['paid_prior_addins',
                                       :])) - r.loc['chart_metrics_WF_util_change_addins',
                                                    :])
        r.loc['chart_metrics_WF_bind', :] = r.loc['paid_core_PEPM', :] + \
            r.loc['paid_addins_PEPM', :]

        r.loc['trad_replaced_monthly_plan_cost'] = trad_agg_monthly_cost
        r.loc['trad_replaced_monthly_ER_cost'] = trad_agg_ER_cost

        r.loc[['t1_enroll_prior',
               't2_enroll_prior',
               't3_enroll_prior',
               't4_enroll_prior',
               't5_enroll_prior',
               't6_enroll_prior',
               't7_enroll_prior',
               't8_enroll_prior',
               't9_enroll_prior',
               't10_enroll_prior']] = 0

        return r

    # returns aggregate results considering overall migration of traditional
    # plans to bind
    def get_company_agg_results(self):
        trad_stats = self.get_trad_results()
        bind_stats = self.get_bind_results()

        r = pd.DataFrame(columns=['no_behav', 'w_behav'])
        total_enrollment = trad_stats.loc['t1_enroll':'t10_enroll'].sum().sum()
        total_enrollment += bind_stats.loc['t1_enroll':'t10_enroll',
                                           'no_behav'].sum()

        r.loc['total_enrollment', :] = total_enrollment

        r.loc['agg_tot_self_funded_rates_SQ', :] = (
            trad_stats.loc['t1_FIE':'t10_FIE'] * trad_stats.loc['t1_enroll':'t10_enroll'].values).sum().sum() * 12
        r.loc['agg_tot_self_funded_rates_bind',
              :] = r.loc['agg_tot_self_funded_rates_SQ', :]
        r.loc['agg_tot_self_funded_rates_SQ',
              :] += bind_stats.loc['trad_replaced_monthly_plan_cost', :] * 12
        r.loc['agg_tot_self_funded_rates_bind', :] += (
            bind_stats.loc['t1_FIE':'t10_FIE'] * bind_stats.loc['t1_enroll':'t10_enroll'].values).sum() * 12
        r.loc['agg_tot_$_diff_self_funded_rate',
              :] = r.loc['agg_tot_self_funded_rates_SQ',
                         :] - r.loc['agg_tot_self_funded_rates_bind',
                                    :]
        r.loc['agg_tot_%_diff_self_funded_rate',
              :] = r.loc['agg_tot_$_diff_self_funded_rate',
                         :] / r.loc['agg_tot_self_funded_rates_SQ',
                                    :]

        r.loc['agg_tot_ER_cost_SQ', :] = (trad_stats.loc['t1_ER_cont':'t10_ER_cont']
                                          * trad_stats.loc['t1_enroll':'t10_enroll'].values).sum().sum() * 12
        r.loc['agg_tot_ER_cost_bind', :] = r.loc['agg_tot_ER_cost_SQ', :]
        r.loc['agg_tot_ER_cost_SQ',
              :] += bind_stats.loc['trad_replaced_monthly_ER_cost', :] * 12
        r.loc['agg_tot_ER_cost_bind', :] += (bind_stats.loc['t1_ER_cont':'t10_ER_cont']
                                             * bind_stats.loc['t1_enroll':'t10_enroll'].values).sum() * 12
        r.loc['agg_tot_$_diff_ER_cost', :] = r.loc['agg_tot_ER_cost_SQ',
                                                   :] - r.loc['agg_tot_ER_cost_bind', :]
        r.loc['agg_tot_%_diff_ER_cost', :] = r.loc['agg_tot_$_diff_ER_cost',
                                                   :] / r.loc['agg_tot_ER_cost_SQ', :]

        r.loc['agg_tot_EE_cost_SQ', :] = r.loc['agg_tot_self_funded_rates_SQ',
                                               :] - r.loc['agg_tot_ER_cost_SQ', :]
        r.loc['agg_tot_EE_cost_bind',
              :] = r.loc['agg_tot_self_funded_rates_bind',
                         :] - r.loc['agg_tot_ER_cost_bind',
                                    :]
        r.loc['agg_tot_$_diff_EE_cost', :] = r.loc['agg_tot_EE_cost_SQ',
                                                   :] - r.loc['agg_tot_EE_cost_bind', :]
        r.loc['agg_tot_%_diff_EE_cost', :] = r.loc['agg_tot_$_diff_EE_cost',
                                                   :] / r.loc['agg_tot_EE_cost_SQ', :]

        r.loc['PEPY_self_funded_rates_SQ'] = r.loc['agg_tot_self_funded_rates_SQ',
                                                   :] / total_enrollment
        r.loc['PEPY_self_funded_rates_bind'] = r.loc['agg_tot_self_funded_rates_bind',
                                                     :] / total_enrollment
        r.loc['PEPY_$_diff_self_funded_rates'] = r.loc['agg_tot_$_diff_self_funded_rate',
                                                       :] / total_enrollment
        r.loc['PEPY_%_diff_self_funded_rates'] = r.loc['agg_tot_%_diff_self_funded_rate', :]

        r.loc['PEPY_ER_cost_SQ'] = r.loc['agg_tot_ER_cost_SQ', :] / \
            total_enrollment
        r.loc['PEPY_ER_cost_bind'] = r.loc['agg_tot_ER_cost_bind', :] / \
            total_enrollment
        r.loc['PEPY_$_diff_ER_cost'] = r.loc['agg_tot_$_diff_ER_cost',
                                             :] / total_enrollment
        r.loc['PEPY_%_diff_ER_cost'] = r.loc['agg_tot_%_diff_ER_cost', :]

        r.loc['PEPY_EE_cost_SQ'] = r.loc['agg_tot_EE_cost_SQ', :] / \
            total_enrollment
        r.loc['PEPY_EE_cost_bind'] = r.loc['agg_tot_EE_cost_bind', :] / \
            total_enrollment
        r.loc['PEPY_$_diff_EE_cost'] = r.loc['agg_tot_$_diff_EE_cost',
                                             :] / total_enrollment
        r.loc['PEPY_%_diff_EE_cost'] = r.loc['agg_tot_%_diff_EE_cost', :]

        return r

    # returns single DataFrame with all control panel results for BQUE use
    def get_combined_results(self):
        trad_results = self.get_trad_results()
        bind_results = self.get_bind_results()
        agg_results = self.get_company_agg_results()

        bind_results = pd.concat([bind_results, agg_results])
        dummy_df = pd.DataFrame(
            index=bind_results.loc['bind_fee':'PEPY_%_diff_EE_cost'].index, columns=trad_results.columns)
        trad_results = pd.concat([trad_results, dummy_df])
        return pd.concat([trad_results, bind_results], axis=1)


######################
