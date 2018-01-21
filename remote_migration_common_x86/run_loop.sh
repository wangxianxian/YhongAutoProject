#!/usr/bin/env bash
case_loop=(
rhel7_10022
rhel7_10026
rhel7_10031
rhel7_10039
rhel7_10059
)

echo "Start to run migration loop..."
PID=$$
echo "Test PID : $PID"

function kill_process()
{
    kill -9 $PID
}

trap 'kill_process' SIGINT

for case in ${case_loop[@]}
do
    python $case.py
    wait
done
