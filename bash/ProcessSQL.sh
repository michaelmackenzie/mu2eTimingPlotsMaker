#!/bin/bash

DIRECTORY=$1
TAG=$2
if [ ! -d ${DIRECTORY} ]; then
    echo "Directory ${DIRECTORY} not found!"
    exit
fi


for dd in $1/*
do
    dir=$dd
    echo "Processing directory $dir"
    for FILE in ${dd}/*.db
    do
        echo "--> Processing $FILE"

        if [ ! -d $dir/csv_${TAG} ]; then
            mkdir -p $dir/csv_${TAG}
        else
            echo "--> Clearing previous results"
            rm $dir/csv_${TAG}/*.csv
        fi
        echo "---> Processing batch ${TAG}"

        # Check what modules were run in the events
        module_list=`sqlite3 ${FILE} -separator "," "SELECT ModuleLabel FROM TimeModule" | sort | uniq`

        # Process the timing for each module
        for mod in ${module_list}; do
            echo Processing module $mod
            sqlite3  -separator "," $FILE "SELECT Run, SubRun, Event, Time FROM TimeModule WHERE ModuleLabel='${mod}';" >| $dir/csv_${TAG}/$mod.csv
        done

        # Process the input source timing
        sqlite3  -separator "," $FILE  "SELECT Run, SubRun, Event, Time FROM TimeSource" >| $dir/csv_${TAG}/OfflineFragmentReader.csv

        # Process the total event timing
        sqlite3  -separator "," $FILE  "SELECT Run, SubRun, Event, Time FROM TimeEvent" >| $dir/csv_${TAG}/tot_event.csv

        # split the output into every-other line, init and write
        if [ -f $dir/csv_${TAG}/subsystemOutput.csv ]; then
            sed -n 'p;n' $dir/csv_${TAG}/subsystemOutput.csv >| $dir/csv_${TAG}/subsystemOutput_init.csv
            sed -n 'n;p' $dir/csv_${TAG}/subsystemOutput.csv >| $dir/csv_${TAG}/subsystemOutput_write.csv
        fi
    done
done
