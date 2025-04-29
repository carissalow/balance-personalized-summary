#!/bin/bash

pids=(
    101
    102
    103
    104
    105
    106
    107
    108
    109
    110
    111
    112
    113
    114
    115
    116
    117
    118
    119
    120
    122
    123
)

for pid in "${pids[@]}" ;
do
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Rendering final study report for participant $pid"
    bash render_participant_report.sh $pid 
done

echo "[$(date '+%Y-%m-%d %H:%M:%S')] All done!"