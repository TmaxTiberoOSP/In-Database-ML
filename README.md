Python Server for In-Database Machine Learning

# Installation
```sh
# 1. Creating virtual environments
$ python3 -m venv <venv>

# 2. Active virtual environments
$ source <venv>/bin/activate

# 3. Install requirements
$ pip install -r requirements.txt
```

# Getting started
```sh
# Confiture environment
cat << EOT > .env
# Server
HOST=127.0.0.1
PORT=3000

# DB (see $TB_HOME/client/config/tbdsn.tbr)
JDBC_DRIVER=/path/to/tibero-jdbc.jar
DB_HOST=127.0.0.1
DB_PORT=8629
DB_NAME=tibero
DB_USER=tibero
DB_PASSWD=tmax

# Kernel
KERNEL_MASTER_HOST=127.0.0.1
KERNEL_MASTER_PORT=8080
EOT

# Run a kernel master
./master.sh

# Run a kernel provider
# - To run the kernel provider externally, you must modify the file.
#   python -u -m kernel.kernel_provider <the kernel master address> --host <IP for external connections>
./provider.sh

# Run a python ML server
./serrver.sh

# Run all server
./run.sh

# Stop all server & Clear log
./clear.sh
```