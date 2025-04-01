
#!/bin/sh
docker run --rm  -it -v "$(pwd)/3node:/root/inetmanet-4.x-master/examples/manetrouting/testnetwork" -u "$(id -u):$(id -g)" inetmanet:sim
