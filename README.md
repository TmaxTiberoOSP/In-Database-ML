Python Server for In-Database Machine Learning

# Installation
```sh
# 1. Creating virtual environments
$ python3 -m venv <venv>

# 2. Active virtual environments
$ soruce <venv>/bin/activate

# 3. Install requirements
$ pip install -r requirements.txt
```

# Getting started
```sh
# Run a kernel master
./master.sh

# Run a kernel provider
# - To run the kernel provider externally, you must modify the file.
#   python -u -m kernel.kernel_provider <the kernel master address> --host <IP for external connections>
./provider.sh

# Run a python ML server
./serrver.sh
```