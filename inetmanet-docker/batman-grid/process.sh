#!/bin/bash
source /root/omnetpp/setenv

source /root/inetmanet-4.x-master/setenv          

source utils/generateini.sh

generate_config omnetpp_substitution.ini omnetpp.ini

mkdir -p topology

# Generate network positions
echo "Generating network positions for seed ${SEED} with Betweeness Threshold ${BTW_TH}..."

python3 utils/generate_network_positions.py ${numTX} ${numRX} ${numRXTX} ${numRelay} ${area} ${SEED} 1000 ${BTW_TH} ${repeat} topology/positions-${SEED}.ini

echo 'Simulando'
echo "Seed:${SEED}"
cat topology/positions-${SEED}.ini >> omnetpp.ini
inet 
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
