import re
import time

import pigpio
import py_midicsv as pm

ms_per_tick = 9/4080*1000.0
current_time = round(time.time()*1000.0)


midi_string = pm.midi_to_csv("Kuo_PianoConcertoino_Mvt.2_v2_Ab_11_L.mid")

pattern = re.compile("^\s+|\s*,\s*|\s+$")
notes_list = [pattern.split(note.strip()) for note in midi_string if "Note_" in note]


pwm_frequency = 80
pwm_lowest_dutycycle = 170

pi = pigpio.pi()
pi.set_PWM_frequency(6, pwm_frequency)
pi.set_PWM_frequency(13, pwm_frequency)
pi.set_PWM_frequency(19, pwm_frequency)
pi.set_PWM_frequency(26, pwm_frequency)
pi.set_PWM_frequency(12, pwm_frequency)
pi.set_PWM_frequency(16, pwm_frequency)
pi.set_PWM_frequency(20, pwm_frequency)
pi.set_PWM_frequency(21, pwm_frequency)

current_time = round(time.time()*1000.0)

for note in notes_list:
    note_time = int(note[1]) * ms_per_tick
    note_velocity = int(note[5])
    pwm_duty = (255 - pwm_lowest_dutycycle) / 127 * note_velocity + pwm_lowest_dutycycle

    while note_time > round(time.time()*1000.0) - current_time:
        time.sleep(0.001)
    if note[2] == "Note_on_c":
        if note[4] == "56":
            pi.set_PWM_dutycycle(6, pwm_duty)
        elif note[4] == "63":
            pi.set_PWM_dutycycle(13, pwm_duty)
        elif note[4] == "68":
            pi.set_PWM_dutycycle(19, pwm_duty)
        elif note[4] == "72":
            pi.set_PWM_dutycycle(26, pwm_duty)
        elif note[4] == "75":
            pi.set_PWM_dutycycle(12, pwm_duty)
        elif note[4] == "78":
            pi.set_PWM_dutycycle(16, pwm_duty)
        elif note[4] == "80":
            pi.set_PWM_dutycycle(20, pwm_duty)
        elif note[4] == "82":
            pi.set_PWM_dutycycle(21, pwm_duty)
    elif note[2] == "Note_off_c":
        if note[4] == "56":
            pi.set_PWM_dutycycle(6, 0)
        elif note[4] == "63":
            pi.set_PWM_dutycycle(13, 0)
        elif note[4] == "68":
            pi.set_PWM_dutycycle(19, 0)
        elif note[4] == "72":
            pi.set_PWM_dutycycle(26, 0)
        elif note[4] == "75":
            pi.set_PWM_dutycycle(12, 0)
        elif note[4] == "78":
            pi.set_PWM_dutycycle(16, 0)
        elif note[4] == "80":
            pi.set_PWM_dutycycle(20, 0)
        elif note[4] == "82":
            pi.set_PWM_dutycycle(21, 0)