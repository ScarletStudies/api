#! /usr/bin/env bash

# initialize the database
flask db upgrade

# seed test data
flask seed_test_data

