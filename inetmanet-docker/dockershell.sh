
    #!/bin/sh
    docker run  --rm  -it -v "$(pwd)/batman-grid-rate:/root/inetmanet-4.x-master/examples/manetrouting/batmandronenetwork" --env-file ./simulation.conf -u root inetmanet:btw
