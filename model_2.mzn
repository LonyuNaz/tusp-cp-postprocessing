
include "globals.mzn";

int: NUM_TRAINS;
int: NUM_TIMESTEPS;
int: NUM_ACTIONS;
int: NUM_DRIVERS;

int: SCHEDULED_ACTIONS_PER_TRAIN;
int: PAUSE_ACTION_PAIRS;
int: OVERLAP_ACTION_PAIRS;
int: ORDER_ACTION_PAIRS;

%------------------------

array[1..NUM_ACTIONS] of int: action_durations;
array[1..PAUSE_ACTION_PAIRS, 1..2] of 1..NUM_ACTIONS: actions_require_pause_in_between;
array[1..OVERLAP_ACTION_PAIRS, 1..2] of 1..NUM_ACTIONS: actions_cannot_overlap;
array[1..ORDER_ACTION_PAIRS, 1..2] of 1..NUM_ACTIONS: actions_must_start_before;
array[1..NUM_TRAINS, 1..SCHEDULED_ACTIONS_PER_TRAIN] of 0..NUM_ACTIONS: train_actions;

%------------------------

array[1..NUM_TRAINS, 1..NUM_TIMESTEPS] of var 0..NUM_ACTIONS: train_schedule;
array[1..NUM_DRIVERS, 1..NUM_TIMESTEPS] of var 0..NUM_TRAINS: driver_schedule;

%------------------------

function var int: getMaxIndexOfValueGeqThan(array[int] of var int: arr, int: val) = 
   max(  [ if arr[i] >= val
              then i
           else 0 endif  
          | i in index_set(arr) ]
   );


%------------------------



% do all actions that are scheduled for each train
constraint forall (x in 1..NUM_TRAINS)(
    array2set(train_actions[x, ..]) 
    = 
    array2set(train_schedule[x, ..])
);

% do all actions that are scheduled for each train in order
constraint forall (x in 1..NUM_TRAINS)(
    increasing([train_schedule[x, t] | t in 1..NUM_TIMESTEPS where train_schedule[x, t] > 0]) 
);

% amount concurrent movements determined by drivers
constraint forall (t in 1..NUM_TIMESTEPS)(
    sum([bool2int(train_schedule[x,t] > 0) | x in 1..NUM_TRAINS]) <= NUM_DRIVERS
);

% trains cannot start out driving, there is at least the enter action
constraint forall (x in 1..NUM_TRAINS)(
    train_schedule[x, 1] = 0
);

% minimum consecutive values for first timestep
constraint forall (x in 1..NUM_TRAINS, t in 1..(NUM_TIMESTEPS-2))(
    if (
        (train_schedule[x, t-1] != train_schedule[x, t] /\ train_schedule[x, t] > 0)
        \/
        (t = 2 /\ train_schedule[x, t-1] > 0)
    ) then (
        sum([bool2int(train_schedule[x, tt] = train_schedule[x, t]) 
        | tt in (t-1)..(t+action_durations[train_schedule[x, t]])])
        = action_durations[train_schedule[x, t]]
    )
    endif
);

% do not do an action just because you can
constraint global_cardinality(train_schedule, 1..NUM_ACTIONS, action_durations);

% certain actions cannot occur at the same time
constraint not exists(t in 1..NUM_TIMESTEPS, o in 1..OVERLAP_ACTION_PAIRS)(
    member(train_schedule[..,t], actions_cannot_overlap[o, 1])
    /\ member(train_schedule[..,t], actions_cannot_overlap[o, 2])
);

% certain actions must occur before others
constraint forall (s in 1..ORDER_ACTION_PAIRS)(
    min([t | t in 1..NUM_TIMESTEPS where member(train_schedule[..,t], actions_must_start_before[s,1])])
    < min([t | t in 1..NUM_TIMESTEPS where member(train_schedule[..,t], actions_must_start_before[s,2])])
);

% certain actions need a 'pause' in between (actions that require a driver to change direction)
constraint forall (p in 1..PAUSE_ACTION_PAIRS)(
    max([t | t in 1..NUM_TIMESTEPS where member(train_schedule[..,t], actions_require_pause_in_between[p,1])])
    < (min([t | t in 1..NUM_TIMESTEPS where member(train_schedule[..,t], actions_require_pause_in_between[p,2])]) - 1)
);


% driving only possible when operator inside, cannot be 
constraint forall (x in 1..NUM_TRAINS, t in 1..(NUM_TIMESTEPS-2))(
    if (
        train_schedule[x, t] > 0 \/ train_schedule[x, t+1] > 0 \/ train_schedule[x, t+2] > 0
    ) then (
        member(driver_schedule[..,t+1], x)
    ) else (
        not member(driver_schedule[..,t+1], x)
    )
    endif
);

% at most 1 driver per train
constraint forall (d in 1..NUM_DRIVERS, t in 1..NUM_TIMESTEPS)(
    at_most(1, driver_schedule[..,t], d)
);

% when two drivers change position, there must be a gap in the schedule
constraint forall (d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    if (
        driver_schedule[d, t] > 0
    ) then (
        not exists (dd in 1..NUM_DRIVERS)(
            dd != d
            /\ driver_schedule[dd, t+1] = driver_schedule[d, t]
        )
    )
    endif
);

% when a driver changes train, there must be a gap in the schedule
constraint not exists (d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    driver_schedule[d, t] > 0 /\ driver_schedule[d, t+1] > 0 /\ driver_schedule[d, t] != driver_schedule[d, t+1] 
);



% a

solve 
% satisfy;
minimize max([
    max([t | t in 1..NUM_TIMESTEPS where sum(train_schedule[..,t]) > 0]),
    max([t | t in 1..NUM_TIMESTEPS where sum(driver_schedule[..,t]) > 0]),
]);


output(
        [
            show2d(train_schedule),
            show2d(driver_schedule),
        ]
);

