import argparse
import os
import json
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
    train_schedule_mzn, driver_schedule_mzn = run_mzn(mzn_timeout, mzn_solver)
    print('4. Converting Minizinc output to schedule')
    arr_to_schedule(p2d, driver_schedule_mzn, train_schedule_mzn)
    