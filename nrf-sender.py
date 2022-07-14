import argparse
from datetime import datetime
from random import normalvariate
from random import randrange
import struct
import re
import sys
import time
import traceback

import pigpio
from nrf24 import *
import py_midicsv as pm


if __name__ == "__main__":    
    print("Python NRF24 Simple Sender Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="simple-sender.py", description="Simple NRF24 Sender Example.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs='?', default='1SNSR', help="Address to send to (3 to 5 ASCII characters).")
    
    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    if not (2 < len(address) < 6):
        print(f'Invalid address {address}. Addresses must be 3 to 5 ASCII characters.')
        sys.exit(1)

    # Connect to pigpiod
    print(f'Connecting to GPIO daemon on {hostname}:{port} ...')
    pi = pigpio.pi(hostname, port)
    if not pi.connected:
        print("Not connected to Raspberry Pi ... goodbye.")
        sys.exit()

    # MIDI to PWM configs

    ms_per_tick = 9/4080*1000.0
    current_time = round(time.time()*1000.0)


    midi_string = pm.midi_to_csv("Kuo_PianoConcertoino_Mvt.2_v2_Ab_11_L.mid")

    pattern = re.compile("^\s+|\s*,\s*|\s+$")
    notes_list = [pattern.split(note.strip()) for note in midi_string if "Note_" in note]


    pwm_frequency = 80
    pwm_lowest_dutycycle = 170

    # pi = pigpio.pi()
    pi.set_PWM_frequency(6, pwm_frequency)
    pi.set_PWM_frequency(13, pwm_frequency)
    pi.set_PWM_frequency(19, pwm_frequency)
    pi.set_PWM_frequency(26, pwm_frequency)
    pi.set_PWM_frequency(12, pwm_frequency)
    pi.set_PWM_frequency(16, pwm_frequency)
    pi.set_PWM_frequency(20, pwm_frequency)
    pi.set_PWM_frequency(21, pwm_frequency)


    # Create NRF24 object.
    # PLEASE NOTE: PA level is set to MIN, because test sender/receivers are often close to each other, and then MIN works better.
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.LOW)
    nrf.set_address_bytes(len(address))
    nrf.open_writing_pipe(address)
    
    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    try:
        print(f'Send to {address}')
        count = 0
        while True:

            # Emulate that we read temperature and humidity from a sensor, for example
            # a DHT22 sensor.  Add a little random variation so we can see that values
            # sent/received fluctuate a bit.
            temperature = normalvariate(23.0, 0.5)
            humidity = normalvariate(62.0, 0.5)
            print(f'Sensor values: temperature={temperature}, humidity={humidity}')

            # Pack temperature and humidity into a byte buffer (payload) using a protocol 
            # signature of 0x01 so that the receiver knows that the bytes we are sending 
            # are a temperature and a humidity (see "simple-receiver.py").
            payload = struct.pack("<Bff", 0x01, temperature, humidity)

            # Send the payload to the address specified above.
            nrf.reset_packages_lost()
            nrf.send(payload)
            try:
                nrf.wait_until_sent()
            except TimeoutError:
                print('Timeout waiting for transmission to complete.')
                # Wait 10 seconds before sending the next reading.
                time.sleep(10)
                continue
            
            if nrf.get_packages_lost() == 0:
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

                print(f"Success: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")
            else:
                print(f"Error: lost={nrf.get_packages_lost()}, retries={nrf.get_retries()}")

            # Wait 10 seconds before sending the next reading.
            time.sleep(10)
    except:
        traceback.print_exc()
        nrf.power_down()
        pi.stop()




