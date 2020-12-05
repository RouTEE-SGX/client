# client

## How to run `client.py`

```
$ cd client
$ mkdir key
$ mkdir experiment
$ pip3 install -r requirements.txt
```

### Make scripts
```
$ cd scripts
$ python3 makeScript.py
$ cd ..
```

### Run `client.py` console
```
$ python3 client.py
```

### Run `client.py` with script
```
$ python3 client.py script*
```

<!--
### Run `client.py` with pre-signed script
```
$ python3 client.py signed*
```
-->

### Run `client.py` with script line by line
```
$ python3 client.py < script*
```

The second way, running with line by line, is more prefered.


### Run `client.py` with pre-signed script line by line
```
$ python3 client.py < signed* signed
```

<!--
### Run `client.py` parallel
```
$ sh runScripts.sh <rounds>
```
* MUST set <rounds> .
-->

<!--
$ cd client
$ mkdir key
$ mkdir experiment 
$ cd script
$ python3 makeScript.py
0(default) 선택 -> 적절한 파라미터 입력
client의 개인키/공개키 및 대응되는 비트코인 주소, 스크립트가 자동으로 생성됨

scriptAddUser: rouTEE 내부에 초기화된 user account 추가
scriptDepositReq: 생성된 모든 account에 대해 deposit request 발생시킴
scriptDepositTx: 가상의 deposit transaction을 랜덤하게 생성 및 처리; account의 잔금이 업데이트됨
scriptPayment: 생성된 account 간에 랜덤 payment 발생
scriptSettleReq: 생성된 account를 대상으로 랜덤하게 settle request 발생
scriptUpdateSPV: 생성된 account를 대상으로 랜덤하게 SPV 블록 넘버 업데이트

$ cd ../
$ python3 client.py
client.py가 실행되면 적절한 script 파일명 입력 (ex. scriptAddUser)
각 script에 대하여, rouTEE와 정상적으로 통신 및 메시지를 수신하면 메시지 송수신 사이에 걸린 시간을 experiment 폴더 내부에 저장 (ex. paymentResult)
# 주의사항: experiment 내부에 기록되는 데이터는 이미 존재하는 파일에 append됨 
-->

<!--
fast version of `runClient.sh`

#!/bin/bash

#
# rouTEE evaluation script
# run docker image for rouTEE & run this script anywhere you want
#

# get input
echo ""
read -p "how many users: " userNumber
read -p "how many payments per client: " paymentNumber
read -p "how many clients: " clientNumber
echo ""

# make create channels script
echo "Making scripts..."
docker exec -it routee bash -c "cd && cd rouTEE/client/scripts && python3 makeScript.py 1 ${userNumber} scc${userNumber}"

# make random payments scripts concurrently
RANGE=$(seq 1 ${clientNumber})
makeScriptCmd=""
for i in $RANGE
do
	makeScriptCmd="${makeScriptCmd} cd && cd rouTEE/client/scripts && python3 makeScript.py 2 ${paymentNumber} ${userNumber} sp${userNumber}_${paymentNumber}_$i &"
done
makeScriptCmd=${makeScriptCmd% *&} # cut out string " &" at the last
docker exec -it routee bash -c "${makeScriptCmd}"

# remove previous experiment's logs
echo "\nRemoving previous experiment's logs"
docker exec -it routee bash -c "cd && cd rouTEE/client/resultLogs && rm s*"

# run create channels script & save log (2>&1: including error logs)
docker exec -it routee bash -c "cd && cd rouTEE/client && python3 client.py scc${userNumber} > resultLogs/scc${userNumber} 2>&1"

# run random payments scripts concurrently & save log (2>&1: including error logs)
paymentCmd=""
for i in $RANGE
do
	scriptName="sp${userNumber}_${paymentNumber}_$i"
	paymentCmd="${paymentCmd} cd && cd rouTEE/client && python3 client.py ${scriptName} > resultLogs/${scriptName} 2>&1 &"
done
paymentCmd=${paymentCmd% *&} # cut out string " &" at the last
echo "\nRunning payment scripts..."
docker exec -it routee bash -c "${paymentCmd}"

echo "\nAll Done!\n"
-->
