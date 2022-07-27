import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain

class Blockchain:

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0')
        self.node = set()
    
    def add_transactions(self,sender,reciever,amount):
        self.transactions.append({'sender':sender,
                                  'reciever':reciever,
                                  'amount':amount})
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'Transactions':self.transactions,
                 'previous_hash': previous_hash}
        self.transactions = []      #make the transactions 0 as the transaction of the blocks cant be sam
        self.chain.append(block)
        return block 

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    
    def add_node(self,address):
        parsed_url = urlparse(address)
        self.node.add(parsed_url.netloc)


    def replace_chain(self):
        network = self.node
        longest_chain = None
        max_length = len(self.chain)
        
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False

# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)

# Create Address for the node on Port 5000

node_address = str(uuid4()).replace('-', '')  #uuid4 genearate randon unique address for the node 

# Creating a Blockchain
blockchain = Blockchain()

# Mining a new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transactions(sender = node_address, reciever = 'Shwetank', amount = 1)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['Transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


#Add transactions to the blockchain

@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender','reciever','amount']
    if not all (key in json for key in transaction_keys):
        return 'Elements of the transaction missing', 400  #http status code -  request code
    
    index = blockchain.add_transactions(json['sender'],json['reciever'],json['amount'])
    
    response = {'message': f'This transaction will be added to block {index}'}
    return jsonify(response),201 #httpStatusCode -> created request code

# part 3
# decentralizing our blockchain


#connecting new node and register it

@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')   ##gives adsreses of the nodes
    if nodes is None:
        return 'No node',400
    
    for node in nodes:
        blockchain.add_node(node)
    
    response = {'message':'All the nodes are now connected. The Orion Blockchain has the following nodes',
                'total Nodes':list(blockchain.node)}
    
    return jsonify(response),201

#Replacing the longest chain with the smaller one

@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The chain replaced y longest one',
                    'New chain':blockchain.chain}
    else:
        response = {'message': 'No replacement, the current chain is larger one',
                    'Chain':blockchain.chain}
    
    return jsonify(response), 200


# Running the app
app.run(host = '0.0.0.0', port = 5000)

