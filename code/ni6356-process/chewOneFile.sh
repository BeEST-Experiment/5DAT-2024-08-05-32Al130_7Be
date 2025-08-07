#!/bin/bash
# installed via conda-develop

python3 -m cryoant.apps.chewer --metadata metadata_channel$1.json --format tdms -s 1 -V 50000000 --correction 2 --onefile $2
