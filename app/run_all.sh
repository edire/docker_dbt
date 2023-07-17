#!/bin/sh
git clone --depth 1 $git_repo
cd $git_dir
dbt deps
eval $dbt_command
python /app/app.py