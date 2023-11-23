# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

pkill -15 -ef kernel.kernel_provider
python -u -m kernel.kernel_provider 127.0.0.1:8090 > $proj_path/provider.log 2>&1 &
rm -f kernel_provider; ln -s ~/.kernel_provider $proj_path/kernel_provider