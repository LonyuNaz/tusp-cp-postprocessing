import subprocess
import json
import numpy as np

OUTPUT_FILE_NAME = 'minizinc/solution.json'
MODEL_NAME = 'minizinc/model.mzn'
DZN_NAME = 'minizinc/data.dzn'

def mzn_arr_to_numpy(arr_str):
    for char in ['[',']','|', ' ']:
        arr_str = arr_str.replace(char, '')
    return np.array([[int(xx) for xx in x.split(',')] for x in arr_str.split('\n') if x != ''])

def run_and_wait_for_output(timeout_seconds: int, solver_name: str):
    subprocess.check_call(["minizinc", "-w", "--solver", solver_name, "-f", "-a", "--output-time", "--time-limit", 
                                         str(timeout_seconds*1000), "--output-objective", "--json-stream", "-s", "-o", 
                                         OUTPUT_FILE_NAME, MODEL_NAME, DZN_NAME])
    
def parse_output_json():
    with open(OUTPUT_FILE_NAME, 'r') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line_dict = json.loads(line)
        if line_dict['type'] == 'solution':
            all_arr_str = line_dict['output']["default"].split('][')
            arrays = []
            for arr_str in all_arr_str:
                arrays.append([int(x) for x in arr_str.replace(']','').replace('[','').split(',')])
    return arrays


def run_mzn(timeout_seconds: int, solver_name: str):
    run_and_wait_for_output(timeout_seconds, solver_name)
    return parse_output_json()