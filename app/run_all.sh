#!/bin/sh
git clone --depth 1 $GIT_REPO
cd $GIT_DIR
dbt deps
eval $DBT_COMMAND
python /app/app.py