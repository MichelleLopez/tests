#!/bin/bash

# Displays usage
display_usage() {
    echo "This script initializes the Django server with gunicorn."
    echo -e "\nUsage: $0 [IPADDR] [PORT] \n"
}


# Check if help was supplied
if [[ ($1 == "--help") ||  $1 == "-h" ]]
then
    display_usage
    exit 0
fi

# Get and parse parameters
ip=$1
port=$2

if [[ -z $1 ]]
then
    ip=127.0.0.1
    port=8000
fi

if [[ -z $2 ]]
then
    port=8000
fi

# Start gunicorn
gunicorn webserver.wsgi $ip:$port