#! /usr/bin/env bash

# let the DB start
sleep 5;

# initialize the database
flask db upgrade

# add test data
if [ -z "$E2E" ]; then
   flask seed_test_data
fi
 
