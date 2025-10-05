
    #!/bin/sh
    docker run  --rm  -it -v "$(pwd)/3node:/root/inetmanet-4.x-master/examples/manetrouting/testnetwork" -u root inetmanet:dataset-gen-auto
