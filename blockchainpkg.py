# Created 2020/11/25 17:09:11
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


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, nonce=0):
        """
        Constructor for the `Block` class.
        index: Unique ID of the block.
        transactions: List of transactions.
        timestamp: Time of generation of the block.
        """
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce

    def compute_hash(self):
        """
        Hash the block and return a string
        """
        block_string = json.dumps(self.__dict__, sort_keys=True)
        return sha256(block_string.encode()).hexdigest()


class Blockchain:
    # difficulty of PoW algorithm
    difficulty = 2

    def __init__(self):
        self.chain = []
        self.unconfirmed_transactions = []  # data yet to get into blockchain
        self.confirmed_transactions = [] # data in the blockchain

        # dictionary where keys are usernames and values are public encryption keys
        self.users = {}
        # dictionary where keys are usernames and values are dictionaries with account type and account balances.
        self.accounts = {}
        # dictionary containing items for sale, keys are itemid values are dictionaries containing
        self.items = {}

    def create_genesis_block(self):
        """
        A function to generate genesis block and appends it to
        the chain. The block has index 0, previous_hash as 00, and
        a valid hash.
        """
        #
        genesis_block = Block(0, [], 0, "00", 0)
        # genesis_block.hash = genesis_block.compute_hash()
        proof = self.proof_of_work(genesis_block)
        genesis_block.hash = proof
        # self.add_block(genesis_block, proof)
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        """
        Retrieve the most recent block in the chain.
        """
        return self.chain[-1]

    def add_block(self, block, proof):
        """
        A function that adds the block to the chain after verification.
        Verification process:
        * Checking if the proof is valid.
        * The previous_hash referred in the block and the hash of a latest block
          in the chain match.
        """
        previous_hash = self.last_block.hash

        if previous_hash != block.previous_hash:
            return False

        if not self.is_valid_proof(block, proof):
            return False

        block.hash = proof
        self.chain.append(block)
        return True

    def remove_last_block(self):
        self.chain.pop()
        return True

    def proof_of_work(self, block):
        """
        Function that tries different values of the nonce to get a hash
        that satisfies difficulty criteria.
        """
        block.nonce = 0

        computed_hash = block.compute_hash()
        while not computed_hash.startswith('0' * Blockchain.difficulty):
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def is_valid_proof(self, block, block_hash):
        """
        Check if block_hash is valid hash of block and satisfies
        the difficulty criteria.
        """
        return (block_hash.startswith('0' * Blockchain.difficulty) and
                block_hash == block.compute_hash())

    def check_chain_validity(cls, chain):
        result = True
        previous_hash = "00"

        for block in chain.chain:
            block_hash = block.hash
            # remove the hash field to recompute the hash again
            # using `compute_hash` method.
            delattr(block, "hash")

            print("Validity checks:")
            print("is_valid_proof:")
            print(cls.is_valid_proof(block, block_hash))
            print(block.compute_hash())
            print(block_hash)
            print("previous_hash != block.previous_hash:")
            print(previous_hash)
            print(block.previous_hash)

            if (not cls.is_valid_proof(block, block_hash)) or previous_hash != block.previous_hash:
                result = False
                break

            block.hash, previous_hash = block_hash, block_hash

        return result

    def mine(self):
        """
        This function serves as an interface to add the pending
        transactions to the blockchain by first evaluating account balances
        and if the buyer has the required amount before adding them to the
        block and figuring out proof of work.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.last_block

        new_block = Block(index=last_block.index + 1,
                          transactions=self.unconfirmed_transactions,
                          timestamp=time.time(),
                          previous_hash=last_block.hash)

        proof = self.proof_of_work(new_block)
        self.add_block(new_block, proof)

        # try and update items.
        # if invalid data to update items, delete last block and unconfirmed transaction
        if not self.update_items():
            self.unconfirmed_transactions = []
            self.remove_last_block()
            print("invalid data to update items status. transaction rejected.")
            return False

        self.confirmed_transactions += self.unconfirmed_transactions
        self.unconfirmed_transactions = []

        return new_block.index

    def update_items(self):
        # function to update items dictionary after successful mining

        # get transactions from latest block
        last_block = self.last_block

        for transaction in last_block.transactions:
            # based on action in transaction, perform necessary actions to item and update properties
            # if action == 1: listing products
            # if action == 2: purchasing product
            # if action == 3: delivering product
            if transaction["action"] == 1:
                self.items[transaction["itemid"]] = {"paymentStatus": 0, "deliveryStatus": 0, "seller_username": transaction["username"], "price": transaction["price"]}
                # self.items[transaction["itemid"]]["paymentStatus"] = 0
                # self.items[transaction["itemid"]]["deliveryStatus"] = 0
                # self.items[transaction["itemid"]]["sellerpubkey"] = transaction["mypubkey"]
                return True
            if transaction["action"] == 2:
                # debit buyers account and move funds to escrow
                # add here

                self.items[transaction["itemid"]]["buyer_username"] = transaction["mypubkey"]
                self.items[transaction["itemid"]]["paymentStatus"] = 1
                self.items[transaction["itemid"]]["deliveryStatus"] = 0
                return True

            if transaction["action"] == 3:
                # credit sellers account and move funds from escrow
                # add here

                self.items[transaction["itemid"]]["delivery_username"] = transaction["mypubkey"]
                self.items[transaction["itemid"]]["paymentStatus"] = 2
                self.items[transaction["itemid"]]["deliveryStatus"] = 1
                return True

    def add_new_user(self, username, public_key):
        self.users[username] = public_key

def create_chain_from_dump(chain_dump):
    generated_blockchain = Blockchain()
    generated_blockchain.create_genesis_block()
    for idx, block_data in enumerate(chain_dump):
        if idx == 0:
            continue  # skip genesis block
        block = Block(block_data["index"],
                      block_data["transactions"],
                      block_data["timestamp"],
                      block_data["previous_hash"],
                      block_data["nonce"])
        proof = block_data['hash']
        added = generated_blockchain.add_block(block, proof)
        if not added:
            raise Exception("The chain dump is tampered!!")
    return generated_blockchain
