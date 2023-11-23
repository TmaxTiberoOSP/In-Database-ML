# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

pkill -2 -f main.py
nohup python -u ./main.py > $proj_path/server.log 2>&1 &