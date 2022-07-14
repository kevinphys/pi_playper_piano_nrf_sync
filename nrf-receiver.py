import argparse
from datetime import datetime
import struct
import re
import sys
import time
import traceback

import pigpio
from nrf24 import *
import py_midicsv as pm

#
# A simple NRF24L receiver that connects to a PIGPIO instance on a hostname and port, default "localhost" and 8888, and
# starts receiving data on the address specified.  Use the companion program "simple-sender.py" to send data to it from
# a different Raspberry Pi.
#
if __name__ == "__main__":

    print("Python NRF24 Simple Receiver Example.")
    
    # Parse command line argument.
    parser = argparse.ArgumentParser(prog="simple-receiver.py", description="Simple NRF24 Receiver Example.")
    parser.add_argument('-n', '--hostname', type=str, default='localhost', help="Hostname for the Raspberry running the pigpio daemon.")
    parser.add_argument('-p', '--port', type=int, default=8888, help="Port number of the pigpio daemon.")
    parser.add_argument('address', type=str, nargs='?', default='1SNSR', help="Address to listen to (3 to 5 ASCII characters)")

    args = parser.parse_args()
    hostname = args.hostname
    port = args.port
    address = args.address

    # Verify that address is between 3 and 5 characters.
    if not (2 < len(address) < 6):
        print(f'Invalid address {address}. Addresses must be between 3 and 5 ASCII characters.')
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


    midi_string = pm.midi_to_csv("Kuo_PianoConcertoino_Mvt.2_v2_Ab_11_H.mid")

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
    nrf = NRF24(pi, ce=25, payload_size=RF24_PAYLOAD.DYNAMIC, channel=100, data_rate=RF24_DATA_RATE.RATE_250KBPS, pa_level=RF24_PA.MIN)
    nrf.set_address_bytes(len(address))

    # Listen on the address specified as parameter
    nrf.open_reading_pipe(RF24_RX_ADDR.P1, address)
    
    # Display the content of NRF24L01 device registers.
    nrf.show_registers()

    # Enter a loop receiving data on the address specified.
    try:
        print(f'Receive from {address}')
        count = 0
        while True:

            # As long as data is ready for processing, process it.
            while nrf.data_ready():
                # Count message and record time of reception.            
                count += 1
                now = datetime.now()
                
                # Read pipe and payload for message.
                pipe = nrf.data_pipe()
                payload = nrf.get_payload()    

                # Resolve protocol number.
                protocol = payload[0] if len(payload) > 0 else -1            

                hex = ':'.join(f'{i:02x}' for i in payload)

                # Show message received as hex.
                print(f"{now:%Y-%m-%d %H:%M:%S.%f}: pipe: {pipe}, len: {len(payload)}, bytes: {hex}, count: {count}")

                # If the length of the message is 9 bytes and the first byte is 0x01, then we try to interpret the bytes
                # sent as an example message holding a temperature and humidity sent from the "simple-sender.py" program.
                if len(payload) == 9 and payload[0] == 0x01:
                    values = struct.unpack("<Bff", payload)
                    print(f'Protocol: {values[0]}, temperature: {values[1]}, humidity: {values[2]}')
                
                current_time = round(time.time()*1000.0)

                for note in notes_list:
                    note_time = int(note[1]) * ms_per_tick
                    note_velocity = int(note[5])
                    pwm_duty = (255 - pwm_lowest_dutycycle) / 127 * note_velocity + pwm_lowest_dutycycle

                    while note_time > round(time.time()*1000.0) - current_time:
                        time.sleep(0.001)
                    if note[2] == "Note_on_c":
                        if note[4] == "72":
                            pi.set_PWM_dutycycle(6, pwm_duty)
                        elif note[4] == "75":
                            pi.set_PWM_dutycycle(13, pwm_duty)
                        elif note[4] == "78":
                            pi.set_PWM_dutycycle(19, pwm_duty)
                        elif note[4] == "80":
                            pi.set_PWM_dutycycle(26, pwm_duty)
                        elif note[4] == "82":
                            pi.set_PWM_dutycycle(12, pwm_duty)
                        elif note[4] == "84":
                            pi.set_PWM_dutycycle(16, pwm_duty)
                        elif note[4] == "85":
                            pi.set_PWM_dutycycle(20, pwm_duty)
                        elif note[4] == "87":
                            pi.set_PWM_dutycycle(21, pwm_duty)
                    elif note[2] == "Note_off_c":
                        if note[4] == "72":
                            pi.set_PWM_dutycycle(6, 0)
                        elif note[4] == "75":
                            pi.set_PWM_dutycycle(13, 0)
                        elif note[4] == "78":
                            pi.set_PWM_dutycycle(19, 0)
                        elif note[4] == "80":
                            pi.set_PWM_dutycycle(26, 0)
                        elif note[4] == "82":
                            pi.set_PWM_dutycycle(12, 0)
                        elif note[4] == "84":
                            pi.set_PWM_dutycycle(16, 0)
                        elif note[4] == "85":
                            pi.set_PWM_dutycycle(20, 0)
                        elif note[4] == "87":
                            pi.set_PWM_dutycycle(21, 0)

            # Sleep 100 ms.
            time.sleep(0.1)
    except:
        traceback.print_exc()
        nrf.power_down()
        pi.stop()