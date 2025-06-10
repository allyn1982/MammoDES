import math
import pandas as pd
from params import exam_type_prob
from utils import MriGuidedBiopsyWorkflow, CheckinStaffHandler, MriOnlyWorkflow, PublicWaitRoomHandler, \
    ScreenUSWorkflow, MammoGuidedBiopsyWorkflow, ChangeRoomHandler, USGuidedBiopsyWorkflow, DxUSWorkflow, \
    DxMammoWorkflow, DxMammoUSWorkflow, ScreenMammoDxUSWorkflow, ScreenMammoDxMammoWorkflow, \
    ScreenMammoDxMammoUSWorkflow, ScreenMammoNoDxWorkflow, GownedWaitRoomHandler, ConsentRoomHandler


class MammographyClinicWorkflow:
    """
    Main class to simulate a mammography clinic workflow for a single patient.
    This class orchestrates the patient's journey through various clinic processes
    based on their assigned exam type.
    """

    def __init__(self, env, patient, clinic, rg, pct_dx_after_ai, ai_on_dict,
                 rad_change=False, rad_change_2=False, enable_1ss=True):
        self.env = env
        self.patient = patient
        self.clinic = clinic
        self.rg = rg
        self.pct_dx_after_ai = pct_dx_after_ai
        self.ai_on_dict = ai_on_dict
        self.rad_change = rad_change
        self.rad_change_2 = rad_change_2
        self.enable_1ss = enable_1ss

    def _calculate_baseline_exam_percentages(self, exam_type_distribution):
        """
        Calculates the cumulative baseline percentages for different exam types
        based on the provided exam_type_distribution.
        This is a private helper method for internal use within the class.

        Args:
            exam_type_distribution (dict_values): The values from the exam type
                                                distribution dictionary.

        Returns:
            tuple: A tuple containing the calculated baseline percentages in order:
                   pct_screen_mammo_scheduled_baseline,
                   pct_dx_mammo_us_scheduled_baseline,
                   pct_dx_mammo_scheduled_baseline,
                   pct_dx_us_scheduled_baseline,
                   pct_us_guided_bx_scheduled_baseline,
                   pct_mammo_guided_bx_scheduled_baseline,
                   pct_screen_us_scheduled_baseline,
                   pct_mri_guided_bx_scheduled_baseline
        """
        exam_values = list(exam_type_distribution)

        pct_screen_mammo_scheduled_baseline = exam_values[0]
        pct_dx_mammo_us_scheduled_baseline = sum(exam_values[:2])
        pct_dx_mammo_scheduled_baseline = sum(exam_values[:3])
        pct_dx_us_scheduled_baseline = sum(exam_values[:4])
        pct_us_guided_bx_scheduled_baseline = sum(exam_values[:5])
        pct_mammo_guided_bx_scheduled_baseline = sum(exam_values[:6])
        pct_screen_us_scheduled_baseline = sum(exam_values[:7])
        pct_mri_guided_bx_scheduled_baseline = sum(exam_values[:8])

        return (pct_screen_mammo_scheduled_baseline,
                pct_dx_mammo_us_scheduled_baseline,
                pct_dx_mammo_scheduled_baseline,
                pct_dx_us_scheduled_baseline,
                pct_us_guided_bx_scheduled_baseline,
                pct_mammo_guided_bx_scheduled_baseline,
                pct_screen_us_scheduled_baseline,
                pct_mri_guided_bx_scheduled_baseline)

    def _calculate_exam_percentages(self, pct_screen_mammo_scheduled_baseline,
                                    pct_dx_mammo_us_scheduled_baseline,
                                    pct_dx_mammo_scheduled_baseline,
                                    pct_dx_us_scheduled_baseline,
                                    pct_us_guided_bx_scheduled_baseline,
                                    pct_mammo_guided_bx_scheduled_baseline,
                                    pct_screen_us_scheduled_baseline,
                                    pct_mri_guided_bx_scheduled_baseline,
                                    ai, exam_type_distribution_values):  # Added exam_type_distribution_values
        """
        Calculates and returns the scheduled exam percentages, applying AI-driven
        adjustments if AI is active.
        """
        # Get individual probabilities from the exam_type_distribution
        # Assumes the order of values corresponds to the order used for baseline cumulative sums.
        individual_baseline_probs = list(exam_type_distribution_values)

        # Initialize a list to hold the individual probabilities for the current scenario (AI or no AI)
        current_scenario_individual_probs = []

        if ai:
            # 1. Probability for 'screen mammo + no dx' (patients passing AI screening)
            prob_screen_mammo_no_ai_referral = pct_screen_mammo_scheduled_baseline * (1 - self.pct_dx_after_ai)
            current_scenario_individual_probs.append(prob_screen_mammo_no_ai_referral)

            # 2. Total probability of patients referred from screen mammo due to AI
            referred_from_screen_by_ai = pct_screen_mammo_scheduled_baseline * self.pct_dx_after_ai

            # 3. Distribute AI referrals into the specific _after_ai_ diagnostic paths
            current_scenario_individual_probs.append(referred_from_screen_by_ai * 0.7)  # AI referred to dx mammo us
            current_scenario_individual_probs.append(referred_from_screen_by_ai * 0.15)  # AI referred to dx mammo
            current_scenario_individual_probs.append(referred_from_screen_by_ai * 0.15)  # AI referred to dx us

            # 4. Add the remaining baseline individual probabilities (from index 1 onwards in original distribution)
            # These are the probabilities for exams that do not originate from screening mammography
            # or are not directly impacted by AI's referral decision from screening.
            # Example: original dx_mammo_us_scheduled (excluding its screen mammo part), biopsies, MRI.
            current_scenario_individual_probs.extend(individual_baseline_probs[1:])

        else:
            # If AI is NOT active, the individual probabilities are simply the baseline individual probabilities
            # (which implicitly sum up to the baseline cumulative percentages).
            current_scenario_individual_probs.extend(individual_baseline_probs)

        # Calculate cumulative sums from the individual probabilities for the current scenario
        # This creates the correct thresholds for the 'number' variable.
        cumulative_sums = [0] * 11  # Initialize with enough zeros, or use a dynamic list.
        # Max 11 types (1 screen no-dx, 3 AI-referred, 7 baseline types)

        # Manually calculate cumulative sums to ensure correct ordering for the return tuple
        # and to match the existing unpacking in run_workflow.

        # Ensure the list has enough elements based on expected returns
        if len(current_scenario_individual_probs) < 11:
            # This indicates an issue if the sum of probabilities doesn't match expected length.
            # This part might need adjustment if new types are added or removed.
            pass  # Will be handled by index errors if list is too short.

        # Calculate the cumulative sums based on the refined individual probabilities list
        cumulative_percentages = []
        current_sum = 0
        for prob in current_scenario_individual_probs:
            current_sum += prob
            cumulative_percentages.append(current_sum)

        # Assign to the return variables, ensuring they match the run_workflow unpacking
        pct_screen_mammo_scheduled = cumulative_percentages[0]
        pct_screen_mammo_after_ai_dx_mammo_us_scheduled = cumulative_percentages[1] if ai else 0
        pct_screen_mammo_after_ai_dx_mammo_scheduled = cumulative_percentages[2] if ai else 0
        pct_screen_mammo_after_ai_us_scheduled = cumulative_percentages[3] if ai else 0

        final_thresholds = {}
        current_sum = 0
        idx = 0

        # Base screen mammo (first segment)
        current_sum += individual_baseline_probs[0] * (1 - self.pct_dx_after_ai) if ai else individual_baseline_probs[0]
        final_thresholds['pct_screen_mammo_scheduled'] = current_sum

        if ai:
            referred_from_screen_by_ai = pct_screen_mammo_scheduled_baseline * self.pct_dx_after_ai

            current_sum += referred_from_screen_by_ai * 0.7
            final_thresholds['pct_screen_mammo_after_ai_dx_mammo_us_scheduled'] = current_sum

            current_sum += referred_from_screen_by_ai * 0.15
            final_thresholds['pct_screen_mammo_after_ai_dx_mammo_scheduled'] = current_sum

            current_sum += referred_from_screen_by_ai * 0.15
            final_thresholds['pct_screen_mammo_after_ai_us_scheduled'] = current_sum

            # Now, add the *remaining* individual baseline probabilities (from index 1 onwards in original distribution)
            # These need to be added cumulatively after the AI-impacted screen segments.
            remaining_baseline_individual_probs = individual_baseline_probs[1:]

            # Map the remaining baseline individual probabilities to their corresponding variables in the final thresholds
            # This order must match the `run_workflow`'s `elif` chain order.

            # This is complex because the variable names like `pct_dx_mammo_us_scheduled` were previously cumulative sums of *individual* baseline probabilities.
            # They need to be re-calculated as cumulative sums from the new `current_sum` onwards.

            # Let's reconsider how the `run_workflow` if/elif chain should operate.
            # It should have a clean set of mutually exclusive cumulative ranges.

            # Let's simplify the return from `_calculate_exam_percentages` to be a single ordered list of thresholds.
            # And modify `run_workflow` to use this list more dynamically.

            # Option A: Return a list of all 11 thresholds if AI, 8 if no AI.
            # This complicates unpacking.

            # Option B (Better): Always return 11 thresholds, with `0` for non-applicable `_after_ai` ones when AI is off.
            # And ensure `pct_dx_mammo_us_scheduled` etc. are properly re-based if AI is ON.

            # Re-attempt `_calculate_exam_percentages` for clearer logic for `pct_dx_mammo_us_scheduled` etc.

            # Initialize all variables to their baseline values
            pct_screen_mammo_scheduled = pct_screen_mammo_scheduled_baseline
            pct_dx_mammo_us_scheduled = pct_dx_mammo_us_scheduled_baseline
            pct_dx_mammo_scheduled = pct_dx_mammo_scheduled_baseline
            pct_dx_us_scheduled = pct_dx_us_scheduled_baseline
            pct_us_guided_bx_scheduled = pct_us_guided_bx_scheduled_baseline
            pct_mammo_guided_bx_scheduled = pct_mammo_guided_bx_scheduled_baseline
            pct_screen_us_scheduled = pct_screen_us_scheduled_baseline
            pct_mri_guided_bx_scheduled = pct_mri_guided_bx_scheduled_baseline

            # AI-specific scheduled percentages (will be populated only if AI is active)
            # These are *additional* percentages from AI referral, not cumulative
            pct_screen_mammo_after_ai_dx_mammo_us_scheduled_added_val = 0
            pct_screen_mammo_after_ai_dx_mammo_scheduled_added_val = 0
            pct_screen_mammo_after_ai_us_scheduled_added_val = 0

            if ai:
                # Screen mammo patients who DO NOT get referred for dx by AI
                pct_screen_mammo_scheduled = pct_screen_mammo_scheduled_baseline * (1 - self.pct_dx_after_ai)

                # Patients referred from screen mammo due to AI
                referred_from_screen_by_ai = pct_screen_mammo_scheduled_baseline * self.pct_dx_after_ai

                # Distribute AI referrals into the specific _after_ai_ diagnostic paths
                pct_screen_mammo_after_ai_dx_mammo_us_scheduled_added_val = referred_from_screen_by_ai * 0.7
                pct_screen_mammo_after_ai_dx_mammo_scheduled_added_val = referred_from_screen_by_ai * 0.15
                pct_screen_mammo_after_ai_us_scheduled_added_val = referred_from_screen_by_ai * 0.15

                # Adjust the *overall* diagnostic percentages (these are cumulative from 0)
                # This is the crucial part. The baseline values already include their original portion.
                # We need to add the *new* AI referrals to these.
                pct_dx_mammo_us_scheduled = pct_dx_mammo_us_scheduled_baseline + pct_screen_mammo_after_ai_dx_mammo_us_scheduled_added_val
                pct_dx_mammo_scheduled = pct_dx_mammo_scheduled_baseline + pct_screen_mammo_after_ai_dx_mammo_scheduled_added_val
                pct_dx_us_scheduled = pct_dx_us_scheduled_baseline + pct_screen_mammo_after_ai_us_scheduled_added_val

                # The remaining original baseline paths (biopsies, screen US, MRI) are assumed to remain consistent,
                # their cumulative thresholds should still be based on original ordering.

                # Now, construct the final cumulative thresholds for the `run_workflow` `if/elif` chain
                # This needs to be carefully ordered to be mutually exclusive.

                # Current cumulative_start will track the lower bound of each next segment.
                cumulative_start = 0

                # 1. Screen mammo (non-AI referred)
                final_pct_screen_mammo_scheduled = pct_screen_mammo_scheduled
                cumulative_start = final_pct_screen_mammo_scheduled

                # 2. screen mammo + dx mammo US (with AI)
                final_pct_screen_mammo_after_ai_dx_mammo_us_scheduled = cumulative_start + pct_screen_mammo_after_ai_dx_mammo_us_scheduled_added_val
                cumulative_start = final_pct_screen_mammo_after_ai_dx_mammo_us_scheduled

                # 3. screen mammo + dx mammo (with AI)
                final_pct_screen_mammo_after_ai_dx_mammo_scheduled = cumulative_start + pct_screen_mammo_after_ai_dx_mammo_scheduled_added_val
                cumulative_start = final_pct_screen_mammo_after_ai_dx_mammo_scheduled

                # 4. screen mammo + dx US (with AI)
                final_pct_screen_mammo_after_ai_us_scheduled = cumulative_start + pct_screen_mammo_after_ai_us_scheduled_added_val
                cumulative_start = final_pct_screen_mammo_after_ai_us_scheduled

                # 5. dx mammo + dx US (original baseline part)
                # Calculate the individual probability for this segment from the baseline (excluding screen mammo baseline)
                individual_prob_dx_mammo_us_baseline = list(exam_type_distribution_values)[1]
                final_pct_dx_mammo_us_scheduled = cumulative_start + individual_prob_dx_mammo_us_baseline
                cumulative_start = final_pct_dx_mammo_us_scheduled

                # 6. dx mammo (original baseline part)
                individual_prob_dx_mammo_baseline = list(exam_type_distribution_values)[2]
                final_pct_dx_mammo_scheduled = cumulative_start + individual_prob_dx_mammo_baseline
                cumulative_start = final_pct_dx_mammo_scheduled

                # 7. dx US (original baseline part)
                individual_prob_dx_us_baseline = list(exam_type_distribution_values)[3]
                final_pct_dx_us_scheduled = cumulative_start + individual_prob_dx_us_baseline
                cumulative_start = final_pct_dx_us_scheduled

                # 8. US-guided bx
                individual_prob_us_guided_bx_baseline = list(exam_type_distribution_values)[4]
                final_pct_us_guided_bx_scheduled = cumulative_start + individual_prob_us_guided_bx_baseline
                cumulative_start = final_pct_us_guided_bx_scheduled

                # 9. mammo-guided bx
                individual_prob_mammo_guided_bx_baseline = list(exam_type_distribution_values)[5]
                final_pct_mammo_guided_bx_scheduled = cumulative_start + individual_prob_mammo_guided_bx_baseline
                cumulative_start = final_pct_mammo_guided_bx_scheduled

                # 10. screen US
                individual_prob_screen_us_baseline = list(exam_type_distribution_values)[6]
                final_pct_screen_us_scheduled = cumulative_start + individual_prob_screen_us_baseline
                cumulative_start = final_pct_screen_us_scheduled

                # 11. mri-guided bx
                individual_prob_mri_guided_bx_baseline = list(exam_type_distribution_values)[7]
                final_pct_mri_guided_bx_scheduled = cumulative_start + individual_prob_mri_guided_bx_baseline
                # cumulative_start = final_pct_mri_guided_bx_scheduled # No need to update if it's the last one used in this method.

                # Now return these 'final_pct' variables.
                # Note: The `run_workflow` expects a tuple of 11 values for dynamic assignment.
                # We need to make sure the order matches exactly.

                return (final_pct_screen_mammo_scheduled,
                        final_pct_screen_mammo_after_ai_dx_mammo_us_scheduled,
                        final_pct_screen_mammo_after_ai_dx_mammo_scheduled,
                        final_pct_screen_mammo_after_ai_us_scheduled,
                        final_pct_dx_mammo_us_scheduled,  # This is the main dx mammo us, now re-based
                        final_pct_dx_mammo_scheduled,  # Main dx mammo, re-based
                        final_pct_dx_us_scheduled,  # Main dx us, re-based
                        final_pct_us_guided_bx_scheduled,
                        final_pct_mammo_guided_bx_scheduled,
                        final_pct_screen_us_scheduled,
                        final_pct_mri_guided_bx_scheduled)

            else:  # ai is False, use direct baseline cumulative percentages
                return (pct_screen_mammo_scheduled_baseline,
                        0,  # These AI-specific thresholds are not applicable
                        0,
                        0,
                        pct_dx_mammo_us_scheduled_baseline,
                        pct_dx_mammo_scheduled_baseline,
                        pct_dx_us_scheduled_baseline,
                        pct_us_guided_bx_scheduled_baseline,
                        pct_mammo_guided_bx_scheduled_baseline,
                        pct_screen_us_scheduled_baseline,
                        pct_mri_guided_bx_scheduled_baseline)

    def run_workflow(self):
        """
        Executes the patient's workflow through the clinic.
        This method determines the patient's exam type and dispatches to the
        appropriate specialized workflow handler.
        """
        # patient arrives to clinic
        arrival_ts = self.env.now

        # generate a random number to determine exam type
        number = self.rg.random()

        # get exam type distribution based on current time
        exam_type_distribution = exam_type_prob(arrival_ts)

        # Retrieve baseline percentages using the new utility function
        (pct_screen_mammo_scheduled_baseline,
         pct_dx_mammo_us_scheduled_baseline,
         pct_dx_mammo_scheduled_baseline,
         pct_dx_us_scheduled_baseline,
         pct_us_guided_bx_scheduled_baseline,
         pct_mammo_guided_bx_scheduled_baseline,
         pct_screen_us_scheduled_baseline,
         pct_mri_guided_bx_scheduled_baseline) = self._calculate_baseline_exam_percentages(
            exam_type_distribution.values())

        ai = self.ai_on_dict[math.floor(arrival_ts) + 7] if self.enable_1ss else False

        # Calculate scheduled percentages using the new helper method
        (pct_screen_mammo_scheduled,
         pct_screen_mammo_after_ai_dx_mammo_us_scheduled,
         pct_screen_mammo_after_ai_dx_mammo_scheduled,
         pct_screen_mammo_after_ai_us_scheduled,
         pct_dx_mammo_us_scheduled,
         pct_dx_mammo_scheduled,
         pct_dx_us_scheduled,
         pct_us_guided_bx_scheduled,
         pct_mammo_guided_bx_scheduled,
         pct_screen_us_scheduled,
         pct_mri_guided_bx_scheduled) = self._calculate_exam_percentages(
            pct_screen_mammo_scheduled_baseline,
            pct_dx_mammo_us_scheduled_baseline,
            pct_dx_mammo_scheduled_baseline,
            pct_dx_us_scheduled_baseline,
            pct_us_guided_bx_scheduled_baseline,
            pct_mammo_guided_bx_scheduled_baseline,
            pct_screen_us_scheduled_baseline,
            pct_mri_guided_bx_scheduled_baseline,
            ai,
            exam_type_distribution.values())  # Pass the full values

        # Initialize all timestamps to pd.NA for this patient instance
        timestamps = {
            'patient_id': self.patient,
            'patient_type': pd.NA,
            'arrival_ts': arrival_ts,
            'got_checkin_staff_ts': pd.NA, 'release_checkin_staff_ts': pd.NA,
            'got_change_room_ts': pd.NA, 'release_change_room_ts': pd.NA,
            'got_public_wait_room_ts': pd.NA, 'release_public_wait_room_ts': pd.NA,
            'got_consent_staff_ts': pd.NA, 'release_consent_staff_ts': pd.NA,
            'got_gowned_wait_room_ts': pd.NA, 'release_gowned_wait_room_ts': pd.NA,
            'got_screen_scanner_ts': pd.NA, 'release_screen_scanner_ts': pd.NA,
            'got_dx_scanner_after_ai_ts': pd.NA, 'release_dx_scanner_after_ai_ts': pd.NA,
            'got_us_machine_after_ai_ts': pd.NA, 'release_us_machine_after_ai_ts': pd.NA,
            'got_dx_scanner_before_us_after_ai_ts': pd.NA, 'release_dx_scanner_before_us_after_ai_ts': pd.NA,
            'got_us_machine_after_dx_scanner_after_ai_ts': pd.NA, 'release_dx_scanner_us_machine_after_ai_ts': pd.NA,
            'begin_ai_assess_ts': pd.NA, 'end_ai_assess_ts': pd.NA,
            'got_dx_scanner_ts': pd.NA, 'release_dx_scanner_ts': pd.NA,
            'got_us_machine_ts': pd.NA, 'release_us_machine_ts': pd.NA,
            'got_dx_scanner_before_us_ts': pd.NA, 'release_dx_scanner_before_us_ts': pd.NA,
            'got_us_machine_after_dx_scanner_ts': pd.NA, 'release_dx_scanner_us_machine_ts': pd.NA,
            'got_us_machine_bx_ts': pd.NA, 'release_us_machine_after_bx_ts': pd.NA,
            'got_scanner_bx_ts': pd.NA,
            'got_scanner_after_us_bx_ts': pd.NA, 'release_scanner_after_post_bx_mammo_ts': pd.NA,
            'got_screen_us_machine_ts': pd.NA, 'release_screen_us_machine_ts': pd.NA,
            'got_scanner_after_mri_bx_ts': pd.NA,
            'got_mri_machine_ts': pd.NA, 'release_mri_machine_ts': pd.NA,
            'got_checkout_change_room_ts': pd.NA, 'release_checkout_change_room_ts': pd.NA,
            'get_rad_dx_mammo_ts': pd.NA, 'release_rad_dx_mammo_ts': pd.NA,
            'get_rad_dx_us_ts': pd.NA, 'release_rad_dx_us_ts': pd.NA,
            'get_rad_dx_mammo_us_mammo_ts': pd.NA, 'release_rad_dx_mammo_us_mammo_ts': pd.NA,
            'get_rad_dx_mammo_us_us_ts': pd.NA, 'release_rad_dx_mammo_us_us_ts': pd.NA,
            'get_rad_us_bx_ts': pd.NA, 'release_rad_us_bx_ts': pd.NA,
            'get_rad_mri_bx_ts': pd.NA, 'release_rad_mri_bx_ts': pd.NA,
            'get_rad_mammo_bx_ts': pd.NA, 'release_rad_mammo_bx_ts': pd.NA,
            'get_rad_dx_mammo_us_mammo_after_ai_ts': pd.NA, 'release_rad_dx_mammo_us_mammo_after_ai_ts': pd.NA,
            'get_rad_dx_mammo_us_us_after_ai_ts': pd.NA, 'release_rad_dx_mammo_us_us_after_ai_ts': pd.NA,
            'get_rad_dx_mammo_after_ai_ts': pd.NA, 'release_rad_dx_mammo_after_ai_ts': pd.NA,
            'get_rad_dx_us_after_ai_ts': pd.NA, 'release_rad_dx_us_after_ai_ts': pd.NA,
            'exit_system_ts': pd.NA
        }

        # Handle common initial steps
        yield self.env.process(CheckinStaffHandler(self.env, self.patient, self.clinic, timestamps).run())

        # Handle MRI workflows (MRI has its own change rooms, so treated separately)
        if number > pct_screen_us_scheduled:
            if pct_screen_us_scheduled < number <= pct_mri_guided_bx_scheduled:
                # 11. mri-guided bx
                workflow_handler = MriGuidedBiopsyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
            elif number > pct_mri_guided_bx_scheduled:
                # Other MRI procedures (currently just sets patient_type)
                workflow_handler = MriOnlyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
        else:
            # Non-MRI workflows (common initial steps)
            yield self.env.process(PublicWaitRoomHandler(self.env, self.patient, self.clinic, timestamps).run())
            yield self.env.process(
                ConsentRoomHandler(self.env, self.patient, self.clinic, timestamps, number, pct_dx_us_scheduled).run())
            yield self.env.process(
                ChangeRoomHandler(self.env, self.patient, self.clinic, timestamps, 'got_change_room_ts',
                                  'release_change_room_ts').run())
            yield self.env.process(GownedWaitRoomHandler(self.env, self.patient, self.clinic, timestamps).run())

            # Dispatch to specific workflow handlers based on exam type
            if number <= pct_screen_mammo_scheduled:
                # 1. screen mammo + no dx
                workflow_handler = ScreenMammoNoDxWorkflow(self.env, self.patient, self.clinic, timestamps,
                                                           self.rad_change)
                yield self.env.process(workflow_handler.run())
            # Changed the conditions to use the correct cumulative thresholds
            elif ai and pct_screen_mammo_scheduled < number <= pct_screen_mammo_after_ai_dx_mammo_us_scheduled:
                # 2. screen mammo + dx mammo US (with AI)
                workflow_handler = ScreenMammoDxMammoUSWorkflow(self.env, self.patient, self.clinic, timestamps,
                                                                self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif ai and pct_screen_mammo_after_ai_dx_mammo_us_scheduled < number <= pct_screen_mammo_after_ai_dx_mammo_scheduled:
                # 3. screen mammo + dx mammo (with AI)
                workflow_handler = ScreenMammoDxMammoWorkflow(self.env, self.patient, self.clinic, timestamps,
                                                              self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif ai and pct_screen_mammo_after_ai_dx_mammo_scheduled < number <= pct_screen_mammo_after_ai_us_scheduled:
                # 4. screen mammo + dx US (with AI)
                workflow_handler = ScreenMammoDxUSWorkflow(self.env, self.patient, self.clinic, timestamps,
                                                           self.rad_change)
                yield self.env.process(workflow_handler.run())
            # These conditions now correctly follow the adjusted cumulative thresholds.
            elif pct_screen_mammo_after_ai_us_scheduled < number <= pct_dx_mammo_us_scheduled:  # Corrected lower bound for AI case
                # 5. dx mammo + dx US
                workflow_handler = DxMammoUSWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change_2)
                yield self.env.process(workflow_handler.run())
            elif pct_dx_mammo_us_scheduled < number <= pct_dx_mammo_scheduled:
                # 6. dx mammo
                workflow_handler = DxMammoWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change_2)
                yield self.env.process(workflow_handler.run())
            elif pct_dx_mammo_scheduled < number <= pct_dx_us_scheduled:
                # 7. dx US
                workflow_handler = DxUSWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change_2)
                yield self.env.process(workflow_handler.run())
            elif pct_dx_us_scheduled < number <= pct_us_guided_bx_scheduled:
                # 8. US-guided bx
                workflow_handler = USGuidedBiopsyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
            elif pct_us_guided_bx_scheduled < number <= pct_mammo_guided_bx_scheduled:
                # 9. mammo-guided bx
                workflow_handler = MammoGuidedBiopsyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
            elif pct_mammo_guided_bx_scheduled < number <= pct_screen_us_scheduled:
                # 10. screen US
                workflow_handler = ScreenUSWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())

            yield self.env.process(
                ChangeRoomHandler(self.env, self.patient, self.clinic, timestamps, 'got_checkout_change_room_ts',
                                  'release_checkout_change_room_ts').run())

        timestamps['exit_system_ts'] = self.env.now
        self.clinic.timestamps_list.append(timestamps)
