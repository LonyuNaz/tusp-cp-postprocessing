from typing import Tuple
from numpy.typing import ArrayLike

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from plan_to_dzn import PlanToDZN
from datetime import datetime, timedelta
from typing import Tuple, List

DT_MINS = 5

ENTER_TRAIN = 0.1
EXIT_TRAIN = 0.2
CHANGE_DIRECTION = 0.3

def init_train_driver_schedules(start_times: ArrayLike, 
                                durations: ArrayLike, 
                                action_train: ArrayLike,
                                action_driver: ArrayLike) -> Tuple[ArrayLike, ArrayLike]:
    num_trains = np.max(action_train)
    num_drivers = np.max(action_driver)
    max_end_time = np.max(start_times)+np.max(durations)
    FIRST_TRAIN = np.min(action_train)
    FIRST_DRIVER = np.min(action_driver)
    DRIVER_IDLE = FIRST_DRIVER-1
    train_schedule = np.zeros((num_trains,max_end_time))
    driver_schedule = np.ones((num_drivers,max_end_time)) * (FIRST_TRAIN-1)


    for i in range(len(start_times)):
        train_id = action_train[i]
        driver_id = action_driver[i]
        train_schedule[train_id-FIRST_TRAIN,start_times[i]:start_times[i]+durations[i]] = i+1
        driver_schedule[driver_id-FIRST_DRIVER,start_times[i]:start_times[i]+durations[i]] = train_id

    return train_schedule, driver_schedule

def finalize_driver_schedule(driver_schedule: ArrayLike) -> ArrayLike:
    DS = driver_schedule.copy()
    DRIVER_IDLE = np.min(DS)
    for d in range(DS.shape[0]):
        for t in range(DS.shape[1]-2):
            if t == 0 and\
                driver_schedule[d,t] == DRIVER_IDLE and\
                driver_schedule[d,t+1] != DRIVER_IDLE:
                DS[d,t] = DS[d,t+1] + ENTER_TRAIN
            elif driver_schedule[d,t] == DRIVER_IDLE and\
                driver_schedule[d,t+1] == DRIVER_IDLE and\
                driver_schedule[d,t+2] != DRIVER_IDLE:
                 DS[d,t+1] = DS[d,t+2] + ENTER_TRAIN
            elif driver_schedule[d,t] != DRIVER_IDLE and\
                driver_schedule[d,t+1] == DRIVER_IDLE and\
                driver_schedule[d,t+2] == DRIVER_IDLE:
                DS[d,t+1] = DS[d,t] + EXIT_TRAIN   
            elif driver_schedule[d,t] != DRIVER_IDLE and\
                driver_schedule[d,t+1] == DRIVER_IDLE and\
                driver_schedule[d,t+2] != DRIVER_IDLE:
                DS[d,t+1] = DS[d,t+2] + CHANGE_DIRECTION
    return DS

def parse_mzn_arrays(start_times: ArrayLike, 
                    durations: ArrayLike, 
                    action_train: ArrayLike,
                    action_driver: ArrayLike,
                    movement_labels: List[str] = None):
    train_schedule, driver_schedule = init_train_driver_schedules(start_times,durations, 
                                                                  action_train, action_driver)
    driver_schedule = finalize_driver_schedule(driver_schedule)
    train_labels = (['idle'] + movement_labels) if movement_labels else [f'action {int(i)}' for i in np.sort(np.unique(action_train))]
    plot_schedule(train_schedule, train_labels)
    driver_labels = [f'action {int(i)}' for i in np.sort(np.unique(driver_schedule))]
    plot_schedule(train_schedule, driver_labels)

def plot_schedule(schedule: ArrayLike, labels: List[str]):
    # plt.figure(figsize=(20,10))
    im = plt.imshow(schedule, aspect='auto', cmap='tab20b')
    # get the colors of the values, according to the 
    # colormap used by imshow
    colors = [ im.cmap(im.norm(i)) for i in range(len(labels))]
    # create a patch (proxy artist) for every color 
    patches = [ mpatches.Patch(color=colors[i], label=labels[i] ) for i in range(len(labels)) ]
    # put those patched as legend-handles into the legend
    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/train_schedule.png')
    