# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

pkill -2 -f main.py
rm $proj_path/server.log

pkill -15 -f kernel.kernel_provider
rm $proj_path/provider.log

pkill -15 -f kernel.kernel_master
rm $proj_path/master.log