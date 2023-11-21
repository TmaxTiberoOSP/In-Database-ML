# /bin/bash
pkill -9 -ef kernel.kernel_provider
python -u -m kernel.kernel_provider 127.0.0.1:8090