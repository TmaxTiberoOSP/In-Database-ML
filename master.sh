# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

if [ -f .env ]; then
    export $(cat $proj_path/.env | sed 's/#.*//g' | xargs)
fi

pkill -15 -f kernel.kernel_master
nohup python -u -m kernel.kernel_master --port $KERNEL_MASTER_PORT > $proj_path/master.log 2>&1 &
rm -f kernel_master; ln -s ~/.kernel_master $proj_path/kernel_master