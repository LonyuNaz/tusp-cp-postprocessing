import subprocess
import json
import numpy as np

SOLVER_NAME = 'chuffed'
TIMEOUT_SECONDS = 60
OUTPUT_FILE_NAME = 'solution.json'
MODEL_NAME = '2'

def mzn_arr_to_numpy(arr_str):
    for char in ['[',']','|', ' ']:
        arr_str = arr_str.replace(char, '')
    return np.array([[int(xx) for xx in x.split(',')] for x in arr_str.split('\n') if x != ''])

if __name__ == '__main__':

    subprocess.check_call(["minizinc", "--solver", SOLVER_NAME, "--output-time", "--time-limit", 
                                         str(TIMEOUT_SECONDS*1000), "--output-objective", "--json-stream", "-s", "-o", 
                                         OUTPUT_FILE_NAME, f'model_{MODEL_NAME}.mzn', 'test_2.dzn'])
    

    with open(OUTPUT_FILE_NAME, 'r') as f:
        lines = f.readlines()

    for idx, line in enumerate(lines):
        line_dict = json.loads(line)
        if line_dict['type'] == 'solution':
            [train_actions, driver_actions] = line_dict['output']["default"].split('][')
    
        


    print(mzn_arr_to_numpy(train_actions))
    print(mzn_arr_to_numpy(driver_actions))


