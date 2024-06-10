include "globals.mzn";

int: NUM_ACTIONS;
int: NUM_DRIVERS;
int: NUM_TRAINS;

%-------------------------------
array[1..NUM_ACTIONS] of int: D;                            % durations
array[1..NUM_ACTIONS] of 1..NUM_TRAINS: TA;                 % train assignments: which train does which task

%-------------------------------
int: TOTAL_DURATION = 2*sum(D);                             % total duration
var 0..TOTAL_DURATION: end;                                 % total end time

%-------------------------------
int: NUM_PRECEDENCE_CONSTRAINTS;
array[1..NUM_PRECEDENCE_CONSTRAINTS] of 1..NUM_ACTIONS: preceding;
array[1..NUM_PRECEDENCE_CONSTRAINTS] of 1..NUM_ACTIONS: anteceding;

int: NUM_START_ORDER_CONSTRAINTS;
array[1..NUM_START_ORDER_CONSTRAINTS] of 1..NUM_ACTIONS: start_early;
array[1..NUM_START_ORDER_CONSTRAINTS] of 1..NUM_ACTIONS: start_later;

int: NUM_OVERLAP_CONSTRAINS;
array[1..NUM_OVERLAP_CONSTRAINS] of 1..NUM_ACTIONS: overlap_left;
array[1..NUM_OVERLAP_CONSTRAINS] of 1..NUM_ACTIONS: overlap_right;

%-------------------------------
array[1..NUM_ACTIONS] of var 0..TOTAL_DURATION: S;          % start times
array[1..NUM_ACTIONS] of var 1..NUM_DRIVERS: DA;            % driver assignments

%-------------------------------

% precedence constraints
constraint forall (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    if (
        DA[preceding[p]] != DA[anteceding[p]] xor TA[preceding[p]] != TA[anteceding[p]] 
    ) then (
        (S[preceding[p]] + D[preceding[p]]) < S[anteceding[p]]
    ) else (
        (S[preceding[p]] + D[preceding[p]]) <= S[anteceding[p]]
    )
    endif
);

% start order constraints, less strict than precedence
constraint forall (s in 1..NUM_START_ORDER_CONSTRAINTS)(
    if (
        DA[start_early[s]] != DA[start_later[s]] 
        /\ TA[start_early[s]] != TA[start_later[s]] 
    ) then (
        S[start_early[s]] < S[start_later[s]]
    ) else (
        (S[start_early[s]] + D[start_early[s]]) < S[start_later[s]]
    )
    endif    
);

% redundant constraint: precedence implies non overlap
constraint forall (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    disjunctive(
        [S[preceding[p]], S[anteceding[p]]],
        [D[preceding[p]], D[anteceding[p]]]
    )
);

% ensure no overlap of tasks
constraint forall (o in 1..NUM_OVERLAP_CONSTRAINS) (
    disjunctive(
        [S[overlap_left[o]], S[overlap_right[o]]],
        [D[overlap_left[o]], D[overlap_right[o]]]
    )
);

% % if the the driver needs to change train, or the train
% % needs to change diver add a gap in the schedule
% constraint forall (a1 in 1..(NUM_ACTIONS-1))(
%     forall (a2 in (a1+1)..NUM_ACTIONS)(
%         if (
%             (DA[a1] = DA[a2] /\ TA[a1] != TA[a2])
%             \/ (DA[a1] != DA[a2] /\ TA[a1] == TA[a2])
%         ) then (
%             (S[a1] + D[a1] < S[a2])
%             \/ (S[a2] + D[a2] < S[a1])
%         )
%         endif
%     )    
% );

constraint symmetry_breaking_constraint(
    DA[1] = 1
);

% objective
constraint forall(i in 1..NUM_ACTIONS)(
    S[i] + D[i] <= end
);

solve minimize end;

output(
        [
            show(S),
            show(D),
            show(DA),
            show(TA)
        ]
);
