#!/bin/sh
git clone --depth 1 $git_repo
cd $git_dir
dbt deps
dbt build
python /app/app.py