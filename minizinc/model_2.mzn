include "globals.mzn";

int: NUM_ACTIONS;
int: NUM_DRIVERS;
int: NUM_TRAINS;

%-------------------------------
array[1..NUM_ACTIONS] of int: D;                            % durations
array[1..NUM_ACTIONS] of 1..NUM_TRAINS: acting_train;       % which train does which action 

%-------------------------------
int: TOTAL_DURATION = 2*sum(D);                             % total duration
var 0..TOTAL_DURATION: end;                                 % total end time

%-------------------------------
int: NUM_PRECEDENCE_CONSTRAINTS;
array[1..PRECEDENCES] of 1..NUM_ACTIONS: preceding;
array[1..PRECEDENCES] of 1..NUM_ACTIONS: anteceding;

int: NUM_OVERLAP_CONSTRAINS;
array[1..PRECEDENCES] of 1..NUM_ACTIONS: overlap_left;
array[1..PRECEDENCES] of 1..NUM_ACTIONS: overlap_right;

%-------------------------------
array[1..NUM_ACTIONS] of var 0..TOTAL_DURATION: S;          % start times
array[1..NUM_ACTIONS] of var 1..NUM_DRIVERS: DA;            % driver assignments

%-------------------------------




% precedence constraints
constraint forall (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    S[preceding[p]] + D[preceding[p]] <= S[anteceding[p]]
);

% redundant constraint: precedence implies non overlap
constraint (p in 1..NUM_PRECEDENCE_CONSTRAINTS)(
    disjunctive(
        [S[preceding[p]], S[anteceding[p]]],
        [D[preceding[p]], D[anteceding[p]]],
    )
);

% ensure no overlap of tasks
constraint forall(o in 1..OVERLAP_ACTION_PAIRS) (
    disjunctive(
        [S[overlap_left[o]], S[overlap_right[o]]],
        [D[overlap_left[o]], D[overlap_right[o]]],
    )
);

% Cumulative resource constraints
constraint forall ( d in 1..NUM_DRIVERS )(
        let { 
            set of int: DTasks = 
                { i | i in 1..NUM_ACTIONS where DA[i] = d },
            int: sum_dr = card(DTasks) % sum of tasks requiring driver                     
        } in (
            if DTasks != {} /\ sum_rr > 1 then
                % driver can only be in 1 train at the time,
                % so if the driver is assigned to multiple actions
                % these actions must not overlap
                cumulative(
                    [ S[i] | i in DTasks ],
                    [ D[i] | i in DTasks ],
                    [ DA[i] | i in DTasks ],
                    1
                )
            else
                true
            endif
        )
    );


% objective
constraint forall(i in 1..NUM_ACTIONS)(
    S[i] + D[i] <= end
);

solve minimize end;

output(
        [
            show2d(S),
            show2d(D),
        ]
);
