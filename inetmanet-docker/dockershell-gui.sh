
#!/bin/sh
docker run --rm -it -v "$(pwd)/BATMANUDP:/root/inetmanet-4.x-master/examples/manetrouting/BATMANUDP" -u "$(id -u):$(id -g)" -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY inetmanet:sim-gui