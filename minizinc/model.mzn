include "globals.mzn";


int: NUM_ACTIONS;
int: NUM_DRIVERS;
int: NUM_TRAINS;

%-------------------------------
array[1..NUM_ACTIONS] of int: D;                            % durations
array[1..NUM_ACTIONS] of 1..NUM_TRAINS: TA;                 % train assignments: which train does which task

%-------------------------------
int: TOTAL_DURATION = 2*sum(D)+1;                             % total duration

%-------------------------------
int: NUM_PRECEDENCE_CONSTRAINTS;
array[1..NUM_PRECEDENCE_CONSTRAINTS] of 1..NUM_ACTIONS: preceding;
array[1..NUM_PRECEDENCE_CONSTRAINTS] of 1..NUM_ACTIONS: anteceding;

int: NUM_TURN_CONSTRAINTS;
array[1..NUM_TURN_CONSTRAINTS] of 1..NUM_ACTIONS: before_turn;
array[1..NUM_TURN_CONSTRAINTS] of 1..NUM_ACTIONS: after_turn;

int: NUM_START_ORDER_CONSTRAINTS;
array[1..NUM_START_ORDER_CONSTRAINTS] of 1..NUM_ACTIONS: start_early;
array[1..NUM_START_ORDER_CONSTRAINTS] of 1..NUM_ACTIONS: start_later;

int: NUM_OVERLAP_CONSTRAINS;
array[1..NUM_OVERLAP_CONSTRAINS] of 1..NUM_ACTIONS: overlap_left;
array[1..NUM_OVERLAP_CONSTRAINS] of 1..NUM_ACTIONS: overlap_right;

int: NUM_DONT_STOP_CONSTRAINTS;
array[1..NUM_DONT_STOP_CONSTRAINTS] of 1..NUM_ACTIONS: dont_stop_before;
array[1..NUM_DONT_STOP_CONSTRAINTS] of 1..NUM_ACTIONS: dont_stop_after;

%-------------------------------
array[1..NUM_ACTIONS] of var 1..TOTAL_DURATION: S;          % start times
array[1..NUM_ACTIONS] of var 1..NUM_DRIVERS: DA;            % driver assignments
var 1..TOTAL_DURATION: end;                                 % total end time
%-------------------------------

% precedence constraints
constraint forall (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    (S[preceding[p]] + D[preceding[p]]) <= S[anteceding[p]]
);

% turn constraints
constraint forall (tc in 1..NUM_TURN_CONSTRAINTS)(
    (S[before_turn[tc]] + D[before_turn[tc]]) < S[after_turn[tc]]
);

% do not stop (on switches for example) constraints
constraint forall (ds in 1..NUM_DONT_STOP_CONSTRAINTS)(
    (S[dont_stop_before[ds]] + D[dont_stop_before[ds]]) = S[dont_stop_after[ds]]
);

% start order constraints, less strict than precedence
constraint forall (s in 1..NUM_START_ORDER_CONSTRAINTS)(
    S[start_early[s]] < S[start_later[s]]
);

% redundant constraint: strict precedence implies non overlap
constraint forall (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    disjunctive(
        [S[preceding[p]], S[anteceding[p]]],
        [D[preceding[p]], D[anteceding[p]]]
    )
);

% redundant constraint: turn inbetween implies non overlap
constraint forall (tc in 1..NUM_TURN_CONSTRAINTS)(
    disjunctive(
        [S[before_turn[tc]], S[after_turn[tc]]],
        [D[before_turn[tc]], D[after_turn[tc]]]
    )
);

% some task physically are not allowed to happen at the same time
constraint forall (o in 1..NUM_OVERLAP_CONSTRAINS) (
    disjunctive(
        [S[overlap_left[o]], S[overlap_right[o]]],
        [D[overlap_left[o]], D[overlap_right[o]]]
    )
);

% if the the driver needs to change train, or the train
% needs to change diver add a gap in the schedule
constraint forall (a1 in 1..(NUM_ACTIONS-1))(
    forall (a2 in (a1+1)..NUM_ACTIONS)(
        if (
            (DA[a1] != DA[a2] xor TA[a1] != TA[a2])
        ) then (
            ((S[a1] + D[a1]) < (S[a2] - 1))
            \/ ((S[a2] + D[a2]) < (S[a1] - 1))
        )
        endif
    )    
);

constraint symmetry_breaking_constraint(
    DA[1] = 1
);

constraint symmetry_breaking_constraint(
    S[1] = 1
);

% objective
constraint forall(i in 1..NUM_ACTIONS)(
    S[i] + D[i] <= end
);


solve 
::int_search(S, smallest, indomain_min)
minimize end;

output(
        [
            show(S),
            show(D),
            show(DA),
            show(TA),
        ]
);
