#!/bin/bash

# Number of parallel simulations
NUM_CONTAINERS=2
REPEAT=3
# Base dataset directory (host-side)
HOST_DATASET_DIR="$(pwd)/batman-dataset"

# Docker image name
IMAGE_NAME="inetmanet:gen"

# Directory inside container where simulation runs
CONTAINER_WORKDIR="/root/inetmanet-4.x-master/examples/manetrouting/batmandronenetwork"

for i in $(seq 1 $NUM_CONTAINERS); do
    # Create unique result directory on host
    HOST_RESULTS_DIR="$HOST_DATASET_DIR/dataset/results-$i"
    mkdir -p "$HOST_RESULTS_DIR"

    echo "Launching simulation container $i with results in $HOST_RESULTS_DIR"

    docker run -d  \
        -v "$HOST_RESULTS_DIR:$CONTAINER_WORKDIR/results" \
        -w "$CONTAINER_WORKDIR" \
        -u "$(id -u):$(id -g)" \
        -e "SEED=$((i * $REPEAT))"\
        --env-file ./simulation.conf\
        --name "dataset-generator-$i"\
        "$IMAGE_NAME" \
        bash ./simulate.sh
done

