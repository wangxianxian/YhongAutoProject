#!/usr/bin/env bash
utils_list=(
pexpect
nc
bridge-utils
)

for utils in ${utils_list[@]}
do
    echo -e "\n==========>>>>>>>>>Installing package $utils "
    echo -e "**************************************************************************"
    yum install -y $utils
    wait
    echo -e "**************************************************************************"
done

for utils in ${utils_list[@]}
do
    echo -e "\n==========>>>>>>>>>Checking package $utils "
    echo -e "**************************************************************************"
    yum list installed | grep $utils
    wait
    echo -e "**************************************************************************"
done