import simpy
import pandas as pd

class MammoClinic(object):
    """
    Represents a Mammography Clinic with various resources and patient interaction methods.
    This class combines functionalities from both MammoClinic and MammoClinic_1SS,
    allowing for a unified simulation environment.
    """
    def __init__(self, env, num_checkin_staff, num_public_wait_room,
                 num_consent_staff, num_change_room, num_gowned_wait_room,
                 num_scanner, num_us_machine, num_radiologist,
                 num_radiologist_same_day, rad_change, rad_change_2, rg): # Added parameters
        # simulation env
        self.env = env
        self.rg = rg # Use the passed random generator

        # create list to hold timestamps dictionaries (one per pt)
        self.timestamps_list = []

        # create resources
        self.checkin_staff = simpy.Resource(env, num_checkin_staff)
        self.public_wait_room = simpy.Resource(env, num_public_wait_room)
        self.consent_staff = simpy.Resource(env, num_consent_staff)
        self.change_room = simpy.Resource(env, num_change_room)
        self.gowned_wait_room = simpy.Resource(env, num_gowned_wait_room)
        self.scanner = simpy.Resource(env, num_scanner)
        self.us_machine = simpy.Resource(env, num_us_machine) # Already lowercase
        self.radiologist = simpy.Resource(env, num_radiologist)

        # Conditional creation of radiologist_same_day based on rad_change/rad_change_2
        if rad_change or rad_change_2:
            self.radiologist_same_day = simpy.Resource(env, num_radiologist_same_day)
        else:
            self.radiologist_same_day = None # Explicitly set to None if not used

    def pt_checkin(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def use_public_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.01, 0.001))

    def consent_patient(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def use_change_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def use_gowned_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.01, 0.001))

    def get_screen_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.1, 0.01))

    def get_dx_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.1, 0.01))

    def get_dx_us(self, patient): # Changed from get_dx_US to get_dx_us
        yield self.env.timeout(self.rg.normal(0.2, 0.05))

    def get_ai_assess(self, patient):
        yield self.env.timeout(self.rg.normal(0.01, 0.001))

    def rad_review(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def get_us_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.5, 0.1))

    def get_mammo_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.5, 0.1))

    def get_screen_us(self, patient):
        yield self.env.timeout(self.rg.normal(0.2, 0.05))

    def get_mri_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(1.0, 0.2))


class BaseWorkflowHandler:
    """
    Base class for all patient workflow handlers.
    Provides common initialization for environment, patient, clinic,
    and a shared timestamps dictionary.
    """
    def __init__(self, env, patient, clinic, timestamps):
        self.env = env
        self.patient = patient
        self.clinic = clinic
        self.timestamps = timestamps

    def run(self):
        """
        Abstract method to be implemented by concrete workflow classes.
        This method will contain the simulation logic for the specific workflow.
        It should be a generator (def) because it will yield SimPy processes.
        """
        raise NotImplementedError("Subclasses must implement 'run' method")


class CheckinStaffHandler(BaseWorkflowHandler):
    """Handles the patient check-in process."""
    def run(self):
        with self.clinic.checkin_staff.request() as request:
            yield request
            self.timestamps['got_checkin_staff_ts'] = self.env.now
            yield self.env.process(self.clinic.pt_checkin(self.patient))
            self.timestamps['release_checkin_staff_ts'] = self.env.now


class PublicWaitRoomHandler(BaseWorkflowHandler):
    """Handles the patient waiting in the public waiting room."""
    def run(self):
        with self.clinic.public_wait_room.request() as request:
            yield request
            self.timestamps['got_public_wait_room_ts'] = self.env.now
            yield self.env.process(self.clinic.use_public_wait_room(self.patient))
            self.timestamps['release_public_wait_room_ts'] = self.env.now


class ConsentRoomHandler(BaseWorkflowHandler):
    """Handles the patient consent process, conditional on exam type."""
    def __init__(self, env, patient, clinic, timestamps, number, pct_dx_us_scheduled): 
        super().__init__(env, patient, clinic, timestamps)
        self.number = number
        self.pct_dx_us_scheduled = pct_dx_us_scheduled

    def run(self):
        if self.number > self.pct_dx_us_scheduled: 
            with self.clinic.consent_staff.request() as request:
                yield request
                self.timestamps['got_consent_staff_ts'] = self.env.now
                yield self.env.process(self.clinic.consent_patient(self.patient))
                self.timestamps['release_consent_staff_ts'] = self.env.now
        else:
            self.timestamps['got_consent_staff_ts'] = pd.NA
            self.timestamps['release_consent_staff_ts'] = pd.NA


class ChangeRoomHandler(BaseWorkflowHandler):
    """
    Handles the patient using a changing room.
    Can be used for initial gowning or post-procedure checkout.
    """
    def __init__(self, env, patient, clinic, timestamps, entry_ts_key, release_ts_key):
        super().__init__(env, patient, clinic, timestamps)
        self.entry_ts_key = entry_ts_key
        self.release_ts_key = release_ts_key

    def run(self):
        with self.clinic.change_room.request() as request:
            yield request
            self.timestamps[self.entry_ts_key] = self.env.now
            yield self.env.process(self.clinic.use_change_room(self.patient))
            self.timestamps[self.release_ts_key] = self.env.now


class GownedWaitRoomHandler(BaseWorkflowHandler):
    """Handles the patient waiting in the gowned waiting room."""
    def run(self):
        with self.clinic.gowned_wait_room.request() as request:
            yield request
            self.timestamps['got_gowned_wait_room_ts'] = self.env.now
            yield self.env.process(self.clinic.use_gowned_wait_room((self.patient)))
            self.timestamps['release_gowned_wait_room_ts'] = self.env.now


class MriGuidedBiopsyWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'mri-guided bx' patient type."""
    def __init__(self, env, patient, clinic, timestamps):
        super().__init__(env, patient, clinic, timestamps)
        self.timestamps['patient_type'] = 'mri-guided bx' # Set patient type here

    def run(self):
        with self.clinic.radiologist.request() as request_rad:
            yield request_rad
            self.timestamps['got_mri_machine_ts'] = self.env.now
            yield self.env.process(self.clinic.get_mri_guided_bx(self.patient))
            self.timestamps['release_mri_machine_ts'] = self.env.now

        # Post-biopsy mammogram
        request = self.clinic.scanner.request()
        yield request
        self.timestamps['got_scanner_after_mri_bx_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))

        # Radiologist review
        request_rad_2 = self.clinic.radiologist.request()
        yield request_rad_2
        self.timestamps['get_rad_mri_bx_ts'] = self.env.now
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.scanner.release(request)
        self.clinic.radiologist.release(request_rad_2)
        self.timestamps['release_rad_mri_bx_ts'] = self.env.now
        self.timestamps['release_scanner_after_post_bx_mammo_ts'] = self.env.now


class MriOnlyWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'mri' patient type without biopsy."""
    def __init__(self, env, patient, clinic, timestamps):
        super().__init__(env, patient, clinic, timestamps)
        self.timestamps['patient_type'] = 'mri' # Set patient type here

    def run(self):
        # Placeholder for MRI-only procedures, if any
        # It's important for a SimPy process to yield at least once.
        yield self.env.timeout(0) # Added to ensure this is always a generator


class ScreenMammoNoDxWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'screen mammo + no dx' patient type."""
    def __init__(self, env, patient, clinic, timestamps, rad_change):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change = rad_change
        self.timestamps['patient_type'] = 'screen'

    def run(self):
        with self.clinic.scanner.request() as request:
            yield request
            self.timestamps['got_screen_scanner_ts'] = self.env.now
            yield self.env.process(self.clinic.get_screen_mammo(self.patient))
            self.timestamps['release_screen_scanner_ts'] = self.env.now

        if self.rad_change:
            request_rad_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_ai = self.clinic.radiologist.request()
        yield request_rad_ai
        self.timestamps['begin_ai_assess_ts'] = self.env.now
        yield self.env.process(self.clinic.get_ai_assess(self.patient))
        self.timestamps['end_ai_assess_ts'] = self.env.now
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_ai)
        else:
            self.clinic.radiologist.release(request_rad_ai)


class ScreenMammoDxMammoUSWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'screen mammo + dx mammo US' patient type with AI."""
    def __init__(self, env, patient, clinic, timestamps, rad_change):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change = rad_change
        self.timestamps['patient_type'] = 'screen + dx mammo US'

    def run(self):
        with self.clinic.scanner.request() as request:
            yield request
            self.timestamps['got_screen_scanner_ts'] = self.env.now
            yield self.env.process(self.clinic.get_screen_mammo(self.patient))
            self.timestamps['release_screen_scanner_ts'] = self.env.now

        if self.rad_change:
            request_rad_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_ai = self.clinic.radiologist.request()
        yield request_rad_ai

        self.timestamps['begin_ai_assess_ts'] = self.env.now
        yield self.env.process(self.clinic.get_ai_assess(self.patient))
        self.timestamps['end_ai_assess_ts'] = self.env.now
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_ai)
        else:
            self.clinic.radiologist.release(request_rad_ai)

        request_2 = self.clinic.scanner.request()
        yield request_2
        self.timestamps['got_dx_scanner_before_us_after_ai_ts'] = self.env.now 
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))

        if self.rad_change:
            request_rad_after_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_after_ai = self.clinic.radiologist.request()
        yield request_rad_after_ai

        self.timestamps['get_rad_dx_mammo_us_mammo_after_ai_ts'] = self.env.now 
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.scanner.release(request_2)
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_after_ai)
        else:
            self.clinic.radiologist.release(request_rad_after_ai)
        self.timestamps['release_dx_scanner_before_us_after_ai_ts'] = self.env.now 
        self.timestamps['release_rad_dx_mammo_us_mammo_after_ai_ts'] = self.env.now 

        request_3 = self.clinic.us_machine.request()
        yield request_3
        self.timestamps['got_us_machine_after_dx_scanner_after_ai_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_us(self.patient)) 
        if self.rad_change:
            request_rad_after_ai_2 = self.clinic.radiologist_same_day.request()
        else:
            request_rad_after_ai_2 = self.clinic.radiologist.request()
        yield request_rad_after_ai_2

        self.timestamps['get_rad_dx_mammo_us_us_after_ai_ts'] = self.env.now 
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.us_machine.release(request_3)
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_after_ai_2)
        else:
            self.clinic.radiologist.release(request_rad_after_ai_2)
        self.timestamps['release_dx_scanner_us_machine_after_ai_ts'] = self.env.now 
        self.timestamps['release_rad_dx_mammo_us_us_after_ai_ts'] = self.env.now 


class ScreenMammoDxMammoWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'screen mammo + dx mammo' patient type with AI."""
    def __init__(self, env, patient, clinic, timestamps, rad_change):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change = rad_change
        self.timestamps['patient_type'] = 'screen + dx mammo'

    def run(self):
        with self.clinic.scanner.request() as request:
            yield request
            self.timestamps['got_screen_scanner_ts'] = self.env.now
            yield self.env.process(self.clinic.get_screen_mammo(self.patient))
            self.timestamps['release_screen_scanner_ts'] = self.env.now

        if self.rad_change:
            request_rad_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_ai = self.clinic.radiologist.request()
        yield request_rad_ai

        self.timestamps['begin_ai_assess_ts'] = self.env.now
        yield self.env.process(self.clinic.get_ai_assess(self.patient))
        self.timestamps['end_ai_assess_ts'] = self.env.now
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_ai)
        else:
            self.clinic.radiologist.release(request_rad_ai)

        request_2 = self.clinic.scanner.request()
        yield request_2
        self.timestamps['got_dx_scanner_after_ai_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))

        if self.rad_change:
            request_rad_after_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_after_ai = self.clinic.radiologist.request()
        yield request_rad_after_ai

        self.timestamps['get_rad_dx_mammo_after_ai_ts'] = self.env.now
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.scanner.release(request_2)
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_after_ai)
        else:
            self.clinic.radiologist.release(request_rad_after_ai)
        self.timestamps['release_rad_dx_mammo_after_ai_ts'] = self.env.now
        self.timestamps['release_dx_scanner_after_ai_ts'] = self.env.now


class ScreenMammoDxUSWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'screen mammo + dx US' patient type with AI."""
    def __init__(self, env, patient, clinic, timestamps, rad_change):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change = rad_change
        self.timestamps['patient_type'] = 'screen + dx US'

    def run(self):
        with self.clinic.scanner.request() as request:
            yield request
            self.timestamps['got_screen_scanner_ts'] = self.env.now
            yield self.env.process(self.clinic.get_screen_mammo(self.patient))
            self.timestamps['release_screen_scanner_ts'] = self.env.now

        if self.rad_change:
            request_rad_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_ai = self.clinic.radiologist.request()
        yield request_rad_ai

        self.timestamps['begin_ai_assess_ts'] = self.env.now
        yield self.env.process(self.clinic.get_ai_assess(self.patient))
        self.timestamps['end_ai_assess_ts'] = self.env.now
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_ai)
        else:
            self.clinic.radiologist.release(request_rad_ai)

        request_2 = self.clinic.us_machine.request()
        yield request_2
        self.timestamps['got_us_machine_after_ai_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_us(self.patient)) 

        if self.rad_change:
            request_rad_after_ai = self.clinic.radiologist_same_day.request()
        else:
            request_rad_after_ai = self.clinic.radiologist.request()
        yield request_rad_after_ai

        self.timestamps['get_rad_dx_us_after_ai_ts'] = self.env.now 
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.us_machine.release(request_2)
        if self.rad_change:
            self.clinic.radiologist_same_day.release(request_rad_after_ai)
        else:
            self.clinic.radiologist.release(request_rad_after_ai)
        self.timestamps['release_rad_dx_us_after_ai_ts'] = self.env.now 
        self.timestamps['release_us_machine_after_ai_ts'] = self.env.now


class DxMammoUSWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'dx mammo + dx US' patient type."""
    def __init__(self, env, patient, clinic, timestamps, rad_change_2):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change_2 = rad_change_2
        self.timestamps['patient_type'] = 'dx mammo US'

    def run(self):
        request = self.clinic.scanner.request()
        yield request
        self.timestamps['got_dx_scanner_before_us_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))

        if self.rad_change_2:
            if self.clinic.radiologist_same_day and self.clinic.radiologist_same_day.count != 0:
                request_rad = self.clinic.radiologist_same_day.request()
                yield request_rad
                self.timestamps['get_rad_dx_mammo_us_mammo_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.scanner.release(request)
                self.clinic.radiologist_same_day.release(request_rad)
            else:
                request_rad = self.clinic.radiologist.request()
                yield request_rad
                self.timestamps['get_rad_dx_mammo_us_mammo_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.scanner.release(request)
                self.clinic.radiologist.release(request_rad)
        else:
            request_rad = self.clinic.radiologist.request()
            yield request_rad
            self.timestamps['get_rad_dx_mammo_us_mammo_ts'] = self.env.now 
            yield self.env.process(self.clinic.rad_review(self.patient))
            self.clinic.scanner.release(request)
            self.clinic.radiologist.release(request_rad)
        self.timestamps['release_rad_dx_mammo_us_mammo_ts'] = self.env.now 
        self.timestamps['release_dx_scanner_before_us_ts'] = self.env.now 

        request_2 = self.clinic.us_machine.request()
        yield request_2
        self.timestamps['got_us_machine_after_dx_scanner_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_us(self.patient)) 

        if self.rad_change_2:
            if self.clinic.radiologist_same_day and self.clinic.radiologist_same_day.count != 0:
                request_rad_3 = self.clinic.radiologist_same_day.request()
                yield request_rad_3
                self.timestamps['get_rad_dx_mammo_us_us_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.us_machine.release(request_2)
                self.clinic.radiologist_same_day.release(request_rad_3)
            else:
                request_rad_4 = self.clinic.radiologist.request()
                yield request_rad_4
                self.timestamps['get_rad_dx_mammo_us_us_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.us_machine.release(request_2)
                self.clinic.radiologist.release(request_rad_4)
        else:
            request_rad_4 = self.clinic.radiologist.request()
            yield request_rad_4
            self.timestamps['get_rad_dx_mammo_us_us_ts'] = self.env.now 
            yield self.env.process(self.clinic.rad_review(self.patient))
            self.clinic.us_machine.release(request_2)
            self.clinic.radiologist.release(request_rad_4)
        self.timestamps['release_rad_dx_mammo_us_us_ts'] = self.env.now
        self.timestamps['release_dx_scanner_us_machine_ts'] = self.env.now 


class DxMammoWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'dx mammo' patient type."""
    def __init__(self, env, patient, clinic, timestamps, rad_change_2):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change_2 = rad_change_2
        self.timestamps['patient_type'] = 'dx mammo'

    def run(self):
        request = self.clinic.scanner.request()
        yield request
        self.timestamps['got_dx_scanner_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))
        if self.rad_change_2:
            if self.clinic.radiologist_same_day and self.clinic.radiologist_same_day.count != 0:
                request_rad = self.clinic.radiologist_same_day.request()
                yield request_rad
                self.timestamps['get_rad_dx_mammo_ts'] = self.env.now
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.scanner.release(request)
                self.clinic.radiologist_same_day.release(request_rad)
            else:
                request_rad_2 = self.clinic.radiologist.request()
                yield request_rad_2
                self.timestamps['get_rad_dx_mammo_ts'] = self.env.now
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.scanner.release(request)
                self.clinic.radiologist.release(request_rad_2)
        else:
            request_rad = self.clinic.radiologist.request()
            yield request_rad
            self.timestamps['get_rad_dx_mammo_ts'] = self.env.now
            yield self.env.process(self.clinic.rad_review(self.patient))
            self.clinic.scanner.release(request)
            self.clinic.radiologist.release(request_rad)
        self.timestamps['release_rad_dx_mammo_ts'] = self.env.now
        self.timestamps['release_dx_scanner_ts'] = self.env.now


class DxUSWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'dx US' patient type."""
    def __init__(self, env, patient, clinic, timestamps, rad_change_2):
        super().__init__(env, patient, clinic, timestamps)
        self.rad_change_2 = rad_change_2
        self.timestamps['patient_type'] = 'dx US'

    def run(self):
        request = self.clinic.us_machine.request()
        yield request
        self.timestamps['got_us_machine_ts'] = self.env.now
        yield self.env.process(self.clinic.get_dx_us(self.patient)) 

        if self.rad_change_2:
            if self.clinic.radiologist_same_day and self.clinic.radiologist_same_day.count != 0:
                request_rad = self.clinic.radiologist_same_day.request()
                yield request_rad
                self.timestamps['get_rad_dx_us_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.us_machine.release(request)
                self.clinic.radiologist_same_day.release(request_rad)
            else:
                request_rad_2 = self.clinic.radiologist.request()
                yield request_rad_2
                self.timestamps['get_rad_dx_us_ts'] = self.env.now 
                yield self.env.process(self.clinic.rad_review(self.patient))
                self.clinic.us_machine.release(request)
                self.clinic.radiologist.release(request_rad_2)
        else:
            request_rad = self.clinic.radiologist.request()
            yield request_rad
            self.timestamps['get_rad_dx_us_ts'] = self.env.now 
            yield self.env.process(self.clinic.rad_review(self.patient))
            self.clinic.us_machine.release(request)
            self.clinic.radiologist.release(request_rad)
        self.timestamps['release_rad_dx_us_ts'] = self.env.now
        self.timestamps['release_us_machine_ts'] = self.env.now


class USGuidedBiopsyWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'US-guided bx' patient type."""
    def __init__(self, env, patient, clinic, timestamps):
        super().__init__(env, patient, clinic, timestamps)
        self.timestamps['patient_type'] = 'US bx'

    def run(self):
        with self.clinic.us_machine.request() as request, self.clinic.radiologist.request() as request_rad:
            yield request & request_rad
            self.timestamps['got_us_machine_bx_ts'] = self.env.now
            self.timestamps['got_scanner_bx_ts'] = pd.NA
            yield self.env.process(self.clinic.get_us_guided_bx(self.patient)) 
            self.timestamps['release_us_machine_after_bx_ts'] = self.env.now

        request_2 = self.clinic.scanner.request()
        yield request_2
        self.timestamps['got_scanner_after_us_bx_ts'] = self.env.now 
        yield self.env.process(self.clinic.get_dx_mammo(self.patient))

        request_rad = self.clinic.radiologist.request()
        self.timestamps['get_rad_us_bx_ts'] = self.env.now 
        yield request_rad
        yield self.env.process(self.clinic.rad_review(self.patient))
        self.clinic.scanner.release(request_2)
        self.clinic.radiologist.release(request_rad)
        self.timestamps['release_rad_us_bx_ts'] = self.env.now 
        self.timestamps['release_scanner_after_post_bx_mammo_ts'] = self.env.now


class MammoGuidedBiopsyWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'mammo-guided bx' patient type."""
    def __init__(self, env, patient, clinic, timestamps):
        super().__init__(env, patient, clinic, timestamps)
        self.timestamps['patient_type'] = 'mammo bx'

    def run(self):
        with self.clinic.scanner.request() as request, self.clinic.radiologist.request() as request_rad:
            yield request & request_rad
            self.timestamps['got_scanner_bx_ts'] = self.env.now
            yield self.env.process(self.clinic.get_mammo_guided_bx(self.patient))
            yield self.env.process(self.clinic.get_dx_mammo(self.patient))
            self.timestamps['get_rad_mammo_bx_ts'] = self.env.now
            yield self.env.process(self.clinic.rad_review(self.patient))
            self.clinic.scanner.release(request)
            self.clinic.radiologist.release(request_rad)
            self.timestamps['release_rad_mammo_bx_ts'] = self.env.now
            self.timestamps['release_scanner_after_post_bx_mammo_ts'] = self.env.now


class ScreenUSWorkflow(BaseWorkflowHandler):
    """Handles the workflow for 'screen US' patient type."""
    def __init__(self, env, patient, clinic, timestamps):
        super().__init__(env, patient, clinic, timestamps)
        self.timestamps['patient_type'] = 'screen US'

    def run(self):
        with self.clinic.us_machine.request() as request:
            yield request
            self.timestamps['got_screen_us_machine_ts'] = self.env.now
            yield self.env.process(self.clinic.get_screen_us(self.patient))
            self.timestamps['release_screen_us_machine_ts'] = self.env.now

def compute_durations(timestamp_df):
    """
    Combines the logic from both compute_durations_baseline and compute_durations_1ss.
    Computes various duration metrics from a DataFrame of timestamps.
    Handles both baseline and 1SS specific columns gracefully by using .get() or checking for existence.
    """
    timestamp_df['checkin_time'] = timestamp_df['release_checkin_staff_ts'] - timestamp_df['got_checkin_staff_ts']
    timestamp_df['public_wait_room_time'] = timestamp_df['release_public_wait_room_ts'] - timestamp_df['got_public_wait_room_ts']
    timestamp_df['consent_time'] = timestamp_df['release_consent_staff_ts'] - timestamp_df['got_consent_staff_ts']
    timestamp_df['change_room_time'] = timestamp_df['release_change_room_ts'] - timestamp_df['got_change_room_ts']
    timestamp_df['gowned_wait_room_time'] = timestamp_df['release_gowned_wait_room_ts'] - timestamp_df['got_gowned_wait_room_ts']
    timestamp_df['screen_mammo_time'] = timestamp_df['release_screen_scanner_ts'] - timestamp_df['got_screen_scanner_ts']

    # AI specific durations (will be NA if 1SS is not active)
    timestamp_df['ai_assess_time'] = timestamp_df['end_ai_assess_ts'] - timestamp_df['begin_ai_assess_ts']

    # Diagnostic pathways, handling both 1SS and baseline names
    timestamp_df['dx_mammo_time'] = timestamp_df['release_dx_scanner_ts'] - timestamp_df['got_dx_scanner_ts']
    timestamp_df['dx_us_time'] = timestamp_df['release_us_machine_ts'] - timestamp_df['got_us_machine_ts']

    timestamp_df['dx_mammo_us_time_1'] = timestamp_df['release_dx_scanner_before_us_ts'] - timestamp_df['got_dx_scanner_before_us_ts']
    timestamp_df['dx_mammo_us_time_2'] = timestamp_df['release_dx_scanner_us_machine_ts'] - timestamp_df['got_us_machine_after_dx_scanner_ts']
    timestamp_df['dx_mammo_us_time'] = timestamp_df['dx_mammo_us_time_1'] + timestamp_df['dx_mammo_us_time_2']

    # 1SS specific diagnostic times
    timestamp_df['dx_mammo_after_ai_time'] = timestamp_df['release_dx_scanner_after_ai_ts'] - timestamp_df['got_dx_scanner_after_ai_ts']
    timestamp_df['dx_us_after_ai_time'] = timestamp_df['release_us_machine_after_ai_ts'] - timestamp_df['got_us_machine_after_ai_ts']

    timestamp_df['dx_mammo_us_after_ai_time_1'] = timestamp_df['release_dx_scanner_before_us_after_ai_ts'] - timestamp_df['got_dx_scanner_before_us_after_ai_ts']
    timestamp_df['dx_mammo_us_after_ai_time_2'] = timestamp_df['release_dx_scanner_us_machine_after_ai_ts'] - timestamp_df['got_us_machine_after_dx_scanner_after_ai_ts']
    timestamp_df['dx_mammo_us_after_ai_time'] = timestamp_df['dx_mammo_us_after_ai_time_1'] + timestamp_df['dx_mammo_us_after_ai_time_2']


    timestamp_df['us_guided_bx_time'] = timestamp_df['release_us_machine_after_bx_ts'] - timestamp_df['got_us_machine_bx_ts']
    timestamp_df['mammo_guided_bx_time'] = timestamp_df['release_scanner_after_post_bx_mammo_ts'] - timestamp_df['got_scanner_bx_ts']
    timestamp_df['mri_guided_bx_time'] = timestamp_df['release_mri_machine_ts'] - timestamp_df['got_mri_machine_ts']

    timestamp_df['screen_us_time'] = timestamp_df['release_screen_us_machine_ts'] - timestamp_df['got_screen_us_machine_ts']

    timestamp_df['checkout_change_room_time'] = timestamp_df['release_checkout_change_room_ts'] - timestamp_df['got_checkout_change_room_ts']

    # Radiologist review times (can be associated with different dx types or 1SS)
    timestamp_df['rad_dx_mammo_time'] = timestamp_df['release_rad_dx_mammo_ts'] - timestamp_df['get_rad_dx_mammo_ts']
    timestamp_df['rad_dx_us_time'] = timestamp_df['release_rad_dx_us_ts'] - timestamp_df['get_rad_dx_us_ts']
    timestamp_df['rad_dx_mammo_us_mammo_time'] = timestamp_df['release_rad_dx_mammo_us_mammo_ts'] - timestamp_df['get_rad_dx_mammo_us_mammo_ts']
    timestamp_df['rad_dx_mammo_us_us_time'] = timestamp_df['release_rad_dx_mammo_us_us_ts'] - timestamp_df['get_rad_dx_mammo_us_us_ts']

    # 1SS specific rad review times
    timestamp_df['rad_dx_mammo_us_mammo_after_ai_time'] = timestamp_df['release_rad_dx_mammo_us_mammo_after_ai_ts'] - timestamp_df['get_rad_dx_mammo_us_mammo_after_ai_ts']
    timestamp_df['rad_dx_mammo_us_us_after_ai_time'] = timestamp_df['release_rad_dx_mammo_us_us_after_ai_ts'] - timestamp_df['get_rad_dx_mammo_us_us_after_ai_ts']
    timestamp_df['rad_dx_mammo_after_ai_time'] = timestamp_df['release_rad_dx_mammo_after_ai_ts'] - timestamp_df['get_rad_dx_mammo_after_ai_ts']
    timestamp_df['rad_dx_us_after_ai_time'] = timestamp_df['release_rad_dx_us_after_ai_ts'] - timestamp_df['get_rad_dx_us_after_ai_ts']

    timestamp_df['rad_us_bx_time'] = timestamp_df['release_rad_us_bx_ts'] - timestamp_df['get_rad_us_bx_ts']
    timestamp_df['rad_mammo_bx_time'] = timestamp_df['release_rad_mammo_bx_ts'] - timestamp_df['get_rad_mammo_bx_ts']
    timestamp_df['rad_mri_bx_time'] = timestamp_df['release_rad_mri_bx_ts'] - timestamp_df['get_rad_mri_bx_ts']

    timestamp_df['total_system_time'] = timestamp_df['exit_system_ts'] - timestamp_df['arrival_ts']

    return timestamp_df
