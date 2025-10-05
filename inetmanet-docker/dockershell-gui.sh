
#!/bin/sh
docker run --rm -it -v "$(pwd)/gui-debug:/root/inetmanet-4.x-master/examples/manetrouting/testnetwork" -u "$(id -u):$(id -g)" -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY inetmanet:gui
