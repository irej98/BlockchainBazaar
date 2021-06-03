# Created 2021/03/23 01:07:38
# Author: Jeri

# Imports
from hashlib import sha256
import json
import time

from flask import Flask, request
import requests

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils
from cryptography.hazmat.backends import default_backend

import subprocess
import pickle  # for saving and loading blockchain object

from blockchainpkg import *
from networkingpkg import *
from encryptpkg import *


app = Flask(__name__)


# ----------------------------------------------------------------------------
# Blockchain Package Calls
# ----------------------------------------------------------------------------

# Get the chain
@app.route('/chain', methods=['GET'])
def get_chain():
    print('Getting local chain...\n')
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return json.dumps({"length": len(chain_data),
                       "chain": chain_data,
                       "peers": list(peers)})+"\n"+"\n"


# Get the last block
@app.route('/lastblock', methods=['GET'])
def get_last_block():
    print('Getting last block...\n')
    lastblock = blockchain.last_block
    return json.dumps({"last block": lastblock.__dict__})+"\n"+"\n"


# Get the list of items
@app.route('/items', methods=['GET'])
def get_items():
    print('Getting item list...\n')
    return blockchain.items


# Get the list of users and balances
@app.route('/users', methods=['GET'])
def get_users():
    print('Getting user list...\n')
    return blockchain.users


# endpoint to submit a new transaction. This will be used by
# our application to add new data (posts) to the blockchain
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    print('Received new transaction data...\n')
    tx_data = request.get_json()
    required_fields = ["itemid", "username", "action", "securityHash", "source", "price"]

    for field in required_fields:
        if not tx_data.get(field):
            print("Invalid transaction data")
            return "Invalid transaction data. Required {} field missing.".format(field)+"\n"+"\n", 404



    # check that transaction comes from actual person
    # decrypt securityHash with mypubkey
    # string should be "{itemid}_{mypubkey}_{action}"
    # --- here


    # check that transaction is not repeated (check for securityHash in transaction history)
    # first check confirnmed_transactions
    for transaction in blockchain.confirmed_transactions:
        if transaction["securityHash"] == tx_data["securityHash"]:
            return "Invalid transaction data. Transaction already exists."+"\n"+"\n", 404
    # check unconfirmed_transactions
    for transaction in blockchain.unconfirmed_transactions:
        if transaction["securityHash"] == tx_data["securityHash"]:
            return "Invalid transaction data. Transaction already exists."+"\n"+"\n", 404


    # check action is valid
    # if action == 1: listing products
    # if action == 2: purchasing product
    # if action == 3: delivering product
    if (tx_data["action"] != 1) and (tx_data["action"] != 2) and (tx_data["action"] != 3):
        return "Invalid transaction data. Invalid action."+"\n"+"\n", 404

    # source is 1 if this is the device that user is typing in transaction. This is to avoid differnt timestamps on the machiens
    # if source == 1 fill in following fields:
    # if source == 0 don't fill in
    if tx_data['source'] == 1:
        tx_data["timestamp"] = time.time()
        tx_data["source"] == 0
    elif tx_data["source"] == 0:
        pass
    else:
        print("Invalid transaction data. Source field missing."+"\n")
        return "Invalid transaction data. Source field missing."+"\n"+"\n", 404




    # Add transaction to unconfirmed transaction
    print("Adding new transaction...")
    blockchain.add_new_transaction(tx_data)

    # Pass on tx_data to all peers
    for peer in peers:
        if (peer != str(host)+":"+str(port)) and (peer != "127.0.0.1:"+str(port)) and (peer != "localhost:"+str(port)):
            headers = {'Content-Type': "application/json"}

            # Make a request to post a new transaction to peer
            response = requests.post("http://" + peer + "/new_transaction",
                                     data=json.dumps(tx_data), headers=headers)
            print(response)

    # blockchain should mine (if there are 3 unconfirmed transactions???)
    mine_unconfirmed_transactions()






    print("Success\n")
    return "Success"+"\n"+"\n", 201


# endpoint to get pending unconfirmed_transactions
@app.route('/pending', methods=['GET'])
def get_pending_tx():
    print('Getting unconfirmed transaction data...\n')
    print(json.dumps(blockchain.unconfirmed_transactions))
    return json.dumps(blockchain.unconfirmed_transactions)


# endpoint to request the node to mine the unconfirmed
# transactions (if any). We'll be using it to initiate
# a command to mine from our application itself.
@app.route('/mine', methods=['GET'])
def mine_unconfirmed_transactions():
    print('Mining unconfirmed transactions...\n')
    result = blockchain.mine()
    if not result:
        print('No transactions to mine\n')
        return "No transactions to mine \n"+"\n"
    print("Block #{} is mined.\n".format(result))

    for peer in peers:
        requests.get("http://" + peer + "/update_chain")

    return "Block #{} is mined.".format(result)+"\n"+"\n"


# ----------------------------------------------------------------------------
# Networking Package Calls
# ----------------------------------------------------------------------------

# call to register new node
@app.route('/register', methods=['POST'])
def register():
    global peers
    global host
    global port

    new_address = request.get_json()["new_address"]
    if not new_address:
        return "Invalid data", 400

    # call register_peer from networkingpkg
    peers = register_peer(peers, new_address)

    # Add function call to see if chain of new peer is longer and valid
    update_chain()

    return "Registration complete \n"  # + str(response.status_code) + "\n"


@app.route('/get_peers', methods=['GET'])
def get_peers():
    """
    Print peers
    """
    print('Getting peers addresses...\n')
    return "Peers: {}".format(peers)+"\n"


@app.route('/update_chain', methods=['GET'])
def update_chain():
    global blockchain

    for peer in peers:
        print("Updating chain..."+"\n")
        print("Getting peer chain from {}...".format(peer))
        response_new = requests.get("http://" + peer + "/chain")
        print("Length: ")
        print(response_new.json()['length'])
        print("Getting local chain length")
        response_local_length = len(blockchain.chain)
        print(response_local_length)

        if response_new.json()['length'] > response_local_length:
            print("New chain longer than current. Checking validity..."+"\n")
            chain_new = response_new.json()['chain']
            blockchain_new = create_chain_from_dump(chain_new)
            if blockchain.check_chain_validity(blockchain_new):
                blockchain = blockchain_new
                print("New blockchain is valid.")
            else:
                print("New blockchain is not valid.")

    return "Chain updated."+"\n"


@app.route('/add_user', methods=['POST'])
def add_user():
    global blockchain
    return "User addition successful. \n"









# Create nodes copy of blockchain
blockchain = Blockchain()
blockchain.create_genesis_block()

# address of other members of network
peers = set()
# peers = {}


print("Enter host ip to run on (leave blank to run locally): ")
host = str(input())
print("Enter port to run on: ")
port = int(input())
print("Enter user id: ")
userid = str(input())

if not host:
    peers.add("localhost:" + str(port))
else:
    peers.add(str(host) + ":" + str(port))


app.run(debug=False, port=port, host=host)
# To use flask on local network (debug must be disabled):
# , host='0.0.0.0') or can put actual IP from ifconfig
