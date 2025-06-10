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

    def run_workflow(self):
        """
        Executes the patient's workflow through the clinic.
        This method determines the patient's exam type and dispatches to the
        appropriate specialized workflow handler.
        """
        # Patient arrives to clinic
        arrival_ts = self.env.now

        # Generate a random number to determine exam type
        number = self.rg.random()

        # Get exam type distribution based on current time
        exam_type_distribution = exam_type_prob(arrival_ts)

        # Calculate exam percentage based on exam type
        pct_screen_mammo_scheduled_baseline = list(exam_type_distribution.values())[0]
        pct_dx_mammo_us_scheduled_baseline = sum(list(exam_type_distribution.values())[:2])
        pct_dx_mammo_scheduled_baseline = sum(list(exam_type_distribution.values())[:3])
        pct_dx_us_scheduled_baseline = sum(list(exam_type_distribution.values())[:4])
        pct_us_guided_bx_scheduled_baseline = sum(list(exam_type_distribution.values())[:5])
        pct_mammo_guided_bx_scheduled_baseline = sum(list(exam_type_distribution.values())[:6])
        pct_screen_us_scheduled_baseline = sum(list(exam_type_distribution.values())[:7])
        pct_mri_guided_bx_scheduled_baseline = sum(list(exam_type_distribution.values())[:8])

        ai = self.ai_on_dict[math.floor(arrival_ts) + 7] if self.enable_1ss else False

        # Set baseline values for all variables
        pct_screen_mammo_scheduled = pct_screen_mammo_scheduled_baseline
        pct_dx_mammo_us_scheduled = pct_dx_mammo_us_scheduled_baseline
        pct_dx_mammo_scheduled = pct_dx_mammo_scheduled_baseline
        pct_dx_us_scheduled = pct_dx_us_scheduled_baseline
        pct_us_guided_bx_scheduled = pct_us_guided_bx_scheduled_baseline
        pct_mammo_guided_bx_scheduled = pct_mammo_guided_bx_scheduled_baseline
        pct_screen_us_scheduled = pct_screen_us_scheduled_baseline
        pct_mri_guided_bx_scheduled = pct_mri_guided_bx_scheduled_baseline
        pct_screen_mammo_after_ai_us_scheduled = pct_screen_mammo_scheduled_baseline

        if ai:
            pct_screen_mammo_scheduled = pct_screen_mammo_scheduled_baseline * (1 - self.pct_dx_after_ai)
            pct_screen_mammo_after_ai_dx_mammo_us_scheduled = (
                    pct_screen_mammo_scheduled +
                    pct_screen_mammo_scheduled_baseline * self.pct_dx_after_ai * 0.7
            )
            pct_screen_mammo_after_ai_dx_mammo_scheduled = (
                    pct_screen_mammo_after_ai_dx_mammo_us_scheduled +
                    pct_screen_mammo_scheduled_baseline * self.pct_dx_after_ai * 0.15
            )

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

        # Handle common steps
        yield self.env.process(CheckinStaffHandler(self.env, self.patient, self.clinic, timestamps).run())

        # Handle MRI workflows (MRI has its own change rooms, so treated separately)
        if number > pct_screen_us_scheduled: # Using the final pct_screen_us_scheduled
            if pct_screen_us_scheduled < number <= pct_mri_guided_bx_scheduled:
                # 11. mri-guided bx
                workflow_handler = MriGuidedBiopsyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
            elif number > pct_mri_guided_bx_scheduled:
                # Other MRI procedures (currently just sets patient_type)
                workflow_handler = MriOnlyWorkflow(self.env, self.patient, self.clinic, timestamps)
                yield self.env.process(workflow_handler.run())
        else:
            # Handle common steps
            yield self.env.process(PublicWaitRoomHandler(self.env, self.patient, self.clinic, timestamps).run())
            yield self.env.process(ConsentRoomHandler(self.env, self.patient, self.clinic, timestamps, number, pct_dx_us_scheduled).run())
            yield self.env.process(ChangeRoomHandler(self.env, self.patient, self.clinic, timestamps, 'got_change_room_ts', 'release_change_room_ts').run())
            yield self.env.process(GownedWaitRoomHandler(self.env, self.patient, self.clinic, timestamps).run())

            # Dispatch to specific workflow handlers based on exam type
            if number <= pct_screen_mammo_scheduled:
                # 1. screen mammo + no dx
                workflow_handler = ScreenMammoNoDxWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif ai and pct_screen_mammo_scheduled < number <= pct_screen_mammo_after_ai_dx_mammo_us_scheduled:
                # 2. screen mammo + dx mammo US (with AI)
                workflow_handler = ScreenMammoDxMammoUSWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif ai and pct_screen_mammo_after_ai_dx_mammo_us_scheduled < number <= pct_screen_mammo_after_ai_dx_mammo_scheduled:
                # 3. screen mammo + dx mammo (with AI)
                workflow_handler = ScreenMammoDxMammoWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif ai and pct_screen_mammo_after_ai_dx_mammo_scheduled < number <= pct_screen_mammo_after_ai_us_scheduled:
                # 4. screen mammo + dx US (with AI)
                workflow_handler = ScreenMammoDxUSWorkflow(self.env, self.patient, self.clinic, timestamps, self.rad_change)
                yield self.env.process(workflow_handler.run())
            elif pct_screen_mammo_after_ai_us_scheduled < number <= pct_dx_mammo_us_scheduled: # Corrected lower bound for AI case
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

            # Handle common steps
            yield self.env.process(ChangeRoomHandler(self.env, self.patient, self.clinic, timestamps, 'got_checkout_change_room_ts', 'release_checkout_change_room_ts').run())

        timestamps['exit_system_ts'] = self.env.now
        self.clinic.timestamps_list.append(timestamps)
