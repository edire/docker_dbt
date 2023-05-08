#!/bin/sh
git clone $git_repo
cd $git_dir
dbt deps
dbt build
python /app/app.py