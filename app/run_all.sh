#!/bin/bash
git clone $git_repo
cd $git_dir
dbt build
cd ..
python main.py