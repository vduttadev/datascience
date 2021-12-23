import pandas as pd
import datetime


def get_date(t):
    return datetime.datetime.strptime(t, '%Y-%m-%d')


def get_kafka_plan_global_stats(plan_dict, eff_trend):
    global_stats = {
        k: plan_dict[k] for k in (
            'opportunityId',
            'benefitPlanId',
            'planName')}
    global_stats['ind_ded'] = plan_dict['fundingDetails']['deductible']['individualAmount']
    global_stats['fam_ded'] = plan_dict['fundingDetails']['deductible']['familyAmount']

    global_stats['ind_oopm'] = plan_dict['fundingDetails']['outOfPocketMaximum']['individualAmount']
    global_stats['fam_oopm'] = plan_dict['fundingDetails']['outOfPocketMaximum']['familyAmount']

    global_stats['funding_ind'] = plan_dict['fundingDetails']['employerAccountFunding']['individualAmount']
    global_stats['funding_fam'] = plan_dict['fundingDetails']['employerAccountFunding']['familyAmount']

    if plan_dict['deductibleProvisionType']['code'] == 'EMBEDDED':
        global_stats['tf_ded_flag'] = 0
    else:
        global_stats['tf_ded_flag'] = 1

    if plan_dict['outOfPocketProvisionType']['code'] == 'EMBEDDED':
        global_stats['tf_oopm_flag'] = 0
    else:
        global_stats['tf_oopm_flag'] = 1

    if plan_dict['separateRxDeductible']:
        global_stats['split_rx_ded'] = 1
        global_stats['rx_ind_ded'] = plan_dict['fundingDetails']['rxDeductible']['individualAmount']
        if plan_dict['rxDeductiblePerMember']:
            # only the member deductible is effective
            global_stats['rx_fam_ded'] = 999999
        else:
            global_stats['rx_fam_ded'] = plan_dict['fundingDetails']['rxDeductible']['familyAmount']
    else:
        global_stats['split_rx_ded'] = 0
        global_stats['rx_ind_ded'] = 0
        global_stats['rx_fam_ded'] = 0

    if plan_dict['separateRxOutOfPocketMax']:
        global_stats['split_rx_oopm'] = 1
        global_stats['ind_oopm_rx'] = plan_dict['fundingDetails']['rxOutOfPocketMaximum']['individualAmount']
        global_stats['fam_oopm_rx'] = plan_dict['fundingDetails']['rxOutOfPocketMaximum']['familyAmount']
    else:
        global_stats['split_rx_oopm'] = 0
        global_stats['ind_oopm_rx'] = 0
        global_stats['fam_oopm_rx'] = 0

    global_stats['trend'] = eff_trend

    return global_stats


def generate_plan_line(
        item,
        apply_ded,
        not_covered=False,
        coins=0,
        min_pay=0,
        max_pay=999999,
        med_rx='m'):
    df = pd.DataFrame([[apply_ded, not_covered, coins, min_pay, max_pay, med_rx]], index=[
                      item], columns=['apply_ded', 'not_covered', 'coins', 'min_pay', 'max_pay', 'med_rx'])
    return df


def none_to_zero(x):
    if x is None:
        y = 0
    else:
        y = float(x)
    return y


def get_user_defined_lines(dict_list, cov_fam_mapping, general_coins, m_r_ind):
    df = pd.DataFrame(
        columns=[
            'apply_ded',
            'not_covered',
            'coins',
            'min_pay',
            'max_pay',
            'med_rx'])
    for line_dict in dict_list:
        item = cov_fam_mapping[line_dict['treatmentTypeCode']['code']]
        cov_type = line_dict['coverageType']['code']
        if cov_type == 'COPAY_ONLY':
            df = df.append(
                generate_plan_line(
                    item,
                    False,
                    False,
                    0,
                    line_dict['copay'],
                    line_dict['copay'],
                    m_r_ind))
        elif cov_type == 'DEDUCTIBLE':
            df = df.append(
                generate_plan_line(
                    item,
                    True,
                    False,
                    0,
                    0,
                    999999,
                    m_r_ind))
        elif cov_type == 'COPAY_THEN_COINSURANCE':
            df = df.append(
                generate_plan_line(
                    item,
                    False,
                    False,
                    general_coins,
                    line_dict['copay'],
                    999999,
                    m_r_ind))
        elif cov_type == 'DEDUCTIBLE_THEN_COINSURANCE':
            df = df.append(
                generate_plan_line(
                    item,
                    True,
                    False,
                    general_coins,
                    0,
                    999999,
                    m_r_ind))
        elif cov_type == 'NOT_COVERED':
            df = df.append(
                generate_plan_line(
                    item,
                    False,
                    True,
                    1,
                    0,
                    999999,
                    m_r_ind))
        elif cov_type == 'COVERED_FULL':
            df = df.append(
                generate_plan_line(
                    item,
                    False,
                    False,
                    0,
                    0,
                    0,
                    m_r_ind))
        elif cov_type == 'OTHER':
            copay = none_to_zero(line_dict['copay'])
            coins = none_to_zero(line_dict['coinsurance'])
            min_coins = none_to_zero(line_dict['coinsuranceMin'])
            max_coins = none_to_zero(line_dict['coinsuranceMax'])

            min_pay = copay + min_coins
            if coins != 0 and max_coins == 0:
                max_pay = 999999
            else:
                max_pay = copay + max_coins

            df = df.append(
                generate_plan_line(
                    item,
                    line_dict['subjectToDeductible'],
                    False,
                    coins,
                    min_pay,
                    max_pay,
                    m_r_ind))
    return df


def get_faux_cov_fam_mapping():
    mapping = {
        'Z000100': 'XX00001',
        'Z000200': 'XX00002',
        'Z000400': 'XX00016',
        'Z000500': 'SMRT004',
        'Z001000': 'XX00003',
        'Z001100': 'XX00006',
        'Z001300': 'XX00008',
        'Z001401': 'XX00005',
        'Z000801': 'Rx30001',
        'Z000802': 'Rx30002',
        'Z000803': 'Rx30003',
        'Z000905': 'Rx30SP2',
        'Z000x00': 'XX00000'}
    return mapping


# Return list of mappings of form [from, to, multiple]
def get_related_cov_fams():
    relations = [
        [
            'Rx30SP2', 'Rx30SP1', 1], [
            'Rx30SP2', 'Rx30SP3', 1], [
                'Rx30001', 'Rx90001', 2], [
                    'Rx30002', 'Rx90002', 2], [
                        'Rx30003', 'Rx90003', 2], [
                            'Rx30SP1', 'Rx90SP1', 2], [
                                'Rx30SP2', 'Rx90SP2', 2], [
                                    'Rx30SP3', 'Rx90SP3', 2], [
                                        'XX00002', 'XX00004', 1], [
                                            'XX00001', 'XX00009', 1], [
                                                'XX00001', 'XX00011', 1], [
                                                    'XX00016', 'XX00017', 1], [
                                                        'XX00002', 'SMRT001', 1], [
                                                            'XX00003', 'SMRT002', 1], [
                                                                'XX00005', 'SMRT003', 1], [
                                                                    'XX00016', 'XX00010', 1]]
    return relations


def append_related_line(base_df, base_cov_fam, new_cov_fam, multiple=1):
    new_line = base_df.loc[[base_cov_fam]]
    new_line.loc[:, 'min_pay'] = new_line.loc[:, 'min_pay'] * multiple
    new_line.loc[:, 'max_pay'] = new_line.loc[:, 'max_pay'] * multiple
    new_line = new_line.set_index([[new_cov_fam]])
    df = base_df.append(new_line)
    return df


def get_med_rx_ind(t):
    if t[0:2] == 'Rx' or t == 'NC     ':
        m_r_ind = 'r'
    else:
        m_r_ind = 'm'
    return m_r_ind


def get_fixed_lines(general_coins):
    df = pd.DataFrame(
        columns=[
            'apply_ded',
            'not_covered',
            'coins',
            'min_pay',
            'max_pay',
            'med_rx'])
    free_list = ['Rx00000', 'XX00000']
    ded_coins_list = [
        'XX00007',
        'UNKNOWN',
        'DME0001',
        'DME0002',
        'DME0003',
        'DME0004',
        'DME0005',
        'DME0006',
        'DME0007',
        'DME0008',
        'DME0009',
        'DME0010',
        'DME0011',
        'DME0012',
        'DMER001',
        'DMER002',
        'DMER003',
        'DMER004',
        'DMER005',
        'DMER006',
        'DMER007',
        'DMER008',
        'DMER009',
        'DMER010',
        'DMER011',
        'DMER012']
    no_cov_list = ['NC     ', 'XX00012', 'XX00013', 'XX00014', 'XX00015']
    for item in free_list:
        m_r_ind = get_med_rx_ind(item)
        df = df.append(
            generate_plan_line(
                item,
                False,
                False,
                0,
                0,
                0,
                m_r_ind))
    for item in ded_coins_list:
        m_r_ind = get_med_rx_ind(item)
        df = df.append(
            generate_plan_line(
                item,
                True,
                False,
                general_coins,
                0,
                999999,
                m_r_ind))
    for item in no_cov_list:
        m_r_ind = get_med_rx_ind(item)
        df = df.append(
            generate_plan_line(
                item,
                False,
                True,
                1,
                0,
                999999,
                m_r_ind))

    return df


def get_kafka_plan_lines(plan_dict):

    med_dict = plan_dict['medicalCopays']
    rx_dict = plan_dict['rxCopays']
    general_coins = plan_dict['generalCoinsurance'] / 100

    med_df = get_user_defined_lines(
        med_dict,
        get_faux_cov_fam_mapping(),
        general_coins,
        'm')
    rx_df = get_user_defined_lines(
        rx_dict,
        get_faux_cov_fam_mapping(),
        general_coins,
        'r')

    df = pd.concat([med_df, rx_df, get_fixed_lines(general_coins)])
    related_fams = get_related_cov_fams()
    for triplet in related_fams:
        df = append_related_line(df, triplet[0], triplet[1], triplet[2])

    df.index.name = 'item'
    return df.sort_index()


def JSON_to_single_kafka_plan_df(
        j,
        truven_dtstart='2017-01-01',
        truven_dtend='2017-12-31',
        trend=0.06):
    plan_list = j['currentPlans']
    plan_dict = plan_list[0]  # initial kafka JSON will have only one trad plan

    exp_dtstart = get_date(truven_dtstart)
    exp_dtend = get_date(truven_dtend)
    exp_dtmid = exp_dtstart + (exp_dtend - exp_dtstart) / 2

    proj_dtstart = get_date(j['desiredBindEffectiveDate'])
    proj_dtend = get_date(j['desiredBindEndDate'])
    proj_dtmid = proj_dtstart + (proj_dtend - proj_dtstart) / 2

    eff_trend = (1 + trend)**((proj_dtmid - exp_dtmid).days / 365)

    plan_df = get_kafka_plan_lines(plan_dict)
    plan_df = plan_df.assign(global_val=None)

    global_vals = pd.DataFrame.from_dict(
        get_kafka_plan_global_stats(
            plan_dict,
            eff_trend),
        orient='index',
        columns=['global_val'])
    global_vals.index.name = 'item'
    global_vals = global_vals.reindex(
        index=[
            'opportunityId',
            'benefitPlanId',
            'planName',
            'ind_ded',
            'fam_ded',
            'rx_ind_ded',
            'rx_fam_ded',
            'ind_oopm',
            'fam_oopm',
            'ind_oopm_rx',
            'fam_oopm_rx',
            'funding_ind',
            'funding_fam',
            'tf_ded_flag',
            'tf_oopm_flag',
            'split_rx_ded',
            'split_rx_oopm',
            'trend'])
    return pd.concat([global_vals, plan_df], sort=False)
