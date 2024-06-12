import argparse
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from compare_yard_json import extend_plan
from plan_to_dzn import PlanToDZN
from run_mzn import run_mzn
from mzn_arr_to_schedule import arr_to_schedule

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('plan_file', help="File containing the plan extracted from PDDL")
    parser.add_argument('--yard-json', help="JSON file containing description of shunting yard", default=None)
    parser.add_argument('--entry-track-map', help='JSON string of entry track maps', default=None)
    parser.add_argument('--num-drivers', help="Amount of drivers to be scheduled", type=int, default=1)
    parser.add_argument('--turn-included', help="Set this flag if the PDDL plan contains 'turn' actions", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument('--mzn-timeout', help="Timeout seconds for Minizinc model", type=int, default=300)
    parser.add_argument('--mzn-solver', help="Solver used to solve Minizinc model", type=str, default='chuffed')

    args = parser.parse_args()

    plan_filepath = os.path.abspath(args.plan_file)
    assert os.path.exists(plan_filepath)

    num_drivers = args.num_drivers
    assert num_drivers > 0

    turn_included = args.turn_included
    mzn_timeout = args.mzn_timeout
    mzn_solver = args.mzn_solver

    print('1. Ensuring plan is consistent with real shunting yard')
    if args.yard_json is not None:
        entry_track_map = dict()
        try:
            entry_track_map = json.loads(str(args.entry_track_map))
        except:
            pass
        extend_plan(plan_filepath, args.yard_json, entry_track_map)
        plan_filepath = 'ext_plan.plan'
    print('2. Converting plan to DZN file')
    p2d = PlanToDZN(num_drivers, turn_included)
    p2d.create_from_file(plan_filepath)
    print('3. Running Minizinc model')
    [start_times, durations, action_driver, action_train] = run_mzn(mzn_timeout, mzn_solver)
    print('4. Converting Minizinc output to schedule')
    train_schedule = np.ones((np.max(action_train),np.max(start_times)+np.max(durations))) * (len(start_times)+1)
    for i in range(len(start_times)):
        train_id = action_train[i]-1
        train_schedule[train_id,start_times[i]:start_times[i]+durations[i]] = i
    plt.figure(figsize=(40,30))
    im = plt.imshow(train_schedule, aspect='auto', cmap='tab20b')
    # get the colors of the values, according to the 
    # colormap used by imshow
    labels = [f'{m.origin.name}-->{m.destination.name}' for m in p2d.movements]
    colors = [ im.cmap(im.norm(i)) for i in range(len(labels)+1)]
    # create a patch (proxy artist) for every color 
    patches = [ mpatches.Patch(color=colors[i], label=labels[i] ) for i in range(len(labels)) ]
    # put those patched as legend-handles into the legend

    plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2)
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('output/train_schedule.png')
    