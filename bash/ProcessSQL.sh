#!/bin/bash

#-------------------------------------------------------------
# Get the inputs
#-------------------------------------------------------------

DIRECTORY=$1
TAG=$2
if [ ! -d ${DIRECTORY} ]; then
    echo "Directory ${DIRECTORY} not found!"
    exit
fi

#-------------------------------------------------------------
# Get the input database file
#-------------------------------------------------------------

echo "Processing directory ${DIRECTORY}"
FILE=`ls -dt ${DIRECTORY}/*.db | head -n 1`
if [[ "${FILE}" == "" ]]; then
    echo "No timing database found!"
    exit
fi
echo "--> Processing ${FILE}"

#-------------------------------------------------------------
# Make the output area
#-------------------------------------------------------------

if [ ! -d ${DIRECTORY}/csv_${TAG} ]; then
    mkDIRECTORY -p ${DIRECTORY}/csv_${TAG}
else
    echo "--> Clearing previous results"
    rm ${DIRECTORY}/csv_${TAG}/*.csv
fi
echo "---> Processing batch ${TAG}"

#-------------------------------------------------------------
# Create the CSV files for each module run
#-------------------------------------------------------------

# Check what modules were run in the events
MODULES=`sqlite3 ${FILE} -separator "," "SELECT ModuleLabel FROM TimeModule" | sort | uniq`

# Process the timing for each module
for MOD in ${MODULES}; do
    echo Processing module ${MOD}
    sqlite3  -separator "," ${FILE} "SELECT Run, SubRun, Event, Time FROM TimeModule WHERE ModuleLabel='${MOD}';" >| ${DIRECTORY}/csv_${TAG}/${MOD}.csv
done

#-------------------------------------------------------------
# Create the summary timing CSV files
#-------------------------------------------------------------

# Process the input source timing
sqlite3  -separator "," ${FILE}  "SELECT Run, SubRun, Event, Time FROM TimeSource" >| ${DIRECTORY}/csv_${TAG}/OfflineFragmentReader.csv

# Process the total event timing
sqlite3  -separator "," ${FILE}  "SELECT Run, SubRun, Event, Time FROM TimeEvent" >| ${DIRECTORY}/csv_${TAG}/tot_event.csv

# split the output into every-other line, init and write
if [ -f ${DIRECTORY}/csv_${TAG}/subsystemOutput.csv ]; then
    sed -n 'p;n' ${DIRECTORY}/csv_${TAG}/subsystemOutput.csv >| ${DIRECTORY}/csv_${TAG}/subsystemOutput_init.csv
    sed -n 'n;p' ${DIRECTORY}/csv_${TAG}/subsystemOutput.csv >| ${DIRECTORY}/csv_${TAG}/subsystemOutput_write.csv
fi
