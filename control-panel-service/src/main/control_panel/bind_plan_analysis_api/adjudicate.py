import numpy as np
import pandas as pd
import psycopg2
import datetime
import logging

from django.conf import settings
from scipy import stats

logger = logging.getLogger('control_panel')


def get_date(t):
    return datetime.datetime.strptime(t, '%Y-%m-%d')


def none_to_zero(x):
    if x is None:
        y = 0
    else:
        y = int(x)
    return y

# Get the conneciton to DB


def get_conn():
    endpoint = settings.REFDB_HOST
    user = settings.REFDB_USER
    password = settings.REFDB_PASSWORD
    port = settings.REFDB_PORT
    dbname = settings.REFDB_DB
    conn = psycopg2.connect(host=endpoint, user=user,
                            port=port, password=password, dbname=dbname)
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


# return expected utilization change resulting from change in cost share %.
# 'boost' used to amplify utilization change, typically for add-ins to represent additional effect of enforced active decision

# https://www.dropbox.com/s/cerkap2xizlk164/Health%20care%20demand%20elasticities%20by%20type%20of%20service.pdf?dl=0
# using default elasticity for all services. Applying boost as 'higher'
# preceived cost with active decision
def get_util_change(cost_from, cost_to, elas, boost=1):
    cost_mvmt = (cost_to.astype(float)) / cost_from.astype(float) - 1
    factor = cost_mvmt * (elas.astype(float) * boost) + 1
    factor = np.maximum(0, factor)
    return factor

# split apart bind plan input into global variables, static copays and
# smart copay data


def intake_bind_plan_raw_df(raw_df):
    raw_df.index = raw_df['item']
    global_val_series = raw_df.loc[raw_df['global_val']
                                   == raw_df['global_val'], 'global_val']

    raw_df = raw_df.loc[raw_df['global_val'] !=
                        raw_df['global_val'], 'copay_min':'beta_factor']
    std_copay_series = raw_df.loc[raw_df['copay_min']
                                  == raw_df['copay_max'], 'copay_min']
    smart_copay_df = raw_df.loc[raw_df['copay_min'] != raw_df['copay_max']]

    return (global_val_series, std_copay_series, smart_copay_df)

# get corresponding copay/premium/#payments or other item for a specific provider at 'ptile' level.
# based on modified inverse beta distibution given the other inputs


def apply_pricing_scale(
        item_min,
        item_max,
        step,
        slope_from,
        slope_to,
        alpha,
        beta,
        ptile):
    ptile = np.maximum(slope_from, ptile)
    ptile = np.minimum(slope_to, ptile)
    ptile_mod = (ptile - slope_from) / (slope_to - slope_from)
    inv_beta = stats.beta.ppf(
        ptile_mod.astype(float),
        alpha.astype(float),
        beta.astype(float))
    unrounded = item_min + inv_beta * (item_max - item_min)
    return step * round(unrounded / step)

# return the % of people expected to migrate to a lower cost, given current base price - considering moving to target
# price elasticity must be in terms of the percentage difference (not $$)
# of costs


def get_migration_pct(base_price, target_price, elas):
    pct_cost_inc = base_price / target_price - 1
    migrate_pct = pct_cost_inc * elas
    return np.minimum(1, np.maximum(0, migrate_pct))

# take distribution of smart copay-ed items in truven, along with specification of smart copay design and produce
# distibution with migrated claims to lower target ptile group (A-T each
# with 5 percent of providers (not episodes))


def apply_smart_copay_to_dist(
        smart_dist_df_in,
        smart_copay_df,
        trad_cs,
        elas,
        boost,
        util_inc_cap,
        pcp_unit,
        scp_unit,
        inelastic_pct,
        addin_gate_pct,
        addin_util_floor):
    smart_dist_df = smart_dist_df_in.copy()
    exp_copay = smart_copay_df.loc[smart_dist_df.index]
    smart_dist_df = smart_dist_df.assign(
        copay=apply_pricing_scale(
            exp_copay['copay_min'].astype(float),
            exp_copay['copay_max'].astype(float),
            exp_copay['copay_step'].astype(float),
            exp_copay['benefit_slope_from'],
            exp_copay['benefit_slope_to'],
            exp_copay['alpha_factor'],
            exp_copay['beta_factor'],
            smart_dist_df['median_eps_percentile'].astype(float)))

    smart_dist_df = smart_dist_df.assign(paychecks=0)
    smart_dist_df = smart_dist_df.assign(per_paycheck=0)
    addin_list = set(
        exp_copay.loc[exp_copay['payroll_step'] == exp_copay['payroll_step']].index)
    addin_list2 = set(smart_dist_df['cov_fam'])
    addin_list = addin_list.intersection(addin_list2)

    smart_dist_df.loc[addin_list,
                      'paychecks'] = apply_pricing_scale(exp_copay['payroll_count_min'].astype(float),
                                                         exp_copay['payroll_count_max'].astype(
                                                             float),
                                                         1,
                                                         exp_copay['benefit_slope_from'],
                                                         exp_copay['benefit_slope_to'],
                                                         exp_copay['alpha_factor'],
                                                         exp_copay['beta_factor'],
                                                         smart_dist_df['median_eps_percentile'].astype(float)).loc[addin_list]

    smart_dist_df.loc[addin_list,
                      'per_paycheck'] = apply_pricing_scale(exp_copay['payroll_min'].astype(float),
                                                            exp_copay['payroll_max'].astype(float),
                                                            exp_copay['payroll_step'].astype(float),
                                                            exp_copay['benefit_slope_from'],
                                                            exp_copay['benefit_slope_to'],
                                                            exp_copay['alpha_factor'],
                                                            exp_copay['beta_factor'],
                                                            smart_dist_df['median_eps_percentile'].astype(float)).loc[addin_list]

    avg_cov_fam_cost = (smart_dist_df['tot_cost'].groupby('cov_fam').sum().astype(
        float) / smart_dist_df['tot_eps'].groupby('cov_fam').sum().astype(float))
    avg_cov_fam_cost['XX00001'] = pcp_unit  # Replace dummy costs
    avg_cov_fam_cost['XX00002'] = scp_unit  # Replace dummy costs
    trad_member_cost = avg_cov_fam_cost * trad_cs
    trad_member_cost.name = 'trad_member_payment'

    smart_dist_df = pd.concat(
        [smart_dist_df, trad_member_cost], axis=1, join='inner')

    smart_dist_df['bind_member_payment'] = (
        smart_dist_df['copay'].astype(float) +
        smart_dist_df['paychecks'].astype(float) *
        smart_dist_df['per_paycheck'].astype(float))

    smart_dist_df = smart_dist_df.merge(pd.DataFrame(
        elas), how='left', left_index=True, right_on='cov_fam')
    smart_dist_df = smart_dist_df.assign(boost=1)
    smart_dist_df.loc[addin_list, 'boost'] = boost

    smart_dist_df['get_addin_pct'] = np.minimum(
        util_inc_cap,
        get_util_change(
            smart_dist_df['trad_member_payment'],
            smart_dist_df['bind_member_payment'],
            smart_dist_df['elas'].astype(float),
            smart_dist_df['boost']))

    smart_dist_df.loc[addin_list, 'get_addin_pct'] = np.minimum(
        1, smart_dist_df.loc[addin_list, 'get_addin_pct'])
    smart_dist_df.loc[addin_list,
                      'get_addin_pct'] = smart_dist_df.loc[addin_list,
                                                           'get_addin_pct'] * (1 - addin_gate_pct)
    smart_dist_df.loc[addin_list, 'get_addin_pct'] = np.maximum(
        inelastic_pct, np.minimum(1, smart_dist_df.loc[addin_list, 'get_addin_pct']))
    smart_dist_df.loc[addin_list, 'get_addin_pct'] = np.maximum(
        addin_util_floor, smart_dist_df.loc[addin_list, 'get_addin_pct'])

    group_mins = smart_dist_df['bind_member_payment'].groupby('cov_fam').min()
    group_mins.name = 'cov_fam_min_bind'

    smart_dist_df = pd.concat(
        [smart_dist_df, group_mins], axis=1, join='inner')

    smart_dist_df['switch_pct'] = (
        1 - get_util_change(
            smart_dist_df['cov_fam_min_bind'],
            smart_dist_df['bind_member_payment'],
            smart_dist_df['elas'].astype(float))) * smart_dist_df['get_addin_pct']
    smart_dist_df['no_change_pct'] = smart_dist_df['get_addin_pct'] - \
        smart_dist_df['switch_pct']
    smart_dist_df['no_change_pct'] = np.maximum(
        inelastic_pct, smart_dist_df['no_change_pct'])
    smart_dist_df['switch_pct'] = smart_dist_df['get_addin_pct'] - \
        smart_dist_df['no_change_pct']

    smart_dist_df = smart_dist_df.assign(migrated_eps=0)
    for i in range(len(smart_dist_df)):
        base_bind_cost = smart_dist_df['bind_member_payment'][i]
        to_migrate = smart_dist_df['tot_eps'][i] * \
            smart_dist_df['switch_pct'][i]
        if to_migrate > 0:
            sub_dist = smart_dist_df.loc[smart_dist_df['cov_fam']
                                         == smart_dist_df['cov_fam'][i]].copy()
            sub_dist['induced_util'] = np.maximum(
                0,
                get_util_change(
                    base_bind_cost,
                    sub_dist['bind_member_payment'],
                    sub_dist['elas'].astype(float)) - 1)
            sub_dist['induced_util'] = sub_dist['induced_util'] / \
                sub_dist['induced_util'].sum()
            smart_dist_df.loc[smart_dist_df['cov_fam'] == smart_dist_df['cov_fam'][
                i], 'migrated_eps'] += (sub_dist['induced_util'] * to_migrate).tolist()

    smart_dist_df['migrated_eps'] += smart_dist_df['tot_eps'] * \
        smart_dist_df['no_change_pct']

    smart_dist_df['tot_bind_copay_pre'] = smart_dist_df['copay'] * \
        smart_dist_df['tot_eps']
    smart_dist_df['tot_bind_prem_pre'] = smart_dist_df['paychecks'] * \
        smart_dist_df['per_paycheck'] * smart_dist_df['tot_eps']

    smart_dist_df['tot_bind_copay_post'] = smart_dist_df['copay'] * \
        smart_dist_df['migrated_eps']
    smart_dist_df['tot_bind_prem_post'] = smart_dist_df['paychecks'] * \
        smart_dist_df['per_paycheck'] * smart_dist_df['migrated_eps']
    smart_dist_df['tot_cost_migrated'] = smart_dist_df['avg_cost'].astype(
        float) * smart_dist_df['migrated_eps']

    smart_dist_df['tot_cost'] = smart_dist_df['tot_cost'].astype(float)

    return smart_dist_df

# take smart copay info by group A-U and expected migration and summized
# by cov_fam


def get_dist_stats(smart_dist_df):
    dist_stats = smart_dist_df.groupby(
        level='cov_fam')[
        'tot_eps',
        'migrated_eps',
        'tot_cost',
        'tot_cost_migrated',
        'tot_bind_copay_pre',
        'tot_bind_prem_pre',
        'tot_bind_copay_post',
        'tot_bind_prem_post'].sum()
    dist_stats.loc[:, 'avg_eps_pre'] = dist_stats['tot_cost'] / \
        dist_stats['tot_eps']
    dist_stats.loc[:, 'avg_eps_post'] = dist_stats['tot_cost_migrated'] / \
        dist_stats['migrated_eps']
    dist_stats.loc[:, 'avg_eps_change'] = dist_stats['avg_eps_post'] / \
        dist_stats['avg_eps_pre'] - 1

    dist_stats.loc[:, 'avg_copay_pre'] = dist_stats['tot_bind_copay_pre'] / \
        dist_stats['tot_eps']
    dist_stats.loc[:, 'avg_prem_pre'] = dist_stats['tot_bind_prem_pre'] / \
        dist_stats['tot_eps']
    dist_stats.loc[:, 'avg_copay_post'] = dist_stats['tot_bind_copay_post'] / \
        dist_stats['migrated_eps']
    dist_stats.loc[:, 'avg_prem_post'] = dist_stats['tot_bind_prem_post'] / \
        dist_stats['migrated_eps']

    dist_stats.loc[:, 'util_change'] = dist_stats['migrated_eps'] / \
        dist_stats['tot_eps'] - 1
    return dist_stats

# add additional columns to core_df, including static copay stats and pre
# and post migration smart copay statsistics


def add_bind_stats_to_core_df(
        core_df_in,
        std_copay,
        smart_copay,
        dist_stats,
        trad_cs,
        util_inc_cap,
        std_util_floor):

    core_df = core_df_in.copy()
    core_df = core_df.assign(
        copay_pre=0,
        prem_pre=0,
        copay_post=0,
        prem_post=0,
        unit_cost_post=core_df['unit_cost'],
        tot_pay_post=0,
        addin_flg=0,
        event_count_post=core_df['event_count'])

    core_df.loc[set(core_df.index).intersection(
        set(std_copay.index)), 'copay_pre'] = std_copay
    core_df.loc[set(core_df.index).intersection(
        set(std_copay.index)), 'copay_post'] = std_copay

    idx = set(core_df.index).intersection(set(trad_cs.index))
    core_df.loc[idx,
                'trad_cost'] = core_df.loc[idx,
                                           'unit_cost'] * trad_cs[idx]

    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'copay_pre'] = dist_stats['avg_copay_pre']
    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'prem_pre'] = dist_stats['avg_prem_pre']
    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'copay_post'] = dist_stats['avg_copay_post']
    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'prem_post'] = dist_stats['avg_prem_post']

    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'unit_cost_post'] = core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                                                'unit_cost'] * (1 + dist_stats.loc[set(core_df.index).intersection(set(dist_stats.index)),
                                                                                   'avg_eps_change'])
    core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                'event_count_post'] = core_df.loc[set(core_df.index).intersection(set(dist_stats.index)),
                                                  'event_count'] * (1 + dist_stats.loc[set(core_df.index).intersection(set(dist_stats.index)),
                                                                                       'util_change'])

    trad_pay = core_df.loc[set(core_df.index).intersection(set(std_copay.index)),
                           'unit_cost'] * trad_cs[set(core_df.index).intersection(set(std_copay.index))]
    std_util_change = get_util_change(trad_pay, std_copay, core_df.loc[set(
        core_df.index).intersection(set(std_copay.index)), 'elas'])
    std_util_change[std_util_change != std_util_change] = 1
    std_util_change = np.maximum(
        std_util_floor, np.minimum(
            util_inc_cap, std_util_change))

    core_df.loc[set(core_df.index).intersection(set(std_copay.index)), 'event_count_post'] = core_df.loc[set(
        core_df.index).intersection(set(std_copay.index)), 'event_count'] * std_util_change

    core_df.loc[:, 'tot_pay_post'] = core_df['event_count_post'] * \
        core_df['unit_cost_post']

    core_df.loc[core_df['prem_pre'] != 0, 'addin_flg'] = 1

    return core_df


# cleanup to take in trad plan results
def intake_trad_plan_raw_df(raw_df):
    raw_df.index = raw_df.iloc[:, 0]
    raw_df.index.name = 'cov_fam'
    raw_df = raw_df.rename(columns={'Unnamed: 0': 'cov_fam'})
    return raw_df


def get_trad_cs(trad_df, fam=False):
    temp = trad_df.copy()
    temp = temp.loc[temp['cov_fam'] != 'CASH000']
    if not fam:
        cs = (temp['member_paid_ind'] -
              temp['fund_paid_ind']) / temp['pay_ind']
    else:
        cs = (temp['member_paid_fam'] -
              temp['fund_paid_fam']) / temp['pay_fam']
    cs[cs != cs] = 0
    cs.name = 'trad_cs'
    return cs

# calculate observed cost sharing for tradtional and bind plans.
# - both split by individual and family coverage
# - bind is split into with and without behavior change - reflecting smart copay effect of lower copay AND unit costs


def get_cs_df(core_df_ind, core_df_fam, trad_df):
    cov_fams = core_df_ind.loc[:, 'cov_fam']

    mbr_cs = pd.DataFrame(index=core_df_ind.index)
    mbr_cs.loc[:, :] = 1
    trad_df = trad_df.reindex(index=cov_fams)

    mbr_cs = mbr_cs.assign(trad_ind=(
        trad_df.loc[cov_fams, 'member_paid_ind']) / trad_df.loc[cov_fams, 'pay_ind'])
    mbr_cs = mbr_cs.assign(trad_fund_ind=(
        trad_df.loc[cov_fams, 'fund_paid_ind']) / trad_df.loc[cov_fams, 'pay_ind'])

    if core_df_fam is not None:
        mbr_cs = mbr_cs.assign(trad_fam=(
            trad_df.loc[cov_fams, 'member_paid_fam']) / trad_df.loc[cov_fams, 'pay_fam'])
        mbr_cs = mbr_cs.assign(trad_fund_fam=(
            trad_df.loc[cov_fams, 'fund_paid_fam']) / trad_df.loc[cov_fams, 'pay_fam'])

    mbr_cs = mbr_cs.assign(bind_pre_copay_ind=(
        core_df_ind.loc[cov_fams, 'copay_pre'] / core_df_ind.loc[cov_fams, 'unit_cost']))
    mbr_cs = mbr_cs.assign(bind_post_copay_ind=(
        core_df_ind.loc[cov_fams, 'copay_post'] / core_df_ind.loc[cov_fams, 'unit_cost_post']))

    if core_df_fam is not None:
        mbr_cs = mbr_cs.assign(bind_pre_copay_fam=(
            core_df_fam.loc[cov_fams, 'copay_pre'] / core_df_fam.loc[cov_fams, 'unit_cost']))
        mbr_cs = mbr_cs.assign(bind_post_copay_fam=(
            core_df_fam.loc[cov_fams, 'copay_post'] / core_df_fam.loc[cov_fams, 'unit_cost_post']))

    mbr_cs = np.minimum(1, mbr_cs)

    # allowing premiums to be greater than allowed
    mbr_cs = mbr_cs.assign(bind_pre_prem_ind=(
        core_df_ind.loc[cov_fams, 'prem_pre'] / core_df_ind.loc[cov_fams, 'unit_cost']))
    mbr_cs = mbr_cs.assign(bind_post_prem_ind=(
        core_df_ind.loc[cov_fams, 'prem_post'] / core_df_ind.loc[cov_fams, 'unit_cost_post']))

    if core_df_fam is not None:
        mbr_cs = mbr_cs.assign(bind_pre_prem_fam=(
            core_df_fam.loc[cov_fams, 'prem_pre'] / core_df_fam.loc[cov_fams, 'unit_cost']))
        mbr_cs = mbr_cs.assign(bind_post_prem_fam=(
            core_df_fam.loc[cov_fams, 'prem_post'] / core_df_fam.loc[cov_fams, 'unit_cost_post']))

    mbr_cs.loc[mbr_cs['trad_ind'] != mbr_cs['trad_ind']] = 0
    if core_df_fam is not None:
        mbr_cs.loc[mbr_cs['trad_fam'] != mbr_cs['trad_fam']] = 0
    return mbr_cs

# apply trad plan cost sharing to total truven data to summarize into key
# output. calculates any remaining account funding


def get_trad_summary(util, unit, cs_tot, cs_fund, fund_amt_remain, addin_flg):
    allow_vec = util.astype(float) / 1000 * unit
    allow_core = allow_vec.loc[addin_flg == 0].sum()
    allow_addin = allow_vec.loc[addin_flg == 1].sum()
    mbr_oop_core = (allow_vec.loc[addin_flg == 0]
                    * cs_tot.loc[addin_flg == 0]).sum()
    mbr_oop_addin = (allow_vec.loc[addin_flg == 1]
                     * cs_tot.loc[addin_flg == 1]).sum()
    fund_applied_core = (
        allow_vec.loc[addin_flg == 0] * cs_fund.loc[addin_flg == 0]).sum()
    fund_applied_addin = (
        allow_vec.loc[addin_flg == 1] * cs_fund.loc[addin_flg == 1]).sum()

    return [
        allow_core,
        allow_addin,
        mbr_oop_core,
        mbr_oop_addin,
        0,
        fund_applied_core,
        fund_applied_addin,
        fund_amt_remain]

# apply trad plan cost sharing to total truven data, at cov fam level.
# calculates any remaining account funding


def get_trad_detail(
        util,
        unit,
        cs_tot,
        cs_fund,
        fund_amt_tot,
        fund_amount_remain,
        addin_flg):
    r = pd.DataFrame(
        index=util.index,
        columns=[
            'addin_flg',
            'utilization_per_1k',
            'unit_cost',
            'pepy_allowed',
            'mbr_oop',
            'addin_prem',
            'fund_applied',
            'fund_remaining'])
    r.loc[:, :] = 0
    allow_vec = util.astype(float) / 1000 * unit
    r.loc[:, 'addin_flg'] = addin_flg
    r.loc[:, 'utilization_per_1k'] = util
    r.loc[:, 'unit_cost'] = unit
    r.loc[:, 'pepy_allowed'] = allow_vec
    r.loc[:, 'mbr_oop'] = allow_vec * cs_tot
    r.loc[:, 'addin_prem'] = 0
    r.loc[:, 'fund_applied'] = allow_vec * cs_fund
    r.loc['cash', :] = [0, 1000, 0, fund_amt_tot, 0, 0,
                        r.loc[:, 'fund_applied'].sum(), fund_amount_remain]
    return r

# apply bind plan cost sharing to get summary result figures


def get_bind_summary(util, unit, cs_copay, cs_prem, oopm, addin_flg):
    allow_vec = util.astype(float) / 1000 * unit
    allow_core = allow_vec.loc[addin_flg == 0].sum()
    allow_addin = allow_vec.loc[addin_flg == 1].sum()
    mbr_oop_core = np.minimum(
        oopm, (allow_vec.loc[addin_flg == 0] * cs_copay.loc[addin_flg == 0]).sum())
    mbr_oop_addin = np.minimum(oopm -
                               mbr_oop_core, (allow_vec.loc[addin_flg == 1] *
                                              cs_copay.loc[addin_flg == 1]).sum())
    prem = (allow_vec * cs_prem).sum()
    return [
        allow_core,
        allow_addin,
        mbr_oop_core,
        mbr_oop_addin,
        prem,
        0,
        0,
        0]

# apply bind plan cost sharing to get result figure detail


def get_bind_detail(util, unit, cs_copay, cs_prem, oopm, addin_flg):
    r = pd.DataFrame(
        index=util.index,
        columns=[
            'addin_flg',
            'utilization_per_1k',
            'unit_cost',
            'pepy_allowed',
            'mbr_oop',
            'addin_prem',
            'fund_applied',
            'fund_remaining'])
    r.loc[:, :] = 0
    allow_vec = util.astype(float) / 1000 * unit
    r.loc[:, 'addin_flg'] = addin_flg
    r.loc[:, 'utilization_per_1k'] = util
    r.loc[:, 'unit_cost'] = unit
    r.loc[:, 'pepy_allowed'] = allow_vec
    r.loc[:, 'mbr_oop'] = allow_vec * cs_copay
    r.loc[:, 'addin_prem'] = allow_vec * cs_prem
    r.loc[:, 'fund_applied'] = 0
    r.loc[:, 'fund_remaining'] = 0
    r.loc['cash', :] = 0
    return r

# returns expected reduction in member copays due to reaching the OOPM, by coverage family. Based on distribution of
# copays for a sample bind plan and observed copay counts by percentile
# total copay for each family (split into ind/fam)


def get_oopm_reduction_factors(copays, copay_dist, oopm, util_change=None):
    copays = copays.rename('copay')
    copay_df = copay_dist.set_index('cov_fam')
    copay_df = copay_df.join(copays)
    if util_change is not None:
        util_change = util_change.rename('util_change')
        copay_df = copay_df.join(util_change)
       # util_change.to_csv("util_change.csv", index=True)
        copay_df['per_fam_count'] = copay_df['per_fam_count'].astype(
            float) * copay_df['util_change']

    # for 999999 used for Not covered
    copay_df.loc[copay_df['copay'] >= 800000, 'copay'] = 0
    copay_df.loc[:, 'per_fam_copay'] = copay_df['per_fam_count'].astype(
        float) * copay_df['copay']

    copay_gdf = copay_df.groupby('grp')
    grp_copays_raw = copay_gdf['per_fam_copay'].sum()
    grp_copays_capped = np.minimum(oopm, grp_copays_raw)
    grp_factors = grp_copays_capped / grp_copays_raw
    grp_factors.name = 'factor'

    copay_df = copay_df.join(grp_factors, on='grp', how='left')
    copay_df.loc[:, 'agg_copay'] = copay_df['copay_count'] * copay_df['copay']
    copay_df.loc[:, 'agg_copay_adj'] = copay_df['agg_copay'] * \
        copay_df['factor']
    copay_gdf = copay_df.groupby('cov_fam')
    cov_fam_adj = copay_gdf['agg_copay', 'agg_copay_adj'].sum()
    adjustment = cov_fam_adj['agg_copay_adj'] / cov_fam_adj['agg_copay']
    adjustment.name = 'factor'
    adjustment[adjustment != adjustment] = 1
    return adjustment

# adjust other items down (utilization) to account for episodic addin costs not caught in the encounter event
# addin adjusemtne applied to unit costs


def adjust_core_df_for_episodic_cost(
        core_df_in,
        addin_idx,
        core_idx,
        addin_enc_pct):
    core_df = core_df_in.copy()
    addin_df = core_df.loc[addin_idx].copy()
    addin_agg_enc_reduction = addin_df['tot_pay'].sum(
    ) - addin_df['tot_pay_post'].sum()
    addin_dec_factor = 1 / addin_enc_pct

    eps_base_extra_savings = addin_agg_enc_reduction * (addin_dec_factor - 1)

    core_dec_factor = 1 - (eps_base_extra_savings /
                           core_df.loc[core_idx, 'tot_pay_post'].sum())

    # core adjustment
    core_df.loc[core_idx,
                'event_count_post'] = core_df.loc[core_idx,
                                                  'event_count_post'] * float(core_dec_factor)
    core_df.loc[core_idx, 'tot_pay_post'] = core_df.loc[core_idx,
                                                        'tot_pay_post'] * float(core_dec_factor)
    core_df.loc[core_idx, 'post_util_1k'] = core_df.loc[core_idx,
                                                        'post_util_1k'] * float(core_dec_factor)

    return core_df

# wrapper to produce summary of traditional plan, and bind plans. Note that the bind results are specific to experience
# associated with a given traditional plan. Note that allowed amounts are
# trended in this step (assumed all trend attributed to unit trend)


class BindEvaluator:

    def __init__(self):
        self.core_df_in = getRefTable(
            'public.adj_model_cov_fam_summary_45')
        self.smart_dist_df_in = getRefTable(
            'public.adj_model_smart_copay_prov_ptile_dist_45')
        self.exp_base = getRefTable(
            'public.adj_model_membership_summary')
        self.copay_dist = getRefTable(
            'public.adj_model_oopm_grouped_copay_counts_45')

    def intake_bind_raw_df(self, df):
        self.bind_plan_raw_df = df

    def intake_BindPlan(self, BP):
        self.bind_plan_raw_df = BP.to_raw_df()

    def intake_trad_df(self, df):
        self.trad_df_raw = df

    def get_summary_stats(
            self,
            get_detail=False,
            no_family=False,
            util_inc_cap=1.2,
            inelastic_pct=.2,
            std_util_floor=0.8,
            boost=1,
            addin_enc_pct=0.8,
            addin_gate_pct=0.25,
            addin_util_floor=.65):

        # dont modify originals
        trad_df = intake_trad_plan_raw_df(self.trad_df_raw.copy())
        bind_plan_raw_df = self.bind_plan_raw_df.copy()
        core_df = self.core_df_in.copy()
        smart_dist_df = self.smart_dist_df_in.copy()
        exp_base = self.exp_base.copy()
        copay_dist = self.copay_dist.copy()

        (global_vals, std_copay, smart_copay_df) = intake_bind_plan_raw_df(
            bind_plan_raw_df)

        smart_dist_df.index = smart_dist_df['cov_fam']
        smart_dist_df = smart_dist_df.loc[smart_copay_df.index]
        core_df.index = core_df['cov_fam']

        core_df.loc[:, 'tot_pay'] = core_df.loc[:, 'tot_pay'].astype(
            float) * float(global_vals['trend'])
        core_df.loc[:, 'unit_cost'] = core_df.loc[:, 'unit_cost'].astype(
            float) * float(global_vals['trend'])

        core_df_ind = core_df.loc[core_df['tier'] == 'ind']

        smart_dist_df_ind = apply_smart_copay_to_dist(smart_dist_df,
                                                      smart_copay_df,
                                                      trad_cs=get_trad_cs(trad_df,
                                                                          fam=False),
                                                      elas=core_df_ind['elas'],
                                                      boost=boost,
                                                      util_inc_cap=util_inc_cap,
                                                      pcp_unit=core_df_ind.loc['XX00001',
                                                                               'unit_cost'],
                                                      scp_unit=core_df_ind.loc['XX00002',
                                                                               'unit_cost'],
                                                      inelastic_pct=inelastic_pct,
                                                      addin_gate_pct=addin_gate_pct,
                                                      addin_util_floor=addin_util_floor)
        dist_stats_ind = get_dist_stats(smart_dist_df_ind)

        if not no_family:
            core_df_fam = core_df.loc[core_df['tier'] == 'fam']
            smart_dist_df_fam = apply_smart_copay_to_dist(smart_dist_df,
                                                          smart_copay_df,
                                                          trad_cs=get_trad_cs(trad_df,
                                                                              fam=True),
                                                          elas=core_df_fam['elas'],
                                                          boost=boost,
                                                          util_inc_cap=util_inc_cap,
                                                          pcp_unit=core_df_fam.loc['XX00001',
                                                                                   'unit_cost'],
                                                          scp_unit=core_df_fam.loc['XX00002',
                                                                                   'unit_cost'],
                                                          inelastic_pct=inelastic_pct,
                                                          addin_gate_pct=addin_gate_pct,
                                                          addin_util_floor=addin_util_floor)
            dist_stats_fam = get_dist_stats(smart_dist_df_fam)

        ind_subyears = exp_base.loc[exp_base['tier']
                                    == 'ind', 'subyears'].iloc[0]
        fam_subyears = exp_base.loc[exp_base['tier']
                                    == 'fam', 'subyears'].iloc[0]
        ind_fund_count = exp_base.loc[exp_base['tier']
                                      == 'ind', 'distinct_sub_count'].iloc[0]
        fam_fund_count = exp_base.loc[exp_base['tier']
                                      == 'fam', 'distinct_sub_count'].iloc[0]

        ind_pepy_unused_fund = trad_df.loc['CASH000', 'fund_paid_ind'] / (trad_df.sum(
        )['fund_paid_ind'] / trad_df.loc['CASH000', 'pay_ind']) * float(ind_fund_count / ind_subyears)
        if not no_family:
            fam_pepy_unused_fund = trad_df.loc['CASH000', 'fund_paid_fam'] / (trad_df.sum(
            )['fund_paid_fam'] / trad_df.loc['CASH000', 'pay_fam']) * float(fam_fund_count / fam_subyears)
        else:
            fam_pepy_unused_fund = 0

        addin_idx = smart_copay_df.loc[smart_copay_df['payroll_min']
                                       == smart_copay_df['payroll_min']].index
        addin_idx = set(addin_idx).intersection(set(core_df_ind.index))
        core_idx = set(core_df_ind.index) - addin_idx

        core_df_ind = add_bind_stats_to_core_df(
            core_df_ind,
            std_copay,
            smart_copay_df,
            dist_stats_ind,
            trad_cs=get_trad_cs(
                trad_df,
                fam=False),
            util_inc_cap=util_inc_cap,
            std_util_floor=std_util_floor)
        if not no_family:
            core_df_fam = add_bind_stats_to_core_df(
                core_df_fam, std_copay, smart_copay_df, dist_stats_fam, trad_cs=get_trad_cs(
                    trad_df, fam=True), util_inc_cap=util_inc_cap, std_util_floor=std_util_floor)

        ind_oop_adjust_pre = get_oopm_reduction_factors(
            core_df_ind['copay_pre'], copay_dist.loc[copay_dist['tier'] == 'ind'], float(global_vals['oopm_ind']))
        core_df_ind.loc[:, 'copay_pre'] = core_df_ind.loc[:,
                                                          'copay_pre'] * ind_oop_adjust_pre[core_df_ind.index]

        if not no_family:
            fam_oop_adjust_pre = get_oopm_reduction_factors(
                core_df_fam['copay_pre'], copay_dist.loc[copay_dist['tier'] == 'fam'], float(global_vals['oopm_fam']))
            core_df_fam.loc[:, 'copay_pre'] = core_df_fam.loc[:,
                                                              'copay_pre'] * fam_oop_adjust_pre[core_df_fam.index]

        ind_oop_adjust_post = get_oopm_reduction_factors(core_df_ind['copay_post'], copay_dist.loc[copay_dist['tier'] == 'ind'], float(
            global_vals['oopm_ind']), util_change=(core_df_ind['event_count_post'] / core_df_ind['event_count']))
        core_df_ind.loc[:, 'copay_post'] = core_df_ind.loc[:,
                                                           'copay_post'] * ind_oop_adjust_post[core_df_ind.index]
        if not no_family:
            fam_oop_adjust_post = get_oopm_reduction_factors(core_df_fam['copay_post'], copay_dist.loc[copay_dist['tier'] == 'fam'], float(
                global_vals['oopm_fam']), util_change=(core_df_fam['event_count_post'] / core_df_fam['event_count']))
            core_df_fam.loc[:, 'copay_post'] = core_df_fam.loc[:,
                                                               'copay_post'] * fam_oop_adjust_post[core_df_fam.index]

        core_df_ind['base_util_1k'] = core_df_ind['event_count'] / \
            float(ind_subyears) * 1000
        core_df_ind['post_util_1k'] = core_df_ind['event_count_post'] / \
            float(ind_subyears) * 1000
        core_df_ind = adjust_core_df_for_episodic_cost(
            core_df_ind, addin_idx, core_idx, addin_enc_pct)
        if not no_family:
            core_df_fam['base_util_1k'] = core_df_fam['event_count'] / \
                float(fam_subyears) * 1000
            core_df_fam['post_util_1k'] = core_df_fam['event_count_post'] / \
                float(fam_subyears) * 1000
            core_df_fam = adjust_core_df_for_episodic_cost(
                core_df_fam, addin_idx, core_idx, addin_enc_pct)

        if not no_family:
            mbr_cs = get_cs_df(core_df_ind, core_df_fam, trad_df)
        else:
            mbr_cs = get_cs_df(core_df_ind, None, trad_df)

        if get_detail:

            trad_detail_ind = get_trad_detail(core_df_ind['base_util_1k'],
                                              core_df_ind['unit_cost'],
                                              mbr_cs['trad_ind'],
                                              mbr_cs['trad_fund_ind'],
                                              trad_df.loc['CASH000',
                                                          'pay_ind'],
                                              ind_pepy_unused_fund,
                                              core_df_ind['addin_flg'])

            bind_detail_no_behav_ind = get_bind_detail(
                core_df_ind['base_util_1k'],
                core_df_ind['unit_cost'],
                mbr_cs['bind_pre_copay_ind'],
                mbr_cs['bind_pre_prem_ind'],
                float(
                    global_vals['oopm_ind']),
                core_df_ind['addin_flg'])

            bind_detail_w_behav_ind = get_bind_detail(
                core_df_ind['post_util_1k'],
                core_df_ind['unit_cost_post'],
                mbr_cs['bind_post_copay_ind'],
                mbr_cs['bind_post_prem_ind'],
                float(
                    global_vals['oopm_ind']),
                core_df_ind['addin_flg'])

            trad_detail_fam = None
            bind_detail_no_behav_fam = None
            bind_detail_w_behav_fam = None

            if not no_family:
                trad_detail_fam = get_trad_detail(core_df_fam['base_util_1k'],
                                                  core_df_fam['unit_cost'],
                                                  mbr_cs['trad_fam'],
                                                  mbr_cs['trad_fund_fam'],
                                                  trad_df.loc['CASH000',
                                                              'pay_fam'],
                                                  fam_pepy_unused_fund,
                                                  core_df_fam['addin_flg'])

                bind_detail_no_behav_fam = get_bind_detail(
                    core_df_fam['base_util_1k'],
                    core_df_fam['unit_cost'],
                    mbr_cs['bind_pre_copay_fam'],
                    mbr_cs['bind_pre_prem_fam'],
                    float(
                        global_vals['oopm_fam']),
                    core_df_fam['addin_flg'])

                bind_detail_w_behav_fam = get_bind_detail(
                    core_df_fam['post_util_1k'],
                    core_df_fam['unit_cost_post'],
                    mbr_cs['bind_post_copay_fam'],
                    mbr_cs['bind_post_prem_fam'],
                    float(
                        global_vals['oopm_fam']),
                    core_df_fam['addin_flg'])

            return [
                trad_detail_ind,
                trad_detail_fam,
                bind_detail_no_behav_ind,
                bind_detail_no_behav_fam,
                bind_detail_w_behav_ind,
                bind_detail_w_behav_fam]
        else:
            pepy_summary = pd.DataFrame(
                index=[
                    'allowed_core',
                    'allowed_addin',
                    'mbr_oop_core',
                    'mbr_oop_addin',
                    'prem',
                    'fund_applied_core',
                    'fund_applied_addin',
                    'fund_remaining'],
                columns=[
                    'trad_ind',
                    'trad_fam',
                    'bind_no_behav_ind',
                    'bind_final_ind',
                    'bind_no_behav_fam',
                    'bind_final_fam'])
            pepy_summary.loc[:, :] = 0

            pepy_summary['trad_ind'] = get_trad_summary(
                core_df_ind['base_util_1k'],
                core_df_ind['unit_cost'],
                mbr_cs['trad_ind'],
                mbr_cs['trad_fund_ind'],
                ind_pepy_unused_fund,
                core_df_ind['addin_flg'])

            pepy_summary['bind_no_behav_ind'] = get_bind_summary(
                core_df_ind['base_util_1k'],
                core_df_ind['unit_cost'],
                mbr_cs['bind_pre_copay_ind'],
                mbr_cs['bind_pre_prem_ind'],
                float(
                    global_vals['oopm_ind']),
                core_df_ind['addin_flg'])

            pepy_summary['bind_final_ind'] = get_bind_summary(
                core_df_ind['post_util_1k'],
                core_df_ind['unit_cost_post'],
                mbr_cs['bind_post_copay_ind'],
                mbr_cs['bind_post_prem_ind'],
                float(
                    global_vals['oopm_ind']),
                core_df_ind['addin_flg'])

            if not no_family:
                pepy_summary['trad_fam'] = get_trad_summary(
                    core_df_fam['base_util_1k'],
                    core_df_fam['unit_cost'],
                    mbr_cs['trad_fam'],
                    mbr_cs['trad_fund_fam'],
                    fam_pepy_unused_fund,
                    core_df_fam['addin_flg'])

                pepy_summary['bind_no_behav_fam'] = get_bind_summary(
                    core_df_fam['base_util_1k'],
                    core_df_fam['unit_cost'],
                    mbr_cs['bind_pre_copay_fam'],
                    mbr_cs['bind_pre_prem_fam'],
                    float(
                        global_vals['oopm_fam']),
                    core_df_fam['addin_flg'])

                pepy_summary['bind_final_fam'] = get_bind_summary(
                    core_df_fam['post_util_1k'],
                    core_df_fam['unit_cost_post'],
                    mbr_cs['bind_post_copay_fam'],
                    mbr_cs['bind_post_prem_fam'],
                    float(
                        global_vals['oopm_fam']),
                    core_df_fam['addin_flg'])
            return pepy_summary

#############
