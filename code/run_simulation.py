import argparse
import pandas as pd
import random

from utils import compute_durations_1ss, compute_durations_baseline
from run_clinic import main


def run_simulation():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Command line argument parser for various parameters.")

    # Define arguments
    parser.add_argument('--num_iteration', type=int, default=10, help='Number of iterations')
    parser.add_argument('--wf_1ss', type=bool, default=False, help='Whether 1SS is True or False')
    parser.add_argument('--ai_time', type=str, default='none', choices=['morning', 'afternoon', 'any', 'none'], help='Time of day for AI')
    parser.add_argument('--rad_change', type=bool, default=False, help='Dedicate one rad to screen + same day: True or False')
    parser.add_argument('--rad_change_2', type=bool, default=False, help='When rad_change is True, rad_change_2 means dedicate one rad to screen + same day and regular dx: True or False')

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

    if not rad_change and rad_change_2:
        raise ("If rad_change==False, then rad_change_2 must be False. Please change the argument for rad_change_2.")

    if not wf_1ss and rad_change:
        raise ("If wf_1ss==False, then rad_change must be False. Please change the argument for rad_change.")

    if not wf_1ss and ai_time != "none":
        raise ("If wf_1ss==False, ai_time can only be 'none.' Please change the argument for ai_time.")

    count = 0
    seed_list = []
    while count < num_iteration:
        seed = random.randint(1, 1000)
        if seed not in seed_list:
            clinic_end_time = main(wf_1ss, rad_change, rad_change_2, seed=seed, ai_time=ai_time)

            # clinical logs
            if wf_1ss:
                clinic_patient_log_df = pd.read_csv(
                    './output/log_1ss/clinic_patient_log_df_seed_' + str(
                        seed) + '.csv')
                clinic_patient_log_df = compute_durations_1ss(clinic_patient_log_df)
                clinic_patient_log_df.to_csv(
                    './output/log_1ss/clinic_patient_log_df_seed_' + str(
                        seed) + '.csv', index=False)
            else:
                clinic_patient_log_df_baseline = pd.read_csv(
                    './output/log_baseline/clinic_patient_log_df_baseline_seed_' + str(
                        seed) + '.csv')
                clinic_patient_log_df_baseline = compute_durations_baseline(clinic_patient_log_df_baseline)
                clinic_patient_log_df_baseline.to_csv(
                    './output/log_baseline/clinic_patient_log_df_baseline_seed_' + str(
                        seed) + '.csv', index=False)

            count += 1
            seed_list.append(seed)
            print('Simulation', count, 'completed in', clinic_end_time, 'hours.')


if __name__ == "__main__":
    run_simulation()
