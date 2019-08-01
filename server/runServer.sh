#!/bin/bash

# USAGE: ./runServer.sh PORT MARK COUNT
# PORT - the initial TCP port that will be incremented for each server instance
# MARK - the initial fwmark that will be incremented for each server instance
# COUNT - the total number of server instances to run

die() { echo "$*"; exit 1; }
if [ -z "$1" ]; then die "No initial port specified"; fi
if [ -z "$2" ]; then die "No initial mark specified"; fi
if [ -z "$3" ]; then die "No server count specified"; fi

INITIALPORT=$1
INITIALMARK=$2
HOWMANY=$3

for i in `seq 1 $HOWMANY`;
do
    MARK=$INITIALMARK LD_PRELOAD=/$HOME/App-Route-Jail/mark.so /bin/node server.js > ./logs/$INITIALPORT.log $INITIALPORT &
    echo "PID $! running on port $INITIALPORT with mark $INITIALMARK"
    INITIALPORT=$((INITIALPORT + 1))
    INITIALMARK=$((INITIALMARK + 1))
done
