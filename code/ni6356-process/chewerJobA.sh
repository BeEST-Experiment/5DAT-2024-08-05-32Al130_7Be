#!/bin/bash

files=$(basename -a .root/in/Data-CRONOS/summer2024/"$1"/*Sig_A.tdms)

cd "$1"
#: Parallel chewing of *different* files at once (reopening per channel)
#: -u ungroups output so it prints as it goes
parallel -u -j 36 "`realpath ../chewOneFile.sh` 0 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 1 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 2 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 3 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 4 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 5 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 6 {}" ::: $files
parallel -u -j 36 "`realpath ../chewOneFile.sh` 7 {}" ::: $files
echo "Chewing done for $1 A"

files=$(basename -a .root/in/Data-CRONOS/summer2024/"$1"/*Sig_B.tdms)

parallel -j 36 "`realpath ../chewOneFile.sh` 8 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 9 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 10 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 11 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 12 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 13 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 14 {}" ::: $files
parallel -j 36 "`realpath ../chewOneFile.sh` 15 {}" ::: $files
echo "Chewing done for $1 B"
