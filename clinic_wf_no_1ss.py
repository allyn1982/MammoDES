import math
import random
import pandas as pd
from numpy.random import default_rng
import simpy
from utils import MammoClinic, compute_durations_baseline
from params import exam_type_prob


def get_mammo(env, patient, clinic, rg):
    # patient arrives to clinic
    arrival_ts = env.now

    # generate a random number
    number = rg.random()

    # get exam type distribution based on current time
    exam_type_distribution = exam_type_prob(arrival_ts)

    pct_screen_mammo_scheduled = list(exam_type_distribution.values())[0]
    pct_dx_mammo_us_scheduled = sum(list(exam_type_distribution.values())[:2])
    pct_dx_mammo_scheduled = sum(list(exam_type_distribution.values())[:3])
    pct_dx_us_scheduled = sum(list(exam_type_distribution.values())[:4])
    pct_us_guided_bx_scheduled = sum(list(exam_type_distribution.values())[:5])
    pct_mammo_guided_bx_scheduled = sum(list(exam_type_distribution.values())[:6])
    pct_screen_us_scheduled = sum(list(exam_type_distribution.values())[:7])
    pct_mri_guided_bx_scheduled = sum(list(exam_type_distribution.values())[:8])

    # initiatie timestamps
    got_screen_us_machine_ts = pd.NA
    got_screen_scanner_ts, got_dx_scanner_ts, got_us_machine_ts, got_us_machine_after_dx_scanner_ts = pd.NA, pd.NA, pd.NA, pd.NA
    got_us_machine_bx_ts, got_scanner_after_us_bx_ts = pd.NA, pd.NA
    got_dx_scanner_before_us_ts, got_scanner_bx_ts = pd.NA, pd.NA
    got_scanner_after_mri_bx_ts = pd.NA
    got_mri_machine_ts = pd.NA

    release_screen_us_machine_ts = pd.NA
    release_scanner_after_post_bx_mammo_ts = pd.NA
    release_dx_scanner_ts, release_us_machine_ts, release_dx_scanner_us_machine_ts, release_screen_scanner_ts = pd.NA, pd.NA, pd.NA, pd.NA
    release_us_machine_after_bx_ts = pd.NA
    release_dx_scanner_before_us_ts = pd.NA
    release_mri_machine_ts = pd.NA

    got_public_wait_room_ts, release_public_wait_room_ts = pd.NA, pd.NA
    got_consent_staff_ts, release_consent_staff_ts = pd.NA, pd.NA
    got_change_room_ts, release_change_room_ts = pd.NA, pd.NA
    got_gowned_wait_room_ts, release_gowned_wait_room_ts = pd.NA, pd.NA
    got_checkout_change_room_ts, release_checkout_change_room_ts = pd.NA, pd.NA

    get_rad_dx_mammo_ts, release_rad_dx_mammo_ts = pd.NA, pd.NA
    get_rad_dx_us_ts, release_rad_dx_us_ts = pd.NA, pd.NA
    get_rad_dx_mammo_us_mammo_ts, release_rad_dx_mammo_us_mammo_ts = pd.NA, pd.NA
    get_rad_dx_mammo_us_us_ts, release_rad_dx_mammo_us_us_ts = pd.NA, pd.NA
    get_rad_us_bx_ts, release_rad_us_bx_ts = pd.NA, pd.NA
    get_rad_mri_bx_ts, release_rad_mri_bx_ts = pd.NA, pd.NA
    get_rad_mammo_bx_ts, release_rad_mammo_bx_ts = pd.NA, pd.NA

    # request a checkin staff
    with clinic.checkin_staff.request() as request:
        yield request
        got_checkin_staff_ts = env.now
        yield env.process(clinic.pt_checkin(patient))
        release_checkin_staff_ts = env.now

    # mri has own change rooms
    if number > pct_screen_us_scheduled:
        # 8. mri-guided bx
        if pct_screen_us_scheduled < number <= pct_mri_guided_bx_scheduled:
            patient_type = 'mri-guided bx'

            with clinic.radiologist.request() as request_rad:
                yield request_rad
                got_mri_machine_ts = env.now
                yield env.process(clinic.get_mri_guided_bx(patient))
                release_mri_machine_ts = env.now

            # post bx mammo
            request = clinic.scanner.request()
            yield request
            got_scanner_after_mri_bx_ts = env.now
            yield env.process(clinic.get_dx_mammo(patient))

            # rad review
            request_rad = clinic.radiologist.request()
            get_rad_mri_bx_ts = env.now
            yield request_rad
            yield env.process(clinic.rad_review(patient))
            clinic.scanner.release(request)
            clinic.radiologist.release(request_rad)
            release_rad_mri_bx_ts = env.now
            release_scanner_after_post_bx_mammo_ts = env.now

        # 9. Other mri procedures
        if number > pct_mri_guided_bx_scheduled:
            patient_type = 'mri'

    else:
        # request a public wait room
        with clinic.public_wait_room.request() as request:
            yield request
            got_public_wait_room_ts = env.now
            yield env.process(clinic.use_public_wait_room(patient))
            release_public_wait_room_ts = env.now

        # request consent room (bx only)
        if number > pct_dx_us_scheduled:
            with clinic.consent_staff.request() as request:
                yield request
                got_consent_staff_ts = env.now
                yield env.process(clinic.consent_patient(patient))
                release_consent_staff_ts = env.now
        else:
            got_consent_staff_ts = pd.NA
            release_consent_staff_ts = pd.NA

        # request change room
        with clinic.change_room.request() as request:
            yield request
            got_change_room_ts = env.now
            yield env.process(clinic.use_change_room(patient))
            release_change_room_ts = env.now

        # request gowned wait room
        with clinic.gowned_wait_room.request() as request:
            yield request
            got_gowned_wait_room_ts = env.now
            yield env.process(clinic.use_gowned_wait_room((patient)))
            release_gowned_wait_room_ts = env.now

        # 1.screen mammo
        if number <= pct_screen_mammo_scheduled:
            patient_type = 'screen'
            with clinic.scanner.request() as request:
                yield request
                got_screen_scanner_ts = env.now
                yield env.process(clinic.get_screen_mammo(patient))
                release_screen_scanner_ts = env.now


        # 2. dx mammo + dx us
        if pct_screen_mammo_scheduled < number <= pct_dx_mammo_us_scheduled:
            patient_type = 'dx mammo us'
            request = clinic.scanner.request()
            yield request
            got_dx_scanner_before_us_ts = env.now
            yield env.process(clinic.get_dx_mammo(patient))

            # rad review
            request_rad = clinic.radiologist.request()
            get_rad_dx_mammo_us_mammo_ts = env.now
            yield request_rad
            yield env.process(clinic.rad_review(patient))
            clinic.scanner.release(request)
            clinic.radiologist.release(request_rad)
            release_rad_dx_mammo_us_mammo_ts = env.now
            release_dx_scanner_before_us_ts = env.now

            request_2 = clinic.us_machine.request()
            yield request_2
            got_us_machine_after_dx_scanner_ts = env.now
            yield env.process(clinic.get_dx_us(patient))

            # rad review
            request_rad_2 = clinic.radiologist.request()
            get_rad_dx_mammo_us_us_ts = env.now
            yield request_rad_2
            yield env.process(clinic.rad_review(patient))
            clinic.us_machine.release(request_2)
            clinic.radiologist.release(request_rad_2)
            release_rad_dx_mammo_us_us_ts = env.now
            release_dx_scanner_us_machine_ts = env.now

        # 3. dx mammo
        if pct_dx_mammo_us_scheduled < number <= pct_dx_mammo_scheduled:
            patient_type = 'dx mammo'
            request = clinic.scanner.request()
            yield request
            got_dx_scanner_ts = env.now
            yield env.process(clinic.get_dx_mammo(patient))

            # rad review
            request_rad = clinic.radiologist.request()
            get_rad_dx_mammo_ts = env.now
            yield request_rad
            yield env.process(clinic.rad_review(patient))
            clinic.scanner.release(request)
            clinic.radiologist.release(request_rad)
            release_rad_dx_mammo_ts = env.now
            release_dx_scanner_ts = env.now

        # 4. dx us
        if pct_dx_mammo_scheduled < number <= pct_dx_us_scheduled:
            patient_type = 'dx us'
            request = clinic.us_machine.request()
            yield request
            got_us_machine_ts = env.now
            yield env.process(clinic.get_dx_us(patient))

            # rad review
            request_rad = clinic.radiologist.request()
            get_rad_dx_us_ts = env.now
            yield request_rad
            yield env.process(clinic.rad_review(patient))
            clinic.us_machine.release(request)
            clinic.radiologist.release(request_rad)
            release_rad_dx_us_ts = env.now
            release_us_machine_ts = env.now

        # 5. us-guided bx
        if pct_dx_us_scheduled < number <= pct_us_guided_bx_scheduled:
            patient_type = 'us bx'
            with clinic.us_machine.request() as request, clinic.radiologist.request() as request_rad:
                yield request & request_rad
                got_us_machine_bx_ts = env.now
                yield env.process(clinic.get_us_guided_bx(patient))
                release_us_machine_after_bx_ts = env.now

            # post bx mammo
            request = clinic.scanner.request()
            yield request
            got_scanner_after_us_bx_ts = env.now
            yield env.process(clinic.get_dx_mammo(patient))

            # rad review
            request_rad = clinic.radiologist.request()
            get_rad_us_bx_ts = env.now
            yield request_rad
            yield env.process(clinic.rad_review(patient))
            clinic.scanner.release(request)
            clinic.radiologist.release(request_rad)
            release_rad_us_bx_ts = env.now
            release_scanner_after_post_bx_mammo_ts = env.now

        # 6. mammo-guided bx
        if pct_us_guided_bx_scheduled < number <= pct_mammo_guided_bx_scheduled:
            patient_type = 'mammo bx'
            with clinic.scanner.request() as request, clinic.radiologist.request() as request_rad:
                yield request & request_rad
                got_scanner_bx_ts = env.now
                yield env.process(clinic.get_mammo_guided_bx(patient))
                # post bx mammo
                yield env.process(clinic.get_dx_mammo(patient))
                # rad review
                get_rad_mammo_bx_ts = env.now
                yield env.process(clinic.rad_review(patient))
                clinic.scanner.release(request)
                clinic.radiologist.release(request_rad)
                release_rad_mammo_bx_ts = env.now
                release_scanner_after_post_bx_mammo_ts = env.now

        # 7. screen us
        if pct_mammo_guided_bx_scheduled < number <= pct_screen_us_scheduled:
            patient_type = 'screen us'
            with clinic.us_machine.request() as request:
                yield request
                got_screen_us_machine_ts = env.now
                yield env.process(clinic.get_screen_us(patient))
                release_screen_us_machine_ts = env.now

        # request a change room
        with clinic.change_room.request() as request:
            yield request
            got_checkout_change_room_ts = env.now
            yield env.process(clinic.use_change_room(patient))
            release_checkout_change_room_ts = env.now

    exit_system_ts = env.now

    # create dict of timestamps
    timestamps = {'patient_id': patient,
                  'patient_type': patient_type,
                  'arrival_ts': arrival_ts,
                  'got_checkin_staff_ts': got_checkin_staff_ts,
                  'release_checkin_staff_ts': release_checkin_staff_ts,
                  'got_public_wait_room_ts': got_public_wait_room_ts,
                  'release_public_wait_room_ts': release_public_wait_room_ts,
                  'got_consent_staff_ts': got_consent_staff_ts,
                  'release_consent_staff_ts': release_consent_staff_ts,
                  'got_change_room_ts': got_change_room_ts,
                  'release_change_room_ts': release_change_room_ts,
                  'got_gowned_wait_room_ts': got_gowned_wait_room_ts,
                  'release_gowned_wait_room_ts': release_gowned_wait_room_ts,
                  'got_screen_scanner_ts': got_screen_scanner_ts,
                  'release_screen_scanner_ts': release_screen_scanner_ts,
                  'got_dx_scanner_ts': got_dx_scanner_ts,
                  'release_dx_scanner_ts': release_dx_scanner_ts,
                  'got_us_machine_ts': got_us_machine_ts,
                  'release_us_machine_ts': release_us_machine_ts,
                  'got_dx_scanner_before_us_ts': got_dx_scanner_before_us_ts,
                  'release_dx_scanner_before_us_ts': release_dx_scanner_before_us_ts,
                  'got_us_machine_after_dx_scanner_ts': got_us_machine_after_dx_scanner_ts,
                  'release_dx_scanner_us_machine_ts': release_dx_scanner_us_machine_ts,
                  'got_us_machine_bx_ts': got_us_machine_bx_ts,
                  'release_us_machine_after_bx_ts': release_us_machine_after_bx_ts,
                  'got_scanner_bx_ts': got_scanner_bx_ts,
                  'got_scanner_after_us_bx_ts': got_scanner_after_us_bx_ts,
                  'release_scanner_after_post_bx_mammo_ts': release_scanner_after_post_bx_mammo_ts,
                  'got_screen_us_machine_ts':  got_screen_us_machine_ts,
                  'release_screen_us_machine_ts': release_screen_us_machine_ts,
                  'got_scanner_after_mri_bx_ts': got_scanner_after_mri_bx_ts,
                  'got_mri_machine_ts': got_mri_machine_ts,
                  'release_mri_machine_ts': release_mri_machine_ts,
                  'got_checkout_change_room_ts': got_checkout_change_room_ts,
                  'release_checkout_change_room_ts': release_checkout_change_room_ts,
                  'get_rad_dx_mammo_ts': get_rad_dx_mammo_ts,
                  'release_rad_dx_mammo_ts': release_rad_dx_mammo_ts,
                  'get_rad_dx_us_ts': get_rad_dx_us_ts,
                  'release_rad_dx_us_ts': release_rad_dx_us_ts,
                  'get_rad_dx_mammo_us_mammo_ts': get_rad_dx_mammo_us_mammo_ts,
                  'release_rad_dx_mammo_us_mammo_ts': release_rad_dx_mammo_us_mammo_ts,
                  'get_rad_dx_mammo_us_us_ts': get_rad_dx_mammo_us_us_ts,
                  'release_rad_dx_mammo_us_us_ts': release_rad_dx_mammo_us_us_ts,
                  'get_rad_us_bx_ts': get_rad_us_bx_ts,
                  'release_rad_us_bx_ts': release_rad_us_bx_ts,
                  'get_rad_mri_bx_ts': get_rad_mri_bx_ts,
                  'release_rad_mri_bx_ts': release_rad_mri_bx_ts,
                  'get_rad_mammo_bx_ts': get_rad_mammo_bx_ts,
                  'release_rad_mammo_bx_ts': release_rad_mammo_bx_ts,
                  'exit_system_ts': exit_system_ts}
    clinic.timestamps_list.append(timestamps)