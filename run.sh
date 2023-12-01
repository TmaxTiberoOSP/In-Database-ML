# /bin/bash
path=`readlink -f "${BASH_SOURCE:-$0}"`
proj_path=`dirname $path`

$proj_path/master.sh
$proj_path/provider.sh
$proj_path/server.sh