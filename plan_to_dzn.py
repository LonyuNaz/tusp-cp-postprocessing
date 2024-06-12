
import re
import os
import numpy as np
from enum import Enum
from typing import List, Tuple, Set

class Direction(Enum):
    ASIDE = 0
    BSIDE = 1


class Train:
    def __init__(self, id: int, name: str):
        self.id: int = id
        self.name: str = name
        self.movements: List[Movement] = []

    def __str__(self) -> str:
        return f'Train(id={self.id}, name={self.name}, movements={[m.id for m in self.movements]})'
    
    def __repr__(self) -> str:
        return self.__str__()

class Track:
    def __init__(self, id: int, name: str):
        self.id: int = id
        self.name: str = name
        self.movements: List[Movement] = []
    
    def __str__(self) -> str:
        return f'Track(id={self.id}, name={self.name}, movements={[m.id for m in self.movements]})'
    
    def __repr__(self) -> str:
        return self.__str__()

class Movement:
    def __init__(self, id: int, train: Train, direction: Direction, origin: Track, destination: Track):
        self.id: int = id
        self.train: Train = train
        self.direction: Direction = direction
        self.origin: Track = origin
        self.destination: Track = destination

    def __str__(self) -> str:
        return f'Movement(id={self.id}, train={self.train.id}, direction={self.direction}, ' +\
               f'origin={self.origin.id}, destination={self.destination.id})'

    def __repr__(self) -> str:
        return self.__str__()

class PlanToDZN:

    def __init__(self, num_drivers: int, turns_included: bool = False):
        self.num_drivers = num_drivers
        self.turns_included = turns_included

        self.plan_lines = list()
        self.trains: List[Train] = list()
        self.tracks: List[Track] = list()
        self.movements: List[Movement] = list()
        self.turn_pairs: Set[Tuple[Movement, Movement]] = set()
        self.precedence_constraints: Set[Tuple[Movement, Movement]] = set()
        self.turn_constraints: Set[Tuple[Movement, Movement]] = set()
        self.start_order_constraints: Set[Tuple[Movement, Movement]] = set()
        self.non_overlap_constraints: Set[Tuple[Movement, Movement]] = set()
        self.durations: List[int] = list()


    def create_from_file(self, filepath: str):
        self._load_file(filepath)
        self._extract_objects()
        self._extract_movements()
        if not self.turns_included:
            self._add_turns()
        self._add_durations()
        self._precedences()
        self._non_overlap_pairs()
        self._start_precedences()
        self._write_dzn()

    def _load_file(self, filepath: str):
        with open(filepath, 'r') as f:
            lines = f.readlines()

        self.plan_lines = [re.findall(r'\(.*\)', line)[0][1:-1] 
                        for line in lines 
                        if any(x in line for x in ('track', 'train', 'driver'))]

    def _add_train(self, name: str):
        if all(t.name != name for t in self.trains):
            self.trains.append(Train(len(self.trains)+1, name))

    def _add_track(self, name: str):
        if all(t.name != name for t in self.tracks):
            self.tracks.append(Train(len(self.tracks)+1, name))

    def _add_movement(self, train_name: str, dir: Direction, track_from: str, track_to: str):
        train = self.get_train(name=train_name)
        origin = self.get_track(name=track_from)
        destination = self.get_track(name=track_to)
        new_movement = Movement(len(self.movements)+1, train, dir, origin, destination)
        self.movements.append(new_movement)
        train.movements.append(new_movement)
        origin.movements.append(new_movement)
        destination.movements.append(new_movement)


    def get_train(self, id=None, name=None) -> Train:
        if id is not None:
            return next((t for t in self.trains if t.id == id), None)
        elif name is not None:
            return next((t for t in self.trains if t.name == name), None)
        else:
            return None
        
    def get_track(self, id=None, name=None) -> Track:
        if id is not None:
            return next((t for t in self.tracks if t.id == id), None)
        elif name is not None:
            return next((t for t in self.tracks if t.name == name), None)
        else:
            return None
        
    def get_movement(self, id) -> Movement:
        return next((m for m in self.movements if m.id == id), None)

        
    # def load_string(self, plan_str: str):
    #     self.plan_lines = [re.findall(r'\(.*\)', line)[0][1:-1] 
    #                     for line in plan_str.split('\n') 
    #                     if any(x in line for x in ('track', 'train', 'driver'))]

    def _extract_objects(self):
        trains = list()
        tracks = list()
        for line in self.plan_lines:
            for element in line.split(' '):
                if element.startswith('train_'):
                    trains.append(element)
                elif element.startswith('track_'):
                    tracks.append(element)
        for t in trains:
            self._add_train(t)
        for t in tracks:
            self._add_track(t)

    def _extract_movements(self):
        self.movements = list()
        for line in self.plan_lines:
            if 'move' not in line:
                continue
            direction = Direction.ASIDE if 'aside' in line else Direction.BSIDE
            train = re.findall(r'train_\w+', line)[0]
            [track_from, track_to] = re.findall(r'track_\w+', line)
            self._add_movement(train, direction, track_from, track_to)


    def _add_turns(self):
        self.turn_pairs = set()
        for train in self.trains:
            if len(train.movements) <= 1:
                continue
            for i in range(len(train.movements)-1):
                if train.movements[i].direction != train.movements[i+1].direction:
                    self.turn_pairs.add((train.movements[i], train.movements[i+1]))

    def _start_precedences(self):
        for track in self.tracks:
            if len(track.movements) <= 1:
                continue
            for i in range(len(track.movements)-1):
                pair = (track.movements[i], track.movements[i+1])
                if track.movements[i+1].destination in\
                      (track.movements[i].origin, track.movements[i].destination) and\
                    (track.movements[i+1].direction != track.movements[i].direction):
                    self.precedence_constraints.add(pair)
                elif pair not in self.precedence_constraints.union(self.turn_constraints) and\
                    track.movements[i+1].direction == track.movements[i].direction and\
                    track.movements[i+1].origin == track.movements[i].origin:
                    self.start_order_constraints.add(pair)

    def _precedences(self):
        self.precedence_constraints = set()
        for train in self.trains:
            if len(train.movements) <= 1:
                continue
            for i in range(len(train.movements)-1):
                if train.movements[i+1].direction == train.movements[i].direction:
                    self.precedence_constraints.add((train.movements[i], 
                                                train.movements[i+1]))
                else:
                    self.turn_constraints.add((train.movements[i], 
                                                train.movements[i+1]))

    def _non_overlap_pairs(self):
        for i in range(len(self.movements)-1):
            for j in range(i+1, len(self.movements)):
                if self.movements[j].destination in (self.movements[i].origin, self.movements[i].destination):
                    pair = (self.movements[i], self.movements[j])
                    if self.movements[j].destination in\
                      (self.movements[i].origin, self.movements[i].destination) and\
                    (self.movements[j].direction != self.movements[i].direction):
                        if pair not in self.precedence_constraints.union(self.turn_constraints):
                            self.non_overlap_constraints.add((self.movements[i], self.movements[j])) 
                        

    def _ordered_pairs(self):
        self.ordered_pairs = set()
        for track in self.tracks:
            if len(track.movements) <= 1:
                continue
            for i in range(len(track.movements)-1):
                self.ordered_pairs.add((track.movements[i], track.movements[i+1]))       
            
    def _add_durations(self):
        self.durations = list()
        for movement in self.movements:
            # TODO: change to dynamic durations
            self.durations.append(3)

    def _np_to_dzn_arr(self, arr):
        if len(np.shape(arr)) > 2:
            raise Exception('Not supported arrays with >2 dimensions')
        if len(np.shape(arr)) > 1 and np.shape(arr)[1] > 1 and np.shape(arr)[0] > 1:
            return '[|' + ',\n|'.join(','.join(str(int(x)) for x in moves) for moves in arr) + '|]'
        else:
            return '[' + ','.join(str(int(x)) for x in arr) + ']'

    def _write_dzn(self):
        if os.path.exists('minizinc/data.dzn'):
            os.remove('minizinc/data.dzn')

        self.precedence_constraints = sorted(self.precedence_constraints, key=lambda x: x[0].id)
        self.turn_constraints = sorted(self.turn_constraints, key=lambda x: x[0].id)
        self.start_order_constraints = sorted(self.start_order_constraints, key=lambda x: x[0].id)
        self.non_overlap_constraints = sorted(self.non_overlap_constraints, key=lambda x: x[0].id)

        preceding_str = self._np_to_dzn_arr([pc[0].id for pc in self.precedence_constraints])
        anteceding_str = self._np_to_dzn_arr([pc[1].id for pc in self.precedence_constraints])
        before_turn_str = self._np_to_dzn_arr([tc[0].id for tc in self.turn_constraints])
        after_turn_str = self._np_to_dzn_arr([tc[1].id for tc in self.turn_constraints])
        start_early_str = self._np_to_dzn_arr([so[0].id for so in self.start_order_constraints])
        start_later_str = self._np_to_dzn_arr([so[1].id for so in self.start_order_constraints])
        overlap_left_str = self._np_to_dzn_arr([ov[0].id for ov in self.non_overlap_constraints])
        overlap_right_str = self._np_to_dzn_arr([ov[1].id for ov in self.non_overlap_constraints])

        with open('minizinc/data.dzn', 'w') as f:
            f.writelines([
                f'NUM_TRAINS = {len(self.trains)};\n',
                f'NUM_ACTIONS = {len(self.movements)};\n',
                f'NUM_DRIVERS = {self.num_drivers};\n',
                '\n',
                f'D = {self._np_to_dzn_arr(self.durations)};\n',
                f'TA = {self._np_to_dzn_arr([m.train.id for m in self.movements])};\n',
                '\n',
                f'NUM_PRECEDENCE_CONSTRAINTS = {len(self.precedence_constraints)};\n',
                f'preceding = {preceding_str};\n',
                f'anteceding = {anteceding_str};\n',
                '\n',
                f'NUM_TURN_CONSTRAINTS = {len(self.turn_constraints)};\n',
                f'before_turn = {before_turn_str};\n',
                f'after_turn = {after_turn_str};\n',
                '\n',
                f'NUM_START_ORDER_CONSTRAINTS = {len(self.start_order_constraints)};\n',
                f'start_early = {start_early_str};\n',
                f'start_later = {start_later_str};\n',
                '\n',
                f'NUM_OVERLAP_CONSTRAINS = {len(self.non_overlap_constraints)};\n',
                f'overlap_left = {overlap_left_str};\n',
                f'overlap_right = {overlap_right_str};\n',
                '\n',
            ])
