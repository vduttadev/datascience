# coding=utf-8

"""
This is aadjudication script.

This python script creates connection to get the Truven Data and process
traditional plan
__version__ = "1.0"
"""
import psycopg2
import os
import numpy as np
import pandas as pd
import time
import logging
import psutil
from django.conf import settings
from multiprocessing import Queue, Process

logger = logging.getLogger('control_panel')
queueProcessid = 1001


def pids_active(pid):
    """
    This function find pids of computer and return the valid.
    """
    try:
        process = psutil.Process(pid)
        data = {"pid": process.pid,
                "status": process.status(),
                "percent_cpu_used": process.cpu_percent(interval=0.0),
                "percent_memory_used": process.memory_percent()}

    except (psutil.ZombieProcess, psutil.AccessDenied, psutil.NoSuchProcess):
        data = {"pid": pid,
                "status": "Zombie or Killed"}

    return data


def get_conn():
    """
    Get the conneciton to DB
    All the configurations are defined in env file
    """
    endpoint = settings.REFDB_HOST
    user = settings.REFDB_USER
    password = settings.REFDB_PASSWORD
    port = settings.REFDB_PORT
    dbname = settings.REFDB_DB
    conn = psycopg2.connect(host=endpoint, user=user,
                            port=port, password=password, dbname=dbname)
    return conn


def queue_loader(queue, query):  # constantly load queue until done
    cm = ConnectionManager(query)
    while True:
        if not queue.full():
            logger.info('poping block for queue...')
            block = cm.pop_block()
            logger.info('loading block into queue')
            queue.put(block)
            if len(block) == 0:
                queue.close()
                break
        else:
            time.sleep(1)


# get results of a single (small) query and close the connection right away
def get_query_result(Q):
    conn = get_conn()
    cur = conn.cursor('PD')
    cur.execute(Q)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# Deals with database connection and only returns clean blocks
# that do not split claims by efamid
# Query must have a column called 'efamid' to split into chunks
class ConnectionManager:
    # initialize with a psycopg2 connection to pull from 'query'
    def __init__(self, query, blocksize=100000):
        self.conn = get_conn()
        self.cur = self.conn.cursor('PD_cursor')
        self.cur.execute(query)
        self.blocksize = blocksize  # use to adjust fetch size
        self.init_pull = False
        self.q = Queue(maxsize=2)

    # returns True if new rows were available to fetch - should only be
    # used within the class
    def pull_block(self):
        logger.info('starting fetch...')
        t1 = time.time()
        add_block = pd.DataFrame(self.cur.fetchmany(self.blocksize),
                                 columns=[desc[0]
                                          for desc in self.cur.description])
        t2 = time.time()
        logger.info('done. sec. elapsed: %s' % str(t2-t1))
        if self.init_pull:
            self.block = pd.concat([self.block, add_block], axis=0)
        else:
            self.block = add_block
            self.init_pull = True
        if len(add_block) == 0:
            return False
        else:
            return True

    # returns a claims block and holds on to only the last efamid, will
    # eventially return an empty DataFrame

    def pop_block(self):
        if not self.pull_block():  # if no new rows, catches last block, and empty
            return_block = self.block
            self.block = pd.DataFrame(
                columns=[desc[0] for desc in self.cur.description])
            return return_block
        last_efamid = self.block.iloc[-1]['efamid']
        hold_block = self.block.loc[self.block['efamid'] == last_efamid]
        return_block = self.block.loc[self.block['efamid'] != last_efamid]
        if len(hold_block) == len(
                self.block):  # only one family in block, even after a pull
            self.block = return_block  # will be empty
            return hold_block  # special case to dump the single family
        else:
            self.block = hold_block
            return return_block

    def close_conn(self):
        self.cur.close()
        self.conn.close()


# simple container to specify rules for a spectific coverage type
class PlanRule:
    def __init__(
            self,
            coverage_name,
            apply_ded,
            not_covered,
            coins,
            min_pay,
            max_pay,
            med_rx):
        self.cov_name = coverage_name
        self.apply_ded = apply_ded
        self.not_covered = not_covered
        self.coins = coins
        self.min_pay = min_pay
        self.max_pay = max_pay
        self.med_rx = med_rx


# contains some global factors, and a DataFrame of PlanRule objects to apply
# to specific types of coverage
class PlanDesign:

    def __init__(self, opportunityId, benefitPlanId, planName, ind_ded,
                 fam_ded, rx_ind_ded, rx_fam_ded, ind_oopm, fam_oopm,
                 ind_oopm_rx, fam_oopm_rx,
                 funding_ind, funding_fam, tf_ded_flag, tf_oopm_flag,
                 split_rx_ded, split_rx_oopm, trend, ACA_ind_oopm=8150):

        # indicators
        self.planName = planName
        self.opportunityId = opportunityId
        self.benefitPlanId = benefitPlanId
        # boolean indicator for true family deductible
        self.tf_ded_flag = tf_ded_flag == 1
        self.tf_oopm_flag = tf_oopm_flag == 1
        # boolean indicator for separate rx ded. Ignore rx deductibles if false
        self.split_ded = split_rx_ded == 1
        self.split_oopm = split_rx_oopm == 1
        self.trend = float(trend)
        self.ACA_ind_oopm = float(ACA_ind_oopm)

        # deductibles
        self.ind_ded = float(ind_ded)
        self.fam_ded = float(fam_ded)
        if self.split_ded:
            self.ind_ded_rx = float(rx_ind_ded)
            self.fam_ded_rx = float(rx_fam_ded)
        else:
            self.ind_ded_rx = float(ind_ded)
            self.fam_ded_rx = float(fam_ded)

        # OOPM
        self.ind_oopm = float(ind_oopm)
        self.fam_oopm = float(fam_oopm)
        if self.split_oopm:
            self.ind_oopm_rx = float(ind_oopm_rx)
            self.fam_oopm_rx = float(fam_oopm_rx)
        else:
            self.ind_oopm_rx = float(ind_oopm)
            self.fam_oopm_rx = float(fam_oopm)

        self.ind_fund = float(funding_ind)
        self.fam_fund = float(funding_fam)
        self.rules = pd.DataFrame(columns=['not_covered', 'ded_mem', 'ded_fam',
                                           'coins', 'oopm_mem', 'oopm_fam',
                                           'min_pay', 'max_pay', 'med_rx'])

    def add_rule(self, pr):
        med_rx = pr.med_rx
        #  get base ded/OOPM for m/r split
        if med_rx == 'm':
            single_ded = self.ind_ded
            family_ded = self.fam_ded
            single_oopm = self.ind_oopm
            family_oopm = self.fam_oopm
        else:
            single_ded = self.ind_ded_rx
            family_ded = self.fam_ded_rx
            single_oopm = self.ind_oopm_rx
            family_oopm = self.fam_oopm_rx

        # set effective deductibles
        if not pr.apply_ded:
            single_ded_effective = 0
            fam_embedded_ind_ded = 0
            family_ded_effective = 0
        elif self.tf_ded_flag:
            single_ded_effective = single_ded
            fam_embedded_ind_ded = family_ded
            family_ded_effective = family_ded
        else:
            single_ded_effective = single_ded
            fam_embedded_ind_ded = single_ded
            family_ded_effective = family_ded

        # set effective OOPM
        single_oopm_effective = single_oopm
        family_oopm_effective = family_oopm
        if self.tf_oopm_flag:
            fam_embedded_ind_oopm = family_oopm
        else:
            fam_embedded_ind_oopm = np.minimum(single_oopm, self.ACA_ind_oopm)
        self.rules.loc['single:' + pr.cov_name] = [pr.not_covered,
                                                   single_ded_effective,
                                                   single_ded_effective,
                                                   pr.coins,
                                                   single_oopm_effective,
                                                   single_oopm_effective,
                                                   pr.min_pay, pr.max_pay,
                                                   med_rx]

        self.rules.loc['family:' + pr.cov_name] = [pr.not_covered,
                                                   fam_embedded_ind_ded,
                                                   family_ded_effective,
                                                   pr.coins,
                                                   fam_embedded_ind_oopm,
                                                   family_oopm_effective,
                                                   pr.min_pay, pr.max_pay,
                                                   med_rx]


# Actual math to process payment - used in vectorized fashion -
# returns the amount paid in deductible

def adjudicate_line_ded(ded_mem,
                        ded_fam,  # Plan design
                        prior_ind_ded, prior_fam_ded,  # Accumulator Info
                        pay,  # pay == 'pay' in truven - i.e. allowed
                        oopm_mem,
                        oopm_fam, prior_ind_paid,
                        prior_fam_paid):
    # for cases when split ded but combined OOPM would negate ded payment
    remaining_ded = np.maximum(np.minimum(
        (ded_mem - prior_ind_ded), (ded_fam - prior_fam_ded)), 0)
    ded_payment = np.minimum(pay, remaining_ded)
    remaining_oopm = np.maximum(np.minimum((oopm_mem - prior_ind_paid),
                                           (oopm_fam - prior_fam_paid)), 0)
    ded_payment = np.minimum(ded_payment, remaining_oopm)
    return ded_payment


# Actual math to process payment - used in vectorized fashion -
# returns the total amount paid (inc. deductible)
def adjudicate_line_other(coins, oopm_mem, oopm_fam,
                          min_pay,
                          max_pay,  # Plan design (w/ true family status)
                          prior_ind_paid,
                          prior_fam_paid,  # Accumulator Info
                          pay, ded_payment):
    pay_after_ded = pay - ded_payment
    remaining_oopm = np.maximum(np.minimum(
        (oopm_mem - prior_ind_paid - ded_payment),
        (oopm_fam - prior_fam_paid - ded_payment)), 0)
    capped_payment = np.minimum(pay_after_ded * coins, max_pay)
    capped_payment = np.maximum(capped_payment,
                                np.minimum(min_pay, pay_after_ded))
    other_payment = np.minimum(capped_payment, remaining_oopm)
    return other_payment


# Actual math to process payment - used in vectorized fashion -
# returns the amount of member exp. covered by funding
def get_fund_pay(ded_pay, other_pay, fund):
    ded_pay = ded_pay.reset_index(drop=True)
    other_pay = other_pay.reset_index(drop=True)
    fund = fund.reset_index(drop=True)
    return np.minimum(fund, ded_pay + other_pay)


def rotate_list(L):
    return L[-1:] + L[:-1]


# add data/fields to claims pull to allow adjudication processing.
# Note that allowed amounts are trended in this step
# (assumed all trend attributed to unit trend)
def block_processing_setup(claims_df, plan):
    mem_counts = claims_df.groupby('efamid')['enrolid'].nunique()
    proc_claims_df = claims_df.assign(
        tier=np.minimum(mem_counts[claims_df['efamid']].tolist(), 2))
    count_map = pd.Series(['single', 'family'], index=[1, 2])
    proc_claims_df.loc[:, 'tier'] = count_map[proc_claims_df['tier']].tolist()
    plan_expanded_df = plan.rules.reindex(index=proc_claims_df['tier'] + ':' +
                                          proc_claims_df['item_type_id'])
    plan_expanded_df.index = proc_claims_df.index
    proc_claims_df = pd.concat([proc_claims_df, plan_expanded_df], axis=1)
    # 0: not processed, 1: not processed - next round, 2: done
    proc_claims_df = proc_claims_df.assign(proc_state=0)
    proc_claims_df = proc_claims_df.assign(fund_paid=0)
    proc_claims_df = proc_claims_df.assign(member_paid=0)
    proc_claims_df.loc[:, 'pay'] = proc_claims_df['pay'].astype(float)
    proc_claims_df.loc[:, 'pay'] = proc_claims_df['pay'] * plan.trend
    proc_claims_df.loc[proc_claims_df['efamid'] !=
                       rotate_list(proc_claims_df['efamid'].tolist()),
                       'proc_state'] = 1

    del plan_expanded_df
    del count_map
    return proc_claims_df

# Apply adjudication rules to each claim and return processed claims
# along with updated trackers to store aggregate plan stats.


# Iterates through each efamid's nth claim until a round is
# reached with less than min_step new lines processed.
# Any remaining unprocessed claims are then returned and
# re-fed into process_block. Final call will have min_step == 0
def process_block(claims_df=None, remnant_claims_df=None,
                  ind_tracker_prior=None, fam_tracker_prior=None,
                  min_step=0, ind_fund=0.0, fam_fund=0.0,
                  split_ded=False, split_oopm=False):

    ind_fund = float(ind_fund)
    fam_fund = float(fam_fund)

    # Set up trackers for new efamid/enrolid, appended old one if given
    if claims_df is not None:
        ind_tracker = pd.DataFrame(
            index=claims_df['enrolid'].unique().tolist(),
            columns=[
                'ind_ded_mx',
                'ind_ded_rx',
                'ind_paid_mx',
                'ind_paid_rx',
                'allow',
                'ind_fund'])
        ind_tracker.iloc[:, :] = 0.0
        ind_tracker.loc[claims_df.loc[(claims_df['proc_state'] == 1)
                                      & (claims_df['tier'] == 'single'),
                                      'enrolid'], 'ind_fund'] = ind_fund

        fam_tracker = pd.DataFrame(index=claims_df['efamid'].unique().tolist(),
                                   columns=['fam_ded_mx', 'fam_ded_rx',
                                            'fam_paid_mx', 'fam_paid_rx',
                                            'allow', 'fam_fund'])
        fam_tracker.iloc[:, :] = 0.0
        fam_tracker.loc[claims_df.loc[(claims_df['proc_state'] == 1)
                                      & (claims_df['tier'] == 'family'),
                                      'efamid'], 'fam_fund'] = fam_fund
    else:
        ind_tracker = pd.DataFrame(
            columns=[
                'ind_ded_mx',
                'ind_ded_rx',
                'ind_paid_mx',
                'ind_paid_rx',
                'allow',
                'ind_fund'])
        fam_tracker = pd.DataFrame(
            columns=[
                'fam_ded_mx',
                'fam_ded_rx',
                'fam_paid_mx',
                'fam_paid_rx',
                'allow',
                'fam_fund'])

    if ind_tracker_prior is not None:
        ind_tracker = pd.concat([ind_tracker_prior, ind_tracker])

    if fam_tracker_prior is not None:
        fam_tracker = pd.concat([fam_tracker_prior, fam_tracker])

    if remnant_claims_df is not None:
        claims_df = pd.concat([claims_df, remnant_claims_df])

    while len(claims_df.loc[claims_df['proc_state'] == 2]) < len(claims_df):
        # Vectorized calculation of ded/other payments, until all processed, or less than min_step new lines processed
        # in an iteration

        # split data by claim type med/rx
        x_m = claims_df.loc[(claims_df['proc_state'] == 1)
                            & (claims_df['med_rx'] == 'm')]
        x_r = claims_df.loc[(claims_df['proc_state'] == 1)
                            & (claims_df['med_rx'] == 'r')]

        # get deductible accumulators
        prior_ind_ded_m = ind_tracker.loc[x_m['enrolid'], 'ind_ded_mx'].astype(
            float)
        prior_ind_ded_r = ind_tracker.loc[x_r['enrolid'], 'ind_ded_rx'].astype(
            float)
        prior_fam_ded_m = fam_tracker.loc[x_m['efamid'], 'fam_ded_mx'].astype(
            float)
        prior_fam_ded_r = fam_tracker.loc[x_r['efamid'], 'fam_ded_rx'].astype(
            float)

        # get oopm (paid) accumulators
        prior_ind_paid_m = ind_tracker.loc[x_m['enrolid'], 'ind_paid_mx'].astype(
            float)
        prior_ind_paid_r = ind_tracker.loc[x_r['enrolid'], 'ind_paid_rx'].astype(
            float)
        prior_fam_paid_m = fam_tracker.loc[x_m['efamid'], 'fam_paid_mx'].astype(
            float)
        prior_fam_paid_r = fam_tracker.loc[x_r['efamid'], 'fam_paid_rx'].astype(
            float)

        x_m = x_m.reset_index()
        x_r = x_r.reset_index()

        # reset indexs to match x_m, x_r
        prior_ind_ded_m = prior_ind_ded_m.reset_index(drop=True)
        prior_fam_ded_m = prior_fam_ded_m.reset_index(drop=True)
        prior_ind_paid_m = prior_ind_paid_m.reset_index(drop=True)
        prior_fam_paid_m = prior_fam_paid_m.reset_index(drop=True)

        prior_ind_ded_r = prior_ind_ded_r.reset_index(drop=True)
        prior_fam_ded_r = prior_fam_ded_r.reset_index(drop=True)
        prior_ind_paid_r = prior_ind_paid_r.reset_index(drop=True)
        prior_fam_paid_r = prior_fam_paid_r.reset_index(drop=True)

        ded_payment_m = adjudicate_line_ded(
            x_m['ded_mem'].astype(float),
            x_m['ded_fam'].astype(float),
            prior_ind_ded_m,
            prior_fam_ded_m,
            x_m['pay'],
            x_m['oopm_mem'].astype(float),
            x_m['oopm_fam'].astype(float),
            prior_ind_paid_m,
            prior_fam_paid_m)
        ded_payment_r = adjudicate_line_ded(
            x_r['ded_mem'].astype(float),
            x_r['ded_fam'].astype(float),
            prior_ind_ded_r,
            prior_fam_ded_r,
            x_r['pay'],
            x_r['oopm_mem'].astype(float),
            x_r['oopm_fam'].astype(float),
            prior_ind_paid_r,
            prior_fam_paid_r)

        other_payment_m = adjudicate_line_other(
            x_m['coins'],
            x_m['oopm_mem'].astype(float),
            x_m['oopm_fam'].astype(float),
            x_m['min_pay'].astype(float),
            x_m['max_pay'].astype(float),
            prior_ind_paid_m,
            prior_fam_paid_m,
            x_m['pay'],
            ded_payment_m)

        other_payment_r = adjudicate_line_other(
            x_r['coins'],
            x_r['oopm_mem'].astype(float),
            x_r['oopm_fam'].astype(float),
            x_r['min_pay'].astype(float),
            x_r['max_pay'].astype(float),
            prior_ind_paid_r,
            prior_fam_paid_r,
            x_r['pay'],
            ded_payment_r)

        # Update trackers
        if len(x_m) > 0:
            ind_tracker.loc[x_m['enrolid'], 'allow'] += x_m['pay'].tolist()
            fam_tracker.loc[x_m['efamid'], 'allow'] += x_m['pay'].tolist()

            ind_tracker.loc[x_m['enrolid'],
                            'ind_ded_mx'] += ded_payment_m.tolist()
            fam_tracker.loc[x_m['efamid'],
                            'fam_ded_mx'] += ded_payment_m.tolist()

            ind_tracker.loc[x_m['enrolid'],
                            'ind_paid_mx'] += ded_payment_m.tolist()
            fam_tracker.loc[x_m['efamid'],
                            'fam_paid_mx'] += ded_payment_m.tolist()
            ind_tracker.loc[x_m['enrolid'],
                            'ind_paid_mx'] += other_payment_m.tolist()
            fam_tracker.loc[x_m['efamid'],
                            'fam_paid_mx'] += other_payment_m.tolist()

            if not split_ded:
                ind_tracker.loc[x_m['enrolid'],
                                'ind_ded_rx'] += ded_payment_m.tolist()
                fam_tracker.loc[x_m['efamid'],
                                'fam_ded_rx'] += ded_payment_m.tolist()
            if not split_oopm:
                ind_tracker.loc[x_m['enrolid'],
                                'ind_paid_rx'] += ded_payment_m.tolist()
                fam_tracker.loc[x_m['efamid'],
                                'fam_paid_rx'] += ded_payment_m.tolist()
                ind_tracker.loc[x_m['enrolid'],
                                'ind_paid_rx'] += other_payment_m.tolist()
                fam_tracker.loc[x_m['efamid'],
                                'fam_paid_rx'] += other_payment_m.tolist()

            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'm'), 'member_paid'] += ded_payment_m.tolist()
            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'm'), 'member_paid'] += other_payment_m.tolist()

            ind_fund_pay_m = get_fund_pay(
                ded_payment_m, other_payment_m, ind_tracker.loc[x_m['enrolid'], 'ind_fund'])
            fam_fund_pay_m = get_fund_pay(
                ded_payment_m, other_payment_m, fam_tracker.loc[x_m['efamid'], 'fam_fund'])

            ind_tracker.loc[x_m['enrolid'], 'ind_fund'] -= ind_fund_pay_m
            fam_tracker.loc[x_m['efamid'], 'fam_fund'] -= fam_fund_pay_m

            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'm'), 'fund_paid'] += ind_fund_pay_m.tolist()
            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'm'), 'fund_paid'] += fam_fund_pay_m.tolist()

        if len(x_r) > 0:

            ind_tracker.loc[x_r['enrolid'], 'allow'] += x_r['pay'].tolist()
            fam_tracker.loc[x_r['efamid'], 'allow'] += x_r['pay'].tolist()

            ind_tracker.loc[x_r['enrolid'],
                            'ind_ded_rx'] += ded_payment_r.tolist()
            fam_tracker.loc[x_r['efamid'],
                            'fam_ded_rx'] += ded_payment_r.tolist()

            ind_tracker.loc[x_r['enrolid'],
                            'ind_paid_rx'] += ded_payment_r.tolist()
            fam_tracker.loc[x_r['efamid'],
                            'fam_paid_rx'] += ded_payment_r.tolist()
            ind_tracker.loc[x_r['enrolid'],
                            'ind_paid_rx'] += other_payment_r.tolist()
            fam_tracker.loc[x_r['efamid'],
                            'fam_paid_rx'] += other_payment_r.tolist()

            if not split_ded:
                ind_tracker.loc[x_r['enrolid'],
                                'ind_ded_mx'] += ded_payment_r.tolist()
                fam_tracker.loc[x_r['efamid'],
                                'fam_ded_mx'] += ded_payment_r.tolist()
            if not split_oopm:
                ind_tracker.loc[x_r['enrolid'],
                                'ind_paid_mx'] += ded_payment_r.tolist()
                fam_tracker.loc[x_r['efamid'],
                                'fam_paid_mx'] += ded_payment_r.tolist()
                ind_tracker.loc[x_r['enrolid'],
                                'ind_paid_mx'] += other_payment_r.tolist()
                fam_tracker.loc[x_r['efamid'],
                                'fam_paid_mx'] += other_payment_r.tolist()

            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'r'), 'member_paid'] += ded_payment_r.tolist()
            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'r'), 'member_paid'] += other_payment_r.tolist()

            ind_fund_pay_r = get_fund_pay(
                ded_payment_r, other_payment_r, ind_tracker.loc[x_r['enrolid'], 'ind_fund'])
            fam_fund_pay_r = get_fund_pay(
                ded_payment_r, other_payment_r, fam_tracker.loc[x_r['efamid'], 'fam_fund'])

            ind_tracker.loc[x_r['enrolid'], 'ind_fund'] -= ind_fund_pay_r
            fam_tracker.loc[x_r['efamid'], 'fam_fund'] -= fam_fund_pay_r

            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'r'), 'fund_paid'] += ind_fund_pay_r.tolist()
            claims_df.loc[(claims_df['proc_state'] == 1) & (
                claims_df['med_rx'] == 'r'), 'fund_paid'] += fam_fund_pay_r.tolist()

        del x_m
        del x_r
        # Setup for next loop
        a_prior = len(claims_df.loc[claims_df['proc_state'] == 2])
        claims_df.loc[claims_df['proc_state'] == 1, 'proc_state'] = 2
        claims_df.loc[(claims_df['proc_state'] == 0) & (pd.Series(rotate_list(
            claims_df['proc_state'].tolist())) == 2).tolist(), 'proc_state'] = 1
        a = len(claims_df.loc[claims_df['proc_state'] == 2])
        # to speed up - split off the families with the most claims into the next batch. Min_step = 0 for finishing
        logger.debug('Current Block: %s' % str(a))
        if (a - a_prior) < min_step:
            break
    logger.debug('Current Block: %s' % (str(a)))
    processed_claims_df = claims_df.loc[claims_df['proc_state'] == 2, ]
    remaining_claims_df = claims_df.loc[claims_df['proc_state'] != 2, ]

    return (processed_claims_df, remaining_claims_df, ind_tracker, fam_tracker)

# helper function to update trackers with each round of claims processing


def update_trackers(
        plan,
        output_df,
        remnant,
        type_summary,
        funding_tracker,
        ind_tracker,
        fam_tracker):

    gdf_ind = output_df.loc[output_df['tier'] == 'single'].groupby('cov_fam')
    gdf_fam = output_df.loc[output_df['tier'] == 'family'].groupby('cov_fam')

    type_summary.loc[gdf_ind.groups.keys(),
                     ['pay_ind',
                      'member_paid_ind',
                      'fund_paid_ind']] += gdf_ind['pay',
                                                   'member_paid',
                                                   'fund_paid'].sum().rename(index=str,
                                                                             columns={'pay': 'pay_ind',
                                                                                      'member_paid': 'member_paid_ind',
                                                                                      'fund_paid': 'fund_paid_ind'})
    type_summary.loc[gdf_fam.groups.keys(),
                     ['pay_fam',
                      'member_paid_fam',
                      'fund_paid_fam']] += gdf_fam['pay',
                                                   'member_paid',
                                                   'fund_paid'].sum().rename(index=str,
                                                                             columns={'pay': 'pay_fam',
                                                                                      'member_paid': 'member_paid_fam',
                                                                                      'fund_paid': 'fund_paid_fam'})

    ind_tracker = ind_tracker.loc[remnant['enrolid'].unique()]
    fam_tracker = fam_tracker.loc[remnant['efamid'].unique()]

    funded_fams = set(funding_tracker.index.tolist())
    ind_fams = set(output_df.loc[output_df['tier'] == 'single', 'enrolid'])
    fam_fams = set(output_df.loc[output_df['tier'] == 'family', 'enrolid'])

    ind_fams = ind_fams - funded_fams
    fam_fams = fam_fams - funded_fams

    funding_ind = pd.DataFrame(index=ind_fams, columns=['single', 'family'])
    funding_ind.loc[:, 'single'] = plan.ind_fund
    funding_ind.loc[:, 'family'] = 0

    funding_fam = pd.DataFrame(index=fam_fams, columns=['single', 'family'])
    funding_fam.loc[:, 'single'] = 0
    funding_fam.loc[:, 'family'] = plan.fam_fund

    funding_tracker = pd.concat([funding_tracker, funding_ind, funding_fam])

    return(type_summary, funding_tracker, ind_tracker, fam_tracker)

# Wrapper to run overall adjudication of a plan


def wait_queue_get(queue, queueProcessid):
    logger.info('process queue...%s' % (queueProcessid))
    data = pids_active(queueProcessid)
    while queue.empty():
        logger.info('waiting on queue...')
        data = pids_active(queueProcessid)
        logger.info('Queue Process=%s' % (data))
        time.sleep(1)
    return queue.get()


def adjudicate(
        top_queue,
        block_queue,
        cov_fams,
        plan,
        queue_processId,
        min_step=1000,
        blocksize=100000):
    adj_processId = str(os.getpid())
    logger.info('queue_processid=%s and adjdication_processid=%s ' %
                (queue_processId, adj_processId))
    t0 = time.time()
    type_summary = pd.DataFrame(
        index=cov_fams,
        columns=[
            'pay_ind',
            'member_paid_ind',
            'fund_paid_ind',
            'pay_fam',
            'member_paid_fam',
            'fund_paid_fam'])
    type_summary.loc[:, :] = 0.0
    type_summary = type_summary.astype(float)

    funding_tracker = pd.DataFrame(columns=['single', 'family'])
    funding_tracker = funding_tracker.astype(float)
    logger.info('getting the block')
    block = wait_queue_get(block_queue, queue_processId)
    t1 = time.time()
    logger.info('processing block...')
    claims_df = block_processing_setup(block, plan)
    (output_df,
     remnant,
     ind_tracker,
     fam_tracker) = process_block(claims_df,
                                  min_step=min_step,
                                  ind_fund=plan.ind_fund,
                                  fam_fund=plan.fam_fund,
                                  split_ded=plan.split_ded,
                                  split_oopm=plan.split_oopm)
    (type_summary, funding_tracker, ind_tracker, fam_tracker) = update_trackers(
        plan, output_df, remnant, type_summary, funding_tracker, ind_tracker, fam_tracker)
    t2 = time.time()
    logger.debug('done. sec. elapsed: %s' % str(t2-t1))
    del output_df
    logger.debug('getting the block')
    block = wait_queue_get(block_queue, queue_processId)
    logger.debug('processing block...')
    t1 = time.time()
    while len(block) > 0:
        t1 = time.time()
        claims_df = block_processing_setup(block, plan)
        logger.debug('processing block...')
        (output_df,
         remnant,
         ind_tracker,
         fam_tracker) = process_block(claims_df=claims_df,
                                      remnant_claims_df=remnant,
                                      ind_tracker_prior=ind_tracker,
                                      fam_tracker_prior=fam_tracker,
                                      min_step=min_step,
                                      ind_fund=plan.ind_fund,
                                      fam_fund=plan.fam_fund,
                                      split_ded=plan.split_ded,
                                      split_oopm=plan.split_oopm)
        (type_summary, funding_tracker, ind_tracker, fam_tracker) = update_trackers(
            plan, output_df, remnant, type_summary, funding_tracker, ind_tracker, fam_tracker)
        t2 = time.time()
        logger.debug('done. sec. elapsed: %s' % str(t2-t1))
        del output_df
        block = wait_queue_get(block_queue, queue_processId)

    if len(remnant) > 0:
        (output_df,
         remnant,
         ind_tracker,
         fam_tracker) = process_block(remnant_claims_df=remnant,
                                      ind_tracker_prior=ind_tracker,
                                      fam_tracker_prior=fam_tracker,
                                      min_step=0,
                                      ind_fund=plan.ind_fund,
                                      fam_fund=plan.fam_fund,
                                      split_ded=plan.split_ded,
                                      split_oopm=plan.split_oopm)
        (type_summary, funding_tracker, ind_tracker, fam_tracker) = update_trackers(
            plan, output_df, remnant, type_summary, funding_tracker, ind_tracker, fam_tracker)
        del output_df

    # remaining cash balance
    cash_ind = funding_tracker.sum()['single'] - \
        type_summary.sum()['fund_paid_ind']
    # remaining cash balance
    cash_fam = funding_tracker.sum()['family'] - \
        type_summary.sum()['fund_paid_fam']

    type_summary.loc['CASH000'] = [
        plan.ind_fund,
        0,
        cash_ind,
        plan.fam_fund,
        0,
        cash_fam]  # Allowed represents total funding here

    t_final = time.time()
    logger.info('processid=%s status=finished processing' % (adj_processId))
    logger.info("processId=%s status=finished execution_time(min)=%s" %
                (adj_processId, str((t_final - t0) / 60)))
    top_queue.put(type_summary)
    return

# second wrapper to run overall adjudication of a plan


def run_traditional_plan(
        plan_raw_df,
        cov_fams,
        table,
        blockQueueSize,
        mod=None,
        mod2=None,
        mod2_val=None,
        processid=None):
    plan_global_vals = plan_raw_df.loc[plan_raw_df['global_val']
                                       == plan_raw_df['global_val'], ['item', 'global_val']]
    plan_line_rules = plan_raw_df.loc[plan_raw_df['med_rx'] == plan_raw_df['med_rx'], [
        'item', 'apply_ded', 'not_covered', 'coins', 'min_pay', 'max_pay', 'med_rx']]
    plan = PlanDesign(*plan_global_vals['global_val'].tolist())
    for i in range(len(plan_line_rules.index)):
        plan.add_rule(PlanRule(*plan_line_rules.iloc[i].tolist()))
    if mod:
        if mod2:
            Q = 'SELECT * FROM ' + table + \
                ' WHERE (MOD(efamid::int8, ' + str(mod) + ') = 0 AND MOD(efamid::int8, ' + \
                str(mod2) + ')= ' + str(mod2_val) + ') ORDER BY efamid, dtstart, pay, cov_fam;'
        else:
            Q = 'SELECT * FROM ' + table + \
                ' WHERE MOD(efamid::int8, ' + str(mod) + \
                ') = 0 ORDER BY efamid, dtstart, pay, cov_fam'
    else:
        Q = 'SELECT * FROM ' + table + ' ORDER BY efamid, dtstart, pay, cov_fam'
    logger.info(Q)
    cov_fams = [item[0] for item in cov_fams]
    logger.info('Query: %s' % (Q))
    if processid is None:
        processid = "1"

    top_queue = Queue()
    block_queue = Queue(maxsize=blockQueueSize)
    # constantly loads the queue with blocks
    p1 = Process(target=queue_loader, args=(block_queue, Q))
    p1.start()
    logger.debug('Queue ProcessID=%s' % (p1.pid))
    queueProcessid = p1.pid
    p2 = Process(
        target=adjudicate,
        args=(
            top_queue,
            block_queue,
            cov_fams,
            plan,
            p1.pid))  # runs trad plan loading from the queue
    p2.start()
    logger.debug('Adjudication ProcessID=%s' % (p2.pid))
    p1.join()
    p2.join()

    type_summary = top_queue.get()
    type_summary = type_summary.sort_index()
    not_covered_types = set(
        [i.split(':')[1] for i in plan.rules.loc[plan.rules['not_covered']].index.tolist()])
    not_covered_types = not_covered_types.intersection(set(type_summary.index))
    # member pays 100%, but not counted for accumulators earlier
    type_summary.loc[not_covered_types,
                     'member_paid_ind'] = type_summary.loc[not_covered_types,
                                                           'pay_ind']
    type_summary.loc[not_covered_types,
                     'member_paid_fam'] = type_summary.loc[not_covered_types,
                                                           'pay_fam']

    return type_summary

#######################################
