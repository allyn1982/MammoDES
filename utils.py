import simpy

class MammoClinic(object):
    def __init__(self, env, num_checkin_staff, num_public_wait_room,
                 num_consent_staff,
                 num_change_room, num_gowned_wait_room,
                 num_scanner, num_us_machine, num_radiologist, rg):
        # simulation env
        self.env = env
        self.rg = rg

        # create list to hold timestamps dictionaries (one per pt)
        self.timestamps_list = []

        # creat resources
        self.checkin_staff = simpy.Resource(env, num_checkin_staff)
        self.public_wait_room = simpy.Resource(env, num_public_wait_room)
        self.consent_staff = simpy.Resource(env, num_consent_staff)
        self.change_room = simpy.Resource(env, num_change_room)
        self.gowned_wait_room = simpy.Resource(env, num_gowned_wait_room)
        self.scanner = simpy.Resource(env, num_scanner)
        self.us_machine = simpy.Resource(env, num_us_machine)
        self.radiologist = simpy.Resource(env, num_radiologist)

    def pt_checkin(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def use_public_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def consent_patient(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def use_change_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.03, 0.006))

    def use_gowned_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.017, 0.0034))

    def get_screen_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def get_dx_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.50-0.083, 0.0834))

    def get_dx_us(self, patient):
        yield self.env.timeout(self.rg.normal(0.50-0.083, 0.0834))

    def get_us_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.75, 0.15))

    def get_mammo_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.75, 0.15))

    def get_screen_us(self, patient):
        yield self.env.timeout(self.rg.normal(0.25, 0.05))

    def get_mri_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.5, 0.1))

    def rad_review(self, patient):
        yield self.env.timeout(self.rg.normal(0.083, 0.017))

class MammoClinic_1SS(object):
    def __init__(self, env, num_checkin_staff, num_public_wait_room, num_consent_staff,
                 num_change_room,
                 num_gowned_wait_room,
                 num_scanner, num_us_machine, num_radiologist, num_radiologist_same_day, rad_change, rad_change_2, rg):
        # simulation env
        self.env = env
        self.rg = rg

        # create list to hold timestamps dictionaries (one per pt)
        self.timestamps_list = []

        # creat resources
        self.checkin_staff = simpy.Resource(env, num_checkin_staff)
        self.public_wait_room = simpy.Resource(env, num_public_wait_room)
        self.consent_staff = simpy.Resource(env, num_consent_staff)
        self.change_room = simpy.Resource(env, num_change_room)
        self.gowned_wait_room = simpy.Resource(env, num_gowned_wait_room)
        self.scanner = simpy.Resource(env, num_scanner)
        self.us_machine = simpy.Resource(env, num_us_machine)
        self.radiologist = simpy.Resource(env, num_radiologist)
        if rad_change or rad_change_2:
            self.radiologist_same_day = simpy.Resource(env, num_radiologist_same_day)

    def pt_checkin(self, patient):
        yield self.env.timeout(self.rg.normal(0.05, 0.01))

    def use_public_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def consent_patient(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def use_change_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.03, 0.006))

    def use_gowned_wait_room(self, patient):
        yield self.env.timeout(self.rg.normal(0.017, 0.0034))

    def get_screen_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.17, 0.034))

    def get_dx_mammo(self, patient):
        yield self.env.timeout(self.rg.normal(0.50-0.083, 0.0834))

    def get_dx_us(self, patient):
        yield self.env.timeout(self.rg.normal(0.50-0.083, 0.0834))

    def get_us_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.75, 0.15))

    def get_mammo_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(1.25, 0.25))

    def get_ai_assess(self, patient):
        yield self.env.timeout(self.rg.normal(0.25, 0.05))

    def get_screen_us(self, patient):
        yield self.env.timeout(self.rg.normal(0.25, 0.05))

    def get_mri_guided_bx(self, patient):
        yield self.env.timeout(self.rg.normal(0.5, 0.1))

    def rad_review(self, patient):
        yield self.env.timeout(self.rg.normal(0.083, 0.017))


def compute_durations_baseline(timestamp_df):
    timestamp_df['wait_for_checkin_staff'] = \
        timestamp_df.loc[:, 'got_checkin_staff_ts'] - timestamp_df.loc[:, 'arrival_ts']
    timestamp_df['wait_for_public_wait_room'] = \
        timestamp_df.loc[:, 'got_public_wait_room_ts'] - timestamp_df.loc[:, 'release_checkin_staff_ts']
    timestamp_df['wait_for_consent_staff_room'] = \
        timestamp_df.loc[:, 'got_consent_staff_ts'] - timestamp_df.loc[:, 'release_public_wait_room_ts']
    timestamp_df['wait_for_change_room'] = \
        timestamp_df.loc[:, 'got_change_room_ts'] - timestamp_df.loc[:, 'release_public_wait_room_ts']
    timestamp_df['wait_for_change_after_consent_room'] = \
        timestamp_df.loc[:, 'got_change_room_ts'] - timestamp_df.loc[:, 'release_consent_staff_ts']
    timestamp_df['wait_for_gowned_wait_room'] = \
        timestamp_df.loc[:, 'got_gowned_wait_room_ts'] - timestamp_df.loc[:, 'release_change_room_ts']
    timestamp_df['wait_for_screen_scanner'] = \
        timestamp_df.loc[:, 'got_screen_scanner_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_dx_scanner'] = \
        timestamp_df.loc[:, 'got_dx_scanner_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_us_machine'] = \
        timestamp_df.loc[:, 'got_us_machine_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_dx_scanner_before_us'] = \
        timestamp_df.loc[:, 'got_dx_scanner_before_us_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_us_machine_after_dx_scanner'] = \
        timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_ts'] - timestamp_df.loc[:, 'release_dx_scanner_before_us_ts']
    timestamp_df['wait_for_us_machine_bx'] = \
        timestamp_df.loc[:, 'got_us_machine_bx_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_scanner_after_us_bx'] = \
        timestamp_df.loc[:, 'got_scanner_after_us_bx_ts'] - timestamp_df.loc[:, 'release_us_machine_after_bx_ts']
    timestamp_df['wait_for_scanner_bx'] = \
        timestamp_df.loc[:, 'got_scanner_bx_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_screen_us_machine_bx'] = \
        timestamp_df.loc[:, 'got_screen_us_machine_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_checkout_change_room_after_screen_mammo'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_screen_scanner_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_mammo'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_us_machine_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_mammo_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_us_machine_ts']
    timestamp_df['wait_for_checkout_change_room_after_bx'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts']
    timestamp_df['time_in_system'] = \
        timestamp_df.loc[:, 'exit_system_ts'] - timestamp_df.loc[:, 'arrival_ts']
    timestamp_df['check_in_time'] = \
        timestamp_df['release_checkin_staff_ts'] - timestamp_df['got_checkin_staff_ts']
    timestamp_df['public_wait_room_time'] = \
        timestamp_df['release_public_wait_room_ts'] - timestamp_df['got_public_wait_room_ts']
    timestamp_df['consent_time'] = \
        timestamp_df['release_consent_staff_ts'] - timestamp_df['got_consent_staff_ts']
    timestamp_df['change_room_time'] = \
        timestamp_df['release_change_room_ts'] - timestamp_df['got_change_room_ts']
    timestamp_df['gowned_wait_room_time'] = \
        timestamp_df['release_gowned_wait_room_ts'] - timestamp_df['got_gowned_wait_room_ts']
    timestamp_df['screen_mammo_time'] = \
        timestamp_df.loc[:, 'release_screen_scanner_ts'] - timestamp_df.loc[:, 'got_screen_scanner_ts']
    timestamp_df['dx_mammo_time'] = \
        timestamp_df.loc[:, 'release_dx_scanner_ts'] - timestamp_df.loc[:, 'got_dx_scanner_ts']
    timestamp_df['dx_us_time'] = \
        timestamp_df.loc[:, 'release_us_machine_ts'] - timestamp_df.loc[:, 'got_us_machine_ts']
    timestamp_df['dx_mammo_us_time_1'] = \
        timestamp_df.loc[:, 'release_dx_scanner_before_us_ts'] - timestamp_df.loc[:, 'got_dx_scanner_before_us_ts']
    timestamp_df['dx_mammo_us_time_2'] = \
        timestamp_df.loc[:, 'release_dx_scanner_us_machine_ts'] - timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_ts']
    timestamp_df['dx_mammo_us_time'] = \
        timestamp_df.loc[:, 'dx_mammo_us_time_1'] + timestamp_df.loc[:, 'dx_mammo_us_time_2']
    timestamp_df['us_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_us_machine_bx_ts']
    timestamp_df['mammo_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_scanner_bx_ts']
    timestamp_df['screen_us_time'] = \
        timestamp_df.loc[:, 'release_screen_us_machine_ts'] - timestamp_df.loc[:, 'got_screen_us_machine_ts']
    timestamp_df['mri_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_mri_machine_ts']
    timestamp_df['checkout_change_room_time'] = \
        timestamp_df['release_checkout_change_room_ts'] - timestamp_df['got_checkout_change_room_ts']

    return timestamp_df

def compute_durations_1ss(timestamp_df):
    timestamp_df['wait_for_checkin_staff'] = \
        timestamp_df.loc[:, 'got_checkin_staff_ts'] - timestamp_df.loc[:, 'arrival_ts']
    timestamp_df['wait_for_public_wait_room'] = \
        timestamp_df.loc[:, 'got_public_wait_room_ts'] - timestamp_df.loc[:, 'release_checkin_staff_ts']
    timestamp_df['wait_for_consent_staff_room'] = \
        timestamp_df.loc[:, 'got_consent_staff_ts'] - timestamp_df.loc[:, 'release_public_wait_room_ts']
    timestamp_df['wait_for_change_room'] = \
        timestamp_df.loc[:, 'got_change_room_ts'] - timestamp_df.loc[:, 'release_public_wait_room_ts']
    timestamp_df['wait_for_change_after_consent_room'] = \
        timestamp_df.loc[:, 'got_change_room_ts'] - timestamp_df.loc[:, 'release_consent_staff_ts']
    timestamp_df['wait_for_gowned_wait_room'] = \
        timestamp_df.loc[:, 'got_gowned_wait_room_ts'] - timestamp_df.loc[:, 'release_change_room_ts']
    ## wait for machines
    timestamp_df['wait_for_screen_scanner'] = \
        timestamp_df.loc[:, 'got_screen_scanner_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_dx_scanner'] = \
        timestamp_df.loc[:, 'got_dx_scanner_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_us_machine'] = \
        timestamp_df.loc[:, 'got_us_machine_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_dx_scanner_before_us'] = \
        timestamp_df.loc[:, 'got_dx_scanner_before_us_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_us_machine_after_dx_scanner'] = \
        timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_ts'] - timestamp_df.loc[:, 'release_dx_scanner_before_us_ts']
    timestamp_df['wait_for_dx_scanner_after_ai'] = \
        timestamp_df.loc[:, 'got_dx_scanner_after_ai_ts'] - timestamp_df.loc[:, 'end_ai_assess_ts']
    timestamp_df['wait_for_us_machine_after_ai'] = \
        timestamp_df.loc[:, 'got_us_machine_after_ai_ts'] - timestamp_df.loc[:, 'end_ai_assess_ts']
    timestamp_df['wait_for_dx_scanner_before_us_ai'] = \
        timestamp_df.loc[:, 'got_dx_scanner_before_us_after_ai_ts'] - timestamp_df.loc[:, 'end_ai_assess_ts']
    timestamp_df['wait_for_us_machine_after_dx_scanner_ai'] = \
        timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_after_ai_ts'] - timestamp_df.loc[:, 'release_dx_scanner_before_us_after_ai_ts']
    timestamp_df['wait_for_us_machine_bx'] = \
        timestamp_df.loc[:, 'got_us_machine_bx_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    timestamp_df['wait_for_scanner_after_us_bx'] = \
        timestamp_df.loc[:, 'got_scanner_after_us_bx_ts'] - timestamp_df.loc[:, 'release_us_machine_after_bx_ts']
    timestamp_df['wait_for_scanner_bx'] = \
        timestamp_df.loc[:, 'got_scanner_bx_ts'] - timestamp_df.loc[:, 'release_gowned_wait_room_ts']
    ## wait for change room after img exam
    timestamp_df['wait_for_checkout_change_room_after_screen_mammo'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'end_ai_assess_ts']
    timestamp_df['wait_for_checkout_change_room_after_screen_mammo_dx_mammo_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_us_machine_after_ai_ts']
    timestamp_df['wait_for_checkout_change_room_after_screen_mammo_dx_mammo'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_after_ai_ts']
    timestamp_df['wait_for_checkout_change_room_after_screen_mammo_dx_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_us_machine_after_ai_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_mammo_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_us_machine_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_mammo'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_dx_scanner_ts']
    timestamp_df['wait_for_checkout_change_room_after_dx_us'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_us_machine_ts']
    timestamp_df['wait_for_checkout_change_room_after_bx'] = \
        timestamp_df.loc[:, 'got_checkout_change_room_ts'] - timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts']
    ## others
    timestamp_df['time_in_system'] = \
        timestamp_df.loc[:, 'exit_system_ts'] - timestamp_df.loc[:, 'arrival_ts']
    timestamp_df['check_in_time'] = \
        timestamp_df['release_checkin_staff_ts'] - timestamp_df['got_checkin_staff_ts']
    timestamp_df['change_room_time'] = \
        timestamp_df['release_change_room_ts'] - timestamp_df['got_change_room_ts']
    timestamp_df['public_wait_room_time'] = \
        timestamp_df['release_public_wait_room_ts'] - timestamp_df['got_public_wait_room_ts']
    timestamp_df['consent_time'] = \
        timestamp_df['release_consent_staff_ts'] - timestamp_df['got_consent_staff_ts']
    timestamp_df['gowned_wait_room_time'] = \
        timestamp_df['release_gowned_wait_room_ts'] - timestamp_df['got_gowned_wait_room_ts']
    timestamp_df['screen_mammo_time'] = \
        timestamp_df.loc[:, 'release_screen_scanner_ts'] - timestamp_df.loc[:, 'got_screen_scanner_ts']
    timestamp_df['dx_mammo_time'] = \
        timestamp_df.loc[:, 'release_dx_scanner_ts'] - timestamp_df.loc[:, 'got_dx_scanner_ts']
    timestamp_df['dx_us_time'] = \
        timestamp_df.loc[:, 'release_us_machine_ts'] - timestamp_df.loc[:, 'got_us_machine_ts']
    timestamp_df['dx_mammo_us_time_1'] = \
        timestamp_df.loc[:, 'release_dx_scanner_before_us_ts'] - timestamp_df.loc[:, 'got_dx_scanner_before_us_ts']
    timestamp_df['dx_mammo_us_time_2'] = \
        timestamp_df.loc[:, 'release_dx_scanner_us_machine_ts'] - timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_ts']
    timestamp_df['dx_mammo_us_time'] = \
        timestamp_df.loc[:, 'dx_mammo_us_time_1'] + timestamp_df.loc[:, 'dx_mammo_us_time_2']
    timestamp_df['dx_mammo_after_ai_time'] = \
        timestamp_df.loc[:, 'release_dx_scanner_after_ai_ts'] - timestamp_df.loc[:, 'got_dx_scanner_after_ai_ts']
    timestamp_df['dx_us_after_ai_time'] = \
        timestamp_df.loc[:, 'release_us_machine_after_ai_ts'] - timestamp_df.loc[:, 'got_us_machine_after_ai_ts']
    timestamp_df['dx_mammo_us_after_ai_time_1'] = \
        timestamp_df.loc[:, 'release_dx_scanner_before_us_after_ai_ts'] - timestamp_df.loc[:, 'got_dx_scanner_before_us_after_ai_ts']
    timestamp_df['dx_mammo_us_after_ai_time_2'] = \
        timestamp_df.loc[:, 'release_dx_scanner_us_machine_after_ai_ts'] - timestamp_df.loc[:, 'got_us_machine_after_dx_scanner_after_ai_ts']
    timestamp_df['dx_mammo_us_after_ai_time'] = \
        timestamp_df.loc[:, 'dx_mammo_us_after_ai_time_1'] - timestamp_df.loc[:,  'dx_mammo_us_after_ai_time_2']
    timestamp_df['us_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_us_machine_bx_ts']
    timestamp_df['mammo_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_scanner_bx_ts']
    timestamp_df['ai_assess_time'] = \
        timestamp_df.loc[:, 'end_ai_assess_ts'] - timestamp_df.loc[:, 'begin_ai_assess_ts']
    timestamp_df['screen_us_time'] = \
        timestamp_df.loc[:, 'release_screen_us_machine_ts'] - timestamp_df.loc[:, 'got_screen_us_machine_ts']
    timestamp_df['mri_guided_bx_time'] = \
        timestamp_df.loc[:, 'release_scanner_after_post_bx_mammo_ts'] - timestamp_df.loc[:, 'got_mri_machine_ts']
    timestamp_df['checkout_change_room_time'] = \
        timestamp_df['release_checkout_change_room_ts'] - timestamp_df['got_checkout_change_room_ts']
    return timestamp_df
