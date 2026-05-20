#!/bin/bash
source /root/omnetpp/setenv

source /root/inetmanet-4.x-master/setenv          

source utils/generateini.sh

START=0
echo $repeat
END=$(($repeat - 1))

for RUN_ID in $(seq $START $END); do
    cd results
    echo $RUN_ID
    pwd
    opp_scavetool x "General-#${RUN_ID}.sca" "General-#${RUN_ID}.vec" -o "results-${RUN_ID}.csv"
    rm General-#${RUN_ID}.sca
    rm General-#${RUN_ID}.vec
    rm General-#${RUN_ID}.vci
    cd ..
done
cd results
rm *.sca
rm *.vec
rm *.vci
cd ..

python3 utils/log_parser.py
