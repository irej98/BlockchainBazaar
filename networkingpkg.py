# Created 2021/03/23 01:07:01
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
import pickle

def register_peer(peers, new_address):
    in_peers = False
    for address in peers:
        if new_address == address:
            in_peers = True
            break

    if not in_peers:
        peers.add(new_address)
        print("New address registered \n")
        try:
            for peer in peers:
                data = {"new_address": peer}
                headers = {'Content-Type': "application/json"}

                # Make a request to register with remote node
                try:
                    response = requests.post("http://" + new_address + "/register",
                                             data=json.dumps(data), headers=headers)
                except:
                    pass
        except:
            pass

        return peers
    else:
        print("Address already registered \n")
        return peers
