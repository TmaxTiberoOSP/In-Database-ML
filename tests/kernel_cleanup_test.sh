# !/bin/bash

echo -n "TEST 1: ML server exit..."

pkill -9 -f 'python -u'; pkill -9 -f 'python kernel'
./master.sh; ./provider.sh; ./server.sh;
sleep 1
curl -X 'POST' \
  'http://localhost:3000/kernels/' \
  -H 'accept: application/json' \
  -d '' -s > /dev/null
curl -X 'POST' \
  'http://localhost:3000/kernels/' \
  -H 'accept: application/json' \
  -d '' -s > /dev/null
sleep 1
pkill -2 -f main.py
sleep 1

if [ `ps -ef | grep 'python kernel' | wc -l` -eq 1 ]; then
    echo "OK"
else
    echo "FAIL"
fi


echo -n "TEST 2: kernel provider exit..."

pkill -9 -f 'python -u'; pkill -9 -f 'python kernel'
./master.sh; ./provider.sh; ./server.sh
sleep 1
curl -X 'POST' \
  'http://localhost:3000/kernels/' \
  -H 'accept: application/json' \
  -d '' -s > /dev/null
curl -X 'POST' \
  'http://localhost:3000/kernels/' \
  -H 'accept: application/json' \
  -d '' -s > /dev/null
sleep 1
pkill -15 -f kernel.kernel_provider
sleep 1

if [ `ps -ef | grep 'python kernel' | wc -l` -eq 1 ]; then
    echo "OK"
else
    echo "FAIL"
fi