#!/usr/bin/env bash
echo 'Start to run migration loop...'

for case in rhel7_10022 rhel7_10059 rhel7_10031 rhel7_10039
do
    python $case.py
    wait
done