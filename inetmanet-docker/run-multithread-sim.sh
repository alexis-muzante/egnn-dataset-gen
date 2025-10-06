#!/bin/bash

# Number of parallel simulations
NUM_CONTAINERS=5
REPEAT=3
# Base dataset directory (host-side)
HOST_DATASET_DIR="$(pwd)/batman-dataset"
HOST_TOPOLOGY_DIR="$(pwd)/batman-dataset/topology"
# Docker image name
IMAGE_NAME="inetmanet:btw"

# Directory inside container where simulation runs
CONTAINER_WORKDIR="/root/inetmanet-4.x-master/examples/manetrouting/batmandronenetwork"

for i in $(seq 1 $NUM_CONTAINERS); do
    # Create unique result directory on host
    HOST_RESULTS_DIR="$HOST_DATASET_DIR/dataset/results-$i"
    mkdir -p "$HOST_RESULTS_DIR"

    echo "Launching simulation container $i with results in $HOST_RESULTS_DIR"
    result=$(echo "0.05 * 1" | bc)

    docker run -d --rm  \
        -v "$HOST_RESULTS_DIR:$CONTAINER_WORKDIR/results" \
        -v "$HOST_TOPOLOGY_DIR:$CONTAINER_WORKDIR/topology" \
        -w "$CONTAINER_WORKDIR" \
        -e "SEED=$((i * $REPEAT))"\
        -e "BTW_TH=$result"\
        --env-file ./simulation.conf\
        --name "dataset-generator-$i"\
        "$IMAGE_NAME" \
        bash ./simulate.sh
done
