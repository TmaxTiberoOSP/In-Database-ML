# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

pkill -15 -ef kernel.kernel_master
nohup python -u -m kernel.kernel_master > $proj_path/master.log 2>&1 &
rm -f kernel_master; ln -s ~/.kernel_master $proj_path/kernel_master