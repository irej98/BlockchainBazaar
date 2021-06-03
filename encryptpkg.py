# Created 2021/03/24 13:21:20
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

class user:

    def __init__(self, username):
        self.username = username
        self.balance = 1000

def verifyNewUser(public_key_bytes, enc_message):
    
    return False

def verifyUser(public_key_bytes, enc_message, itemid, mypubkey, action):

    return False
