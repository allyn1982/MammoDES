import argparse
import pandas as pd
import random
import simpy
import math
from numpy.random._generator import default_rng

from clinic_wf_1ss import MammographyClinicWorkflow
from utils import MammoClinic, compute_durations


def run_clinic(env, clinic, rg, pt_num_list, acc_pt_num_list, pct_dx_after_ai, ai_on_dict,
               rad_change, rad_change_2, wf_1ss, stoptime=None, max_arrivals=simpy.core.Infinity):
    """
    Simulates the patient flow through the mammography clinic.

    Args:
        env (simpy.Environment): The SimPy simulation environment.
        clinic (MammoClinic): The MammoClinic instance with resources.
        rg (numpy.random.Generator): Random number generator.
        pt_num_list (list): List of patient arrival rates per hour.
        acc_pt_num_list (list): Accumulation of patients per hour.
        pct_dx_after_ai (float): Percentage of diagnostic patients after AI assessment.
        ai_on_dict (dict): Dictionary indicating if AI is active for each hour.
        rad_change (bool): If True, a dedicated radiologist for screen + same day is present.
        rad_change_2 (bool): When rad_change is True, this means dedicate one rad to screen + same day and regular dx.
        wf_1ss (bool): True if 1SS (AI-driven workflow) is enabled, False otherwise.
        stoptime (float, optional): Simulation stop time. Defaults to None.
        max_arrivals (int, optional): Maximum number of patients to generate.
                                      Defaults to simpy.core.Infinity.
    """
    patient = 0  # Counter for patients, serves as unique patient ID
    cur_hour = math.floor(env.now)

    # Ensure this function always acts as a generator for SimPy
    yield env.timeout(0)

    # Loop for generating patients
    while env.now < stoptime and patient < max_arrivals:

        patient_num_at_current_hour = pt_num_list[cur_hour]
        mean_interarrival_time = 1.0 / patient_num_at_current_hour

        # Generate next interarrival time
        iat = rg.exponential(mean_interarrival_time)

        if cur_hour == math.floor(env.now):
            yield env.timeout(iat)

        if env.now > stoptime:
            break

        patient += 1

        # The enable_1ss flag is directly from wf_1ss parsed argument
        enable_1SS = wf_1ss

        # Instantiate the workflow for the current patient
        workflow = MammographyClinicWorkflow(env, patient, clinic, rg, pct_dx_after_ai, ai_on_dict,
                                             rad_change=rad_change, rad_change_2=rad_change_2, enable_1ss=enable_1SS)
        env.process(workflow.run_workflow())

        # Adjust current hour based on accumulated patients
        if math.floor(env.now) == cur_hour and patient >= acc_pt_num_list[cur_hour]:
            yield env.timeout(cur_hour + 1 - env.now)
            cur_hour += 1
        elif math.floor(env.now) > cur_hour and patient >= acc_pt_num_list[cur_hour]:
            cur_hour = math.floor(env.now)


def main(wf_1ss, rad_change, rad_change_2, seed=42, ai_time='none'):
    """
    Main function to set up and run the mammography clinic simulation.

    Args:
        wf_1ss (bool): True if 1SS (AI-driven workflow) is enabled, False otherwise.
        rad_change (bool): If True, a dedicated radiologist for screen + same day is present.
        rad_change_2 (bool): When rad_change is True, this means dedicate one rad to screen + same day and regular dx.
        seed (int, optional): Seed for the random number generator. Defaults to 42.
        ai_time (str, optional): Time of day for AI assessment ('morning', 'afternoon', 'any', 'none').
                                 Defaults to 'none'.
    """
    rg = default_rng(seed=seed)

    stoptime = 9.5

    num_checkin_staff = 3
    num_public_wait_room = 20
    num_consent_staff = 1
    num_change_room = 3
    num_gowned_wait_room = 5
    num_scanner = 3
    num_us_machine = 2

    # Determine radiologist numbers based on wf_1ss and rad_change
    if wf_1ss:
        num_radiologist = 3  # Number of general radiologists when 1SS is enabled
        if rad_change:
            num_radiologist_same_day = 1  # Dedicated radiologist for same-day
        else:
            num_radiologist_same_day = 0  # No dedicated same-day rad if rad_change is False
    else:  # Baseline scenario (no 1SS)
        num_radiologist = 4  # Number of general radiologists in baseline
        num_radiologist_same_day = 0  # No dedicated rad in baseline

    # AI time configuration
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
    elif ai_time == "none":  # no 1ss
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

    # Instantiate MammoClinic with updated parameters
    clinic = MammoClinic(
        env,
        num_checkin_staff,
        num_public_wait_room,
        num_consent_staff,
        num_change_room,
        num_gowned_wait_room,
        num_scanner,
        num_us_machine,
        num_radiologist,
        num_radiologist_same_day,
        rad_change,
        rad_change_2,
        rg
    )

    # Run the simulation process
    env.process(run_clinic(env, clinic,
                           rg, pt_num_list, acc_pt_num_list, pct_dx_after_ai, ai_on_dict,
                           rad_change, rad_change_2, wf_1ss,
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


def run_simulation():
    """
    Sets up the argument parser and runs the simulation based on command line arguments.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Command line argument parser for various parameters.")

    # Define arguments
    parser.add_argument('--num_iteration', type=int, default=100, help='Number of iterations')
    parser.add_argument('--wf_1ss', type=bool, default=False, help='Whether 1SS (AI-driven workflow) is True or False')
    parser.add_argument('--ai_time', type=str, default='none', choices=['morning', 'afternoon', 'any', 'none'],
                        help='Time of day for AI assessment to be active')
    parser.add_argument('--rad_change', type=bool, default=False,
                        help='Dedicate one rad to screen + same day: True or False')
    parser.add_argument('--rad_change_2', type=bool, default=False,
                        help='When rad_change is True, rad_change_2 means dedicate one rad to screen + same day and regular dx: True or False')

    # Parse arguments
    args = parser.parse_args()

    # Use parsed arguments
    random.seed(42)
    num_iteration = args.num_iteration
    wf_1ss = args.wf_1ss
    ai_time = args.ai_time
    rad_change = args.rad_change
    rad_change_2 = args.rad_change_2

    print(f'num_iteration: {num_iteration}')
    print(f'wf_1ss: {wf_1ss}')
    print(f'ai_time: {ai_time}')
    print(f'rad_change: {rad_change}')
    print(f'rad_change_2: {rad_change_2}')

    # Validation checks
    if not rad_change and rad_change_2:
        raise ValueError(
            "If rad_change==False, then rad_change_2 must be False. Please change the argument for rad_change_2.")

    if not wf_1ss and rad_change:
        raise ValueError(
            "If wf_1ss==False, then rad_change must be False. A dedicated radiologist for same-day is only relevant with 1SS.")

    if not wf_1ss and ai_time != "none":
        raise ValueError("If wf_1ss==False, ai_time can only be 'none.' Please change the argument for ai_time.")

    count = 0
    seed_list = []
    while count < num_iteration:
        seed = random.randint(1, 1000)
        if seed not in seed_list:
            # Pass all relevant arguments to main, including rad_change_2
            clinic_end_time = main(wf_1ss, rad_change, rad_change_2, seed=seed, ai_time=ai_time)

            # clinical logs
            if wf_1ss:
                clinic_patient_log_df = pd.read_csv(
                    './output/log_1ss/clinic_patient_log_df_seed_' + str(
                        seed) + '.csv')
                clinic_patient_log_df = compute_durations(clinic_patient_log_df)
                clinic_patient_log_df.to_csv(
                    './output/log_1ss/clinic_patient_log_df_seed_' + str(
                        seed) + '.csv', index=False)
            else:
                clinic_patient_log_df_baseline = pd.read_csv(
                    './output/log_baseline/clinic_patient_log_df_baseline_seed_' + str(
                        seed) + '.csv')
                clinic_patient_log_df_baseline = compute_durations(clinic_patient_log_df_baseline)
                clinic_patient_log_df_baseline.to_csv(
                    './output/log_baseline/clinic_patient_log_df_baseline_seed_' + str(
                        seed) + '.csv', index=False)

            count += 1
            seed_list.append(seed)
            print('Simulation', count, 'completed in', clinic_end_time, 'hours.')


if __name__ == "__main__":
    run_simulation()
