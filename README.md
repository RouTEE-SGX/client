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
