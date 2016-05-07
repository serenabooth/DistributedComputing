import csv
from datetime import datetime

with open('experiment_synch_data.csv', 'w') as csvfile:
    fieldnames = ['time', 'expected_brightness_value']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()

    on = 0
    state_ct = 0
    for i in range(0, 120 * 60 * 5):
        # each frame is 8.33333 milliseconds
        # assuming heartbeat is 60bpm, the bulb should be on for 1 second and off for 1 secs
        if on: 
            writer.writerow({'time': str(i), 'expected_brightness_value': '0'})
        else:
            writer.writerow({'time': str(i), 'expected_brightness_value': '255'})

        if state_ct == 120: 
            on = (on + 1) % 2
            state_ct = 0

        state_ct += 1
