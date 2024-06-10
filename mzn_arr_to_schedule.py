import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from plan_to_dzn import PlanToDZN
from datetime import datetime, timedelta
from typing import Tuple, List

DT_MINS = 5

def arr_to_schedule(p2d_obj: PlanToDZN, driver_schedule_mzn: np.ndarray, train_schedule_mzn: np.ndarray):
    driver_schedule = {f'driver {i+1}':[] for i in range(p2d_obj.num_drivers)}
    for i, driver in enumerate(driver_schedule.keys()):
        log = []
        for j in range(np.shape(driver_schedule_mzn)[1]):
            appended = False
            if j == 0:
                if driver_schedule_mzn[i,j] > 0:
                    train_id = driver_schedule_mzn[i,j]
                    train_name = p2d_obj.get_train(id=train_id).name
                    log.append('enter train ' + train_name)
                    appended = True
            elif j < (np.shape(driver_schedule_mzn)[1]-1):
                if driver_schedule_mzn[i,j] > 0:
                    train_id = driver_schedule_mzn[i,j]
                    train_name = p2d_obj.get_train(id=train_id).name
                    if train_schedule_mzn[train_id-1,j] == 0 and\
                         train_schedule_mzn[train_id-1,j+1] == driver_schedule_mzn[i,j]:
                        log.append('enter train ' + train_name)
                        appended = True
                    elif train_schedule_mzn[train_id-1,j] == 0 and\
                         train_schedule_mzn[train_id-1,j-1] == driver_schedule_mzn[i,j]:
                        log.append('exit train ' + train_name)
                        appended = True
                    elif len(log) > 0 and 'enter train' in log[-1]:
                        movement = p2d_obj.get_movement(train_schedule_mzn[train_id-1,j])
                        log.append(f'drive {train_name.split('train_')[1]}: ' +\
                                   f'{movement.origin.name.split('track_')[1]} --> {movement.destination.name.split('track_')[1]}')
                        appended = True
                elif driver_schedule_mzn[i,j] == 0:
                    if driver_schedule_mzn[i,j-1] > 0 and\
                         driver_schedule_mzn[i,j-1] == driver_schedule_mzn[i,j+1]:
                        log.append(f'change direction {train_name}')
                        appended = True
                    
            elif j == (np.shape(driver_schedule_mzn)[1]-1):
                if driver_schedule_mzn[i,j] > 0 and\
                    train_schedule_mzn[driver_schedule_mzn[i,j]-1,j] == 0:
                    log.append('exit train ' + train_name)
                    appended = True

            if not appended:
                if len(log) > 0 and 'driv' in log[-1]:
                    log.append('driving')
                else:
                    log.append('')

        driver_schedule[driver] = log
    start_time = datetime.strptime('0:00', '%H:%M').time()
    start_datetime = datetime.combine(datetime.now(), start_time)
    timestamps = [start_datetime+(i*timedelta(minutes=DT_MINS)) for i in range(np.shape(driver_schedule_mzn)[1])]
    max_len = len(start_datetime.__str__())
    df = pd.DataFrame({'Timestamp':[t.__str__() for t in timestamps], **driver_schedule}).T
    pad = lambda x: x.str.pad(max(max_len, x.str.len().max()))
    df.apply(pad).to_csv('output/schedule.csv', sep=';', index=False) 

    for driver, schedule in driver_schedule.items():
        with open(f'output/{driver}_schedule.txt', 'w') as f:
            f.write(prettify_log(schedule, timestamps))

    plt.figure(figsize=(10,5))
    plt.imshow(train_schedule_mzn, aspect='auto')
    plt.colorbar()
    plt.grid(True)
    plt.savefig('output/train_schedule.png')

    plt.cla()
    plt.figure(figsize=(10,5))
    plt.imshow(driver_schedule_mzn, aspect='auto')
    plt.colorbar()
    plt.grid(True)
    plt.savefig('output/driver_schedule.png')

def prettify_log(log: List[str], dates: List[datetime]) -> str:
    return "\n".join(dates[i].strftime('%H:%M') + ": " + log[i] for i in range(len(log)))