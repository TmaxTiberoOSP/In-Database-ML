# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

if [ -f .env ]; then
    export $(cat $proj_path/.env | sed 's/#.*//g' | xargs)
fi

pkill -15 -f kernel.kernel_provider
python -u -m kernel.kernel_provider $KERNEL_MASTER_HOST:$KERNEL_MASTER_PORT > $proj_path/provider.log 2>&1 &
rm -f kernel_provider; ln -s ~/.kernel_provider $proj_path/kernel_provider