#!/usr/bin/env bash
case_loop=(
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
rhel7_exam
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
