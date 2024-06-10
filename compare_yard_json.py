import networkx
import json
import re

def create_graph_from_json(yard_json_file: str, track_name_mapping: dict) -> networkx.Graph:
    with open(yard_json_file, 'r') as f:
        yard_obj = json.load(f)

    graph = networkx.Graph()

    for track in yard_obj['trackParts']:
        track['name'] = re.sub('[^0-9a-zA-Z]+', '_', track['name'])

    entry_track_map = {re.sub('[^0-9a-zA-Z]+', '_', key): re.sub('[^0-9a-zA-Z]+', '_', val) 
                       for key, val in track_name_mapping.items()}

    for t in yard_obj['trackParts']:
        if t['type'] in ('RailRoad', 'Switch', 'EnglishSwitch'):
            if t['name'] in entry_track_map.keys():
                graph.add_node(entry_track_map[t['name']])
            else:                
                graph.add_node(t['name'])

    for t in yard_obj['trackParts']:
        if t['type'] in ('RailRoad', 'Switch', 'EnglishSwitch'):
            if t['name'] in entry_track_map.keys():
                t_name = entry_track_map[t['name']]
            else:
                t_name = t['name']
            for t2_id in t['aSide']:
                t2 = next(t2 for t2 in yard_obj['trackParts'] if t2['id'] == t2_id)
                if t2['type'] in ('RailRoad', 'Switch', 'EnglishSwitch'):
                    if t2['name'] in entry_track_map.keys():
                        t2_name = entry_track_map[t2['name']]
                    else:
                        t2_name = t2['name']
                    graph.add_edge(t_name, t2_name)
    return graph


def extend_plan(plan_file: str, yard_json_file: str, entry_track_map: dict):
    yard_graph = create_graph_from_json(yard_json_file, entry_track_map)
    
    with open(plan_file, 'r') as f:
        original_lines = f.readlines()
    new_lines = []

    for org_line in original_lines:
        line = org_line.lower().replace('\n','')
        if 'move' in org_line:
            direction = 'aside' if 'aside' in line else 'bside'
            train = re.findall(r'train_\w+', line)[0]
            [track_from, track_to] = re.findall(r'track_\w+', line)
            track_from = track_from.split('track_')[1]
            track_to = track_to.split('track_')[1]
            print(yard_graph.nodes)
            short_path = networkx.shortest_path(yard_graph, track_from, track_to)
            if len(short_path) > 2:
                for i in range(len(short_path)-1):
                    new_lines.append(f'(move_{direction} {train} track_{short_path[i]} track_{short_path[i+1]})')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
   
    with open('ext_plan.plan', 'w') as f:
        f.write('\n'.join(new_lines))
