from tqdm import tqdm
import random
import sys
from bitcoinaddress import Address, Key
import os.path
import csv
import codecs
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15

def base58(address_hex):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    b58_string = ''
    # Get the number of leading zeros
    # leading_zeros = len(address_hex) - len(address_hex.lstrip('0'))
    leading_zeros = 0
    # Convert hex to decimal
    address_int = int(address_hex, 16)
    # Append digits to the start of string
    while address_int > 0:
        digit = address_int % 58
        digit_char = alphabet[digit]
        b58_string = digit_char + b58_string
        address_int //= 58
    # Add ‘1’ for each 2 leading zeros
    ones = leading_zeros // 2
    for one in range(ones):
        b58_string = '1' + b58_string
    return b58_string

# encryption/decryption setting
KEY_SIZE = 16 # bytes
MAC_SIZE = 16 # bytes
NONCE_SIZE = 12 # bytes

# print byte array
def print_hex_bytes(name, byte_array):
    # print('{} len[{}]: '.format(name, len(byte_array)), end='')
    for idx, c in enumerate(byte_array):
        # print("{:02x}".format(int(c)), end='')
        pass
    # print("")

# generate random key
def gen_random_key():
    return get_random_bytes(KEY_SIZE)

# generate random nonce (= Initialization Vector, IV)
def gen_random_nonce():
    return get_random_bytes(NONCE_SIZE)

# AES-GCM encryption
def enc(key, aad, nonce, plain_data):

    # AES-GCM cipher
    cipher = AES.new(key, AES.MODE_GCM, nonce)

    # add AAD (Additional Associated Data)
    # cipher.update(aad)

    # encrypt plain data & get MAC tag
    cipher_data = cipher.encrypt(plain_data)
    mac = cipher.digest()
    return cipher_data, mac

# AES-GCM decryption
def dec(key, aad, nonce, cipher_data, mac):

    # AES128-GCM cipher
    cipher = AES.new(key, AES.MODE_GCM, nonce)
    
    # add AAD (Additional Associated Data)
    # cipher.update(aad)

    try:
        # try decrypt
        plain_data = cipher.decrypt_and_verify(cipher_data, mac)
        return plain_data
    except ValueError:
        # ERROR: wrong MAC tag, data is contaminated
        return None

def executeCommand(command):
    # print(command)
    isForDeposit = False

    # secure command option
    if command[0] == 't':
        isSecure = True
        # OP_GET_READY_FOR_DEPOSIT
        if command[2] == 'v':
            isForDeposit = True
    else:
        isSecure = False
        if command[0] == 'r':
            isForDeposit = True

    split_command = command.split(" ")
    #print(split_command)

    # commnad's last string means message sender 
    user = split_command[-1]

    if isSecure:
        # remove 't ' from command
        command = " ".join(split_command[1:-1])
    else:
        command = " ".join(split_command[:-1])

    # encode command
    command = command.encode('utf-8')

    # encryption using RSA
    try:
        with open("../key/private_key_{}.pem".format(user), "rb") as f:
            sk = RSA.import_key(f.read())
        with open("../key/public_key_{}.pem".format(user), "rb") as f:
            vk = RSA.import_key(f.read())
    except:
        print("no user key")
        exit()

    if isForDeposit:
        pubkey = (vk.n).to_bytes(384, 'little')
        pubkey_hex = pubkey.hex()
        # print(pubkey_hex)
        message = command + b" " + pubkey
    else:
        hash = SHA256.new(command)
        # print(hash.digest().hex())
        sig = pkcs1_15.new(sk).sign(hash)
        message = command + b" " + sig

        try:
            pkcs1_15.new(vk).verify(hash, sig)
        except:
            print("bad signature")
            exit()

    if isSecure:
        # execute secure_command
        return secure_command(message, user)
    else:
        return message

def secure_command(message, sessionID):
    # encrypt command with (hardcoded) symmetric key
    key = bytes([0x0,0x1,0x2,0x3,0x4,0x5,0x6,0x7,0x8,0x9,0xa,0xb,0xc,0xd,0xe,0xf])
    aad = bytes([0])
    nonce = gen_random_nonce()
    # print("plain text command:", command[2:])
    enc_cmd, mac = enc(key, aad, nonce, message)
    secure_cmd = mac + nonce + enc_cmd
    secure_cmd = ("p {} ".format(sessionID)).encode('utf-8') + secure_cmd
    return secure_cmd

# Generate ECC private key, public key and bitcoin address
def makeNewAddresses(addressNumber):
    with open("scriptAddress", "wt") as f:
        for i in tqdm(range(addressNumber)):

            userID = "user" + format(i, '03')

            private_key = RSA.generate(3072)
            public_key = private_key.publickey()

            with open("../key/private_key_{}.pem".format(userID), "wb") as f1:
                f1.write(private_key.export_key('PEM'))
            with open("../key/public_key_{}.pem".format(userID), "wb") as f2:
                f2.write(public_key.export_key('PEM'))

            key = Key()
            key.generate()

            address = Address(key)
            address._generate_publicaddress1_testnet()
            
            f.write("{}\n".format(address.pubaddr1_testnet))

# Script for generating rouTEE accounts
def makeNewAccounts(accountNumber):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return
    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)
    count = 0
    with open("scriptAddUser", "wt") as fscript, open("signedAddUser", "w") as fsigned:
        for address in tqdm(rdr):
            sender_address = address[0]
            settle_address = sender_address
            userID = "user" + format(rdr.line_num - 1, '03')
            command = "t v {} {} {}".format(sender_address, settle_address, userID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

            count = count + 1
            if count == accountNumber:
                break

# Script for generating deposit requests
def getReadyForDeposit(accountNumber):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return
    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)
    count = 0
    with open("scriptDepositReq", "wt") as fscript, open("signedDepositReq", "w") as fsigned:
        for address in tqdm(rdr):
            user_address = address[0]
            userID = "user" + format(rdr.line_num - 1, '03')        
            command = "t j {} {}".format(user_address, userID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

            count = count + 1
            if count == accountNumber:
                break

# Script for managing deposit transactions
# Should be used only for testing
def dealWithDepositTxs(accountNumber):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return
    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)
    count = 0
    with open("scriptDepositTx", "wt") as fscript, open("signedDepositTx", "w") as fsigned:
        for address in tqdm(rdr):
            user_address = address[0]
            userID = "user" + format(rdr.line_num - 1, '03')         
            command = "r {} 0 100000000 100 {}".format(user_address, userID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

            count = count + 1
            if count == accountNumber:
                break

# Script for payments among users
def doMultihopPayments(paymentNumber, batchSize):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return

    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)
    #accountNum = sum(1 for row in rdr)

    address_list = []
    for address in rdr:
        address_list.append(address[0])

    with open("scriptPayment{}".format(batchSize), "wt") as fscript, open("signedPayment{}".format(batchSize), "w") as fsigned:
        for i in tqdm(range(paymentNumber)):
            sender_index = random.randint(0, len(address_list) - 1)
            receiver_indexes = []
            while True:
                receiver_index = random.randint(0, len(address_list) - 1)
                if (sender_index != receiver_index) and (receiver_index not in receiver_indexes):
                    receiver_indexes.append(receiver_index)
                if len(receiver_indexes) == batchSize:
                    break

            sender_address = address_list[sender_index]
            # receiver_address = address_list[receiver_index]
            senderID = "user" + format(sender_index, '03')
            command = "t m {} {} ".format(sender_address, batchSize)  
            for i in range(batchSize):
                receiver_address = address_list[receiver_indexes[i]]
                command += "{} 100 ".format(receiver_address)
            command += "10 {}".format(senderID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

# Script for generating settle requests
def settleBalanceRequest(settleTxNumber):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return

    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)
    count = 0
    # address_list = []
    # for address in rdr:
    #     address_list.append(address[0])

    with open("scriptSettleReq", "wt") as fscript, open("signedSettleReq", "w") as fsigned:
        # for i in tqdm(range(settleTxNumber)):
        #     user_index = random.randint(0, len(address_list) - 1)

        #     user_address = address_list[user_index]
        #     userID = "user" + format(user_index, '03')
        for address in tqdm(rdr):
            user_address = address[0]
            userID = "user" + format(rdr.line_num - 1, '03') 

            command = "t l {} 100000 {}".format(user_address, userID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

            count = count + 1
            if count == settleTxNumber:
                break

# Script for updating boundary block number
def updateLatestSPV(updateSPVNumber):
    if not os.path.exists("scriptAddress"):
        print("execute makeNewAddresses first\n")
        return

    addressFile = open("scriptAddress", 'r')
    rdr = csv.reader(addressFile)

    # address_list = []
    # for address in rdr:
    #     address_list.append(address[0])

    with open("scriptUpdateSPV", "wt") as fscript, open("signedUpdateSPV", "w") as fsigned:
        # for i in tqdm(range(updateSPVNumber)):
            # user_index = random.randint(0, len(address_list) - 1)

            # user_address = address_list[user_index]
            # userID = "user" + format(user_index, '03')
        for address in tqdm(rdr):
            user_address = address[0]
            userID = "user" + format(rdr.line_num - 1, '03') 

            command = "t q {} 3000 {}".format(user_address, userID)
            fscript.write(command + "\n")

            signedCommand = executeCommand(command)
            # fsigned.write(signedCommand)
            fsigned.write(signedCommand.hex())
            fsigned.write('\n')

if __name__ == '__main__':

    # if there is sys.argv input from command line, run a single script
    if len(sys.argv) >= 2:
        command = int(sys.argv[1])
    else:
        command = eval(input("which script do you want to make (0: default / 1: makeNewAddresses / 2: makeNewAccounts / 3: getReadyForDeposit & dealWithDepositTxs / 4: doMultihopPayments / 5: settleBalanceRequest / 6: updateLatestSPV)): "))
    
    if command == 1:
        if len(sys.argv) >= 2:
            addressNumber = int(sys.argv[2])
            scriptName = sys.argv[3]
        else:
            addressNumber = eval(input("how many bitcoin addresses to generate: "))
            scriptName = "scriptAddress"
        makeNewAddresses(addressNumber)

    elif command == 2:
        if len(sys.argv) >= 2:
            accountNumber = int(sys.argv[2])
            scriptName = sys.argv[3]
        else:
            accountNumber = eval(input("how many routee accounts to generate: "))
            scriptName = "scriptAccount"
        makeNewAccounts(accountNumber)

    elif command == 3:
        if len(sys.argv) >= 2:
            depositNumber = int(sys.argv[2])
            scriptName = sys.argv[3]
        else:
            depositNumber = eval(input("how many routee deposits to generate: "))
            scriptName = "scriptDeposit"
        getReadyForDeposit(depositNumber)
        dealWithDepositTxs(depositNumber)

    elif command == 4:
        if len(sys.argv) >= 2:
            paymentNumber = int(sys.argv[2])
            batchSize = int(sys.argv[3])
            scriptName = sys.argv[4]
        else:
            paymentNumber = eval(input("how many rouTEE payments to generate: "))
            batchSize = eval(input("how many transactions per payment request (batch size): "))
            scriptName = "scriptPayment"
        doMultihopPayments(paymentNumber, batchSize)

    elif command == 5:
        if len(sys.argv) >= 2:
            settleRequestNumber = int(sys.argv[2])
            scriptName = sys.argv[3]
        else:
            settleRequestNumber = eval(input("how many rouTEE settle balance requests to generate: "))
            scriptName = "scriptSettle"
        settleBalanceRequest(settleRequestNumber)

    elif command == 6:
        if len(sys.argv) >= 2:
            updateSPVNumber = int(sys.argv[2])
            scriptName = sys.argv[3]
        else:
            updateSPVNumber = eval(input("how many rouTEE SPV block updates to generate: "))
            scriptName = "scriptUpdateSPV"
        updateLatestSPV(updateSPVNumber)

    elif command == 0:
        # accountNumber = eval(input("how many routee accounts to generate: "))
        # makeNewAddresses(accountNumber)
        # makeNewAccounts(accountNumber)
        depositNumber = eval(input("how many routee deposits to generate: "))
        paymentNumber = eval(input("how many rouTEE payments to generate: "))
        batchSize = eval(input("how many transactions per payment request (batch size): "))
        settleRequestNumber = eval(input("how many rouTEE settle balance requests to generate: "))
        getReadyForDeposit(depositNumber)
        dealWithDepositTxs(depositNumber)
        doMultihopPayments(paymentNumber, batchSize)
        settleBalanceRequest(settleRequestNumber)

        # updateSPVNumber = eval(input("how many rouTEE SPV block updates to generate: "))
        # updateLatestSPV(updateSPVNumber)

        scriptName = "scriptForAll"

    print("make script [", scriptName, "] Done")
