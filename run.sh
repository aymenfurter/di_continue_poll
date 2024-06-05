#!/bin/bash

# Step 1: Analyze and get the continuation token.
token=$(python3 main.py analyze | grep 'Continuation Token' | awk '{print $3}')
echo "Continuation Token: ${token:0:15} ..."

# Step 2: Read the data using the continuation token in a new process.
python3 main.py read --token "$token"
