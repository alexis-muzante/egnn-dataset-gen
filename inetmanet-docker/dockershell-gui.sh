
#!/bin/sh
docker run --rm -it -v "$(pwd)/batman-grid-rate:/root/inetmanet-4.x-master/examples/manetrouting/batmandronenetwork" -v "$(pwd)/results:/root/inetmanet-4.x-master/showcases/wireless/errorrate/results" -u "$(id -u):$(id -g)" -v /tmp/.X11-unix:/tmp/.X11-unix -e DISPLAY=$DISPLAY inetmanet:gui
