import math

import pandas as pd
import simpy
from numpy.random._generator import default_rng

from clinic_wf_1ss import get_mammo_1ss
from clinic_wf_no_1ss import get_mammo
from utils import MammoClinic_1SS, MammoClinic


def run_clinic(env, clinic, rg, pt_num_list, acc_pt_num_list, pct_dx_after_ai, ai_on_dict, rad_change, rad_change_2,
               wf_1ss, stoptime=None, max_arrivals=simpy.core.Infinity ):
    # create a counter to keep track of num of pts
    # serve as unique pt id
    patient = 0

    # loop for generating patients
    cur_hour = math.floor(env.now)
    while env.now < stoptime and patient < max_arrivals:

        patient_num_at_current_hour = pt_num_list[cur_hour]
        mean_interarrival_time = 1.0 / patient_num_at_current_hour

        # generate next interarrival time
        iat = rg.exponential(mean_interarrival_time)

        if cur_hour == math.floor(env.now):
            yield env.timeout(iat)

        if env.now > stoptime:
            break

        patient += 1

        if wf_1ss:
            env.process(get_mammo_1ss(env, patient, clinic, rg, pct_dx_after_ai, ai_on_dict, rad_change, rad_change_2))
        else:
            env.process(get_mammo(env, patient, clinic, rg))

        if math.floor(env.now) == cur_hour and patient >= acc_pt_num_list[cur_hour]:
            yield env.timeout(cur_hour+1-env.now)
            cur_hour += 1
        elif math.floor(env.now) > cur_hour and patient >= acc_pt_num_list[cur_hour]:
            cur_hour = math.floor(env.now)

def main(wf_1ss, rad_change, rad_change_2, seed=42, ai_time='none'):
    rg = default_rng(seed=seed)

    stoptime = 9.5

    num_checkin_staff = 3
    num_public_wait_room = 20
    num_consent_staff = 1
    num_change_room = 3
    num_gowned_wait_room = 5
    num_scanner = 3
    num_us_machine = 2
    if wf_1ss:
        num_radiologist = 3
        num_radiologist_same_day = 1
    else:
        num_radiologist = 4

    # ai time
    if ai_time == 'any':
        pct_dx_after_ai = rg.normal(0.12, 0.05)
        ai_on_dict = {7: True, 8: True, 9: True, 10: True, 11: True, 12: True,
                  13: True, 14: True, 15: True, 16: True}
    elif ai_time == "morning":
        pct_dx_after_ai = rg.normal(0.36, 0.15)
        ai_on_dict = {7: False, 8: False, 9: True, 10: True, 11: True, 12: False,
                      13: False, 14: False, 15: False, 16: False}
    elif ai_time == "afternoon":
        pct_dx_after_ai = rg.normal(0.33, 0.12)
        ai_on_dict = {7: False, 8: False, 9: False, 10: False, 11: False, 12: False,
                      13: True, 14: True, 15: True, 16: False}
    elif ai_time == "none": # no 1ss
        pct_dx_after_ai = 0
        ai_on_dict = {7: False, 8: False, 9: False, 10: False, 11: False, 12: False,
                      13: False, 14: False, 15: False, 16: False}

    ### num pts per hour
    num_pt_per_hour = pd.read_csv('./data/num_pt_per_hour_BK_22_12.csv')
    pt_num_list = list(num_pt_per_hour.avg)
    pt_num_list[-1] *= 2

    acc_pt_num_list = []

    curSum = 0
    for num in pt_num_list:
        curSum += num
        acc_pt_num_list.append(curSum)

    env = simpy.Environment()

    if wf_1ss:
        clinic = MammoClinic_1SS(env, num_checkin_staff, num_public_wait_room,
                             num_consent_staff,
                              num_change_room,
                             num_gowned_wait_room,
                             num_scanner, num_us_machine, num_radiologist, num_radiologist_same_day, rad_change, rad_change_2, rg)
        env.process(run_clinic(env, clinic,
                               rg, pt_num_list, acc_pt_num_list, pct_dx_after_ai, ai_on_dict, rad_change, rad_change_2,
                               wf_1ss,
                               stoptime=stoptime))
    else:
        clinic = MammoClinic(env, num_checkin_staff, num_public_wait_room, num_consent_staff,
                             num_change_room, num_gowned_wait_room,
                             num_scanner, num_us_machine, num_radiologist, rg)
        env.process(run_clinic(env, clinic,
                               rg, pt_num_list, acc_pt_num_list, pct_dx_after_ai, ai_on_dict, rad_change, rad_change_2,
                               wf_1ss,
                               stoptime=stoptime))

    env.run()

    # create output files
    clinic_patient_log_df = pd.DataFrame(clinic.timestamps_list)

    if wf_1ss:
        clinic_patient_log_df.to_csv(
            './output/log_1ss/clinic_patient_log_df_seed_' + str(seed) + '.csv', index=False)
    else:
        clinic_patient_log_df.to_csv(
            './output/log_baseline/clinic_patient_log_df_baseline_seed_' + str(
                seed) + '.csv', index=False)

    # Note simulation end time
    end_time = env.now

    print(f"Simulation ended at time {end_time}")

    return (end_time)


