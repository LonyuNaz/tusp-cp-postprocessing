include "globals.mzn";


%----------------------------------

int: NUM_TIMESTEPS = 30;
int: NUM_TRACKS = 3;
int: NUM_TRAINS = 4;
int: NUM_DEFAULT_TRAIN_ACTIONS = 1; % 1=nothing, 2=wait
int: NUM_DRIVERS = 2;

array [1..2, 1..2] of var 1..NUM_TRACKS: movement_mapping = [|1, 2,
                                                             |2, 3|];

int: NUM_MOVEMENTS_IN_SCHEDULE = 4;
array [1..NUM_MOVEMENTS_IN_SCHEDULE, 1..3] of int: movement_order = [| 1, 1, 3,
                                                                     | 2, 1, 3,
                                                                     | 3, 1, 3,
                                                                     | 4, 1, 3|];


%----------------------------------

array [1..NUM_TRAINS, 1..NUM_TIMESTEPS] of var 0..NUM_MOVEMENTS_IN_SCHEDULE: train_actions;
array [1..NUM_DRIVERS, 1..NUM_TIMESTEPS] of var 0..NUM_TRAINS: driver_locations;

%----------------------------------

function var int: getMaxIndexOfValueGeqThan(array[int] of var int: arr, int: val) = 
   max(  [ if arr[i] >= val
              then i
           else 0 endif  
          | i in index_set(arr) ]
   );

%----------------------------------


% do all the movements that are mentioned in the schedule
constraint forall (x in 1..NUM_TRAINS)(
    array2set([i | i in 1..NUM_MOVEMENTS_IN_SCHEDULE where movement_order[i, 1] = x]) 
    = 
    array2set([train_actions[x, t] | t in 1..NUM_TIMESTEPS where train_actions[x, t] >= NUM_DEFAULT_TRAIN_ACTIONS])
);

% only allowed to do either action in the schedule or nothing (waiting)
constraint forall (x in 1..NUM_TRAINS, t in 1..NUM_TIMESTEPS)(
    train_actions[x, t] < NUM_DEFAULT_TRAIN_ACTIONS \/ movement_order[train_actions[x, t], 1] = x
);

% do actions per train in order
constraint forall (x in 1..NUM_TRAINS)(
    increasing([train_actions[x, t] | t in 1..NUM_TIMESTEPS where train_actions[x, t] > 0]) 
);

% maximum amount of concurrent movements is linked to the amount of drivers
constraint forall (t in 1..NUM_TIMESTEPS)(
    
    at_least((NUM_TRAINS-NUM_DRIVERS), train_actions[.., t], 0)
);

% driving only possible when operator inside
constraint forall (x in 1..NUM_TRAINS, t in 1..NUM_TIMESTEPS)(
    if (
        train_actions[x, t] >= NUM_DEFAULT_TRAIN_ACTIONS
    ) then (
        exists (d in 1..NUM_DRIVERS)(
            driver_locations[d, t] = x
        )
    )
    endif
);

% driver must enter a train before it can move
constraint forall (x in 1..NUM_TRAINS, d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    if (
        train_actions[x, t] < NUM_DEFAULT_TRAIN_ACTIONS
        /\ train_actions[x, t+1] >= NUM_DEFAULT_TRAIN_ACTIONS
        /\ driver_locations[d, t+1] = x
    ) then (
        driver_locations[d, t] = x
    )
    endif
);

% driver must exit a train before he can do anything else
constraint forall (x in 1..NUM_TRAINS, d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    if (
        train_actions[x, t] >= NUM_DEFAULT_TRAIN_ACTIONS
        /\ train_actions[x, t+1] < NUM_DEFAULT_TRAIN_ACTIONS
        /\ driver_locations[d, t] = x
    ) then (
        driver_locations[d, t+1] = x
    )
    endif
);

% driver must exit a train before it can move
constraint forall (x in 1..NUM_TRAINS, d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    if (
        train_actions[x, t] < NUM_DEFAULT_TRAIN_ACTIONS
        /\ train_actions[x, t+1] < NUM_DEFAULT_TRAIN_ACTIONS
    ) then (
        (
            driver_locations[d, t] != x
            /\ driver_locations[d, t+1] != x
        ) 
        \/
        (
            driver_locations[d, t+1] = 0
            \/ driver_locations[d, t] = 0
        )
    )
    endif
);


% driver enter in order
constraint (
    increasing([max(driver_locations[.., t]) | t in 1..NUM_TIMESTEPS where max(driver_locations[.., t]) > 0])
);


% one driver per train
constraint forall (x in 1..NUM_TRAINS, t in 1..NUM_TIMESTEPS)(
    sum([bool2int(driver_locations[d, t] = x) | d in 1..NUM_DRIVERS]) <= 1
);

% driver switch takes time
constraint forall (d in 1..NUM_DRIVERS, t in 1..(NUM_TIMESTEPS-1))(
    not exists (dd in 1..NUM_DRIVERS)(
        d != dd
        /\ driver_locations[d, t] > 0
        /\ driver_locations[d, t] = driver_locations[dd, t+1]
    )
);


% minimum consecutive values
constraint forall (x in 1..NUM_TRAINS, t in 1..(NUM_TIMESTEPS-1))(
    if (
        train_actions[x, t] != train_actions[x, t+1]
        /\ train_actions[x, t+1] >= NUM_DEFAULT_TRAIN_ACTIONS
        /\ ((NUM_TIMESTEPS - t - 1) >= movement_order[train_actions[x, t+1], 3])
    ) then (
        sum([bool2int(train_actions[x, tt] = train_actions[x, t+1]) 
        | tt in (t+1)..(t+1+movement_order[train_actions[x, t+1], 3])])
        = movement_order[train_actions[x, t+1], 3]
    )
    endif
);


% driver enter in order
constraint forall (d in 1..NUM_DRIVERS)(
    increasing([driver_locations[d, t] | t in 1..NUM_TIMESTEPS where driver_locations[d, t] > 0]) 
);


% prevent collisions
constraint forall (x in 1..NUM_TRAINS, t in 1..NUM_TIMESTEPS)(
    if (
        train_actions[x, t] >= NUM_DEFAULT_TRAIN_ACTIONS
    ) then (
        not exists (xx in 1..NUM_TRAINS)(
            x != xx
            /\ movement_mapping[movement_order[train_actions[x, t], 2], 1]
                == movement_mapping[movement_order[train_actions[xx, t], 2], 2]
        )
    )
    endif
);

constraint symmetry_breaking_constraint(
    driver_locations[1, 1] = 1
    /\ driver_locations[1, 2] = 1
    /\ train_actions[1,1] = 0
    /\ train_actions[1,2] = 1
);

constraint forall (x in 1..NUM_TRAINS)(
    train_actions[x, 1] = 0
);

solve 
% satisfy;
minimize sum([
    max([getMaxIndexOfValueGeqThan(train_actions[x, ..], 1) | x in 1..NUM_TRAINS]),
    max([getMaxIndexOfValueGeqThan(driver_locations[d, ..], 1) | d in 1..NUM_DRIVERS]),
]);

output(
        [
            show2d(train_actions),
            show2d(driver_locations),
        ]
);