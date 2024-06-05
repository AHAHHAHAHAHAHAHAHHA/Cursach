import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import openmeteo_requests
import requests_cache
from retry_requests import retry

url = "https://api.open-meteo.com/v1/forecast"

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)


class Blockchain:
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.create_block(proof=1, prev_hash='0')
        self.nodes = {"127.0.0.1:5001",
                      "127.0.0.1:5002",
                      "127.0.0.1:5003"}

    def create_block(self, proof, prev_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'data': self.mempool,
                 'proof': proof,
                 'prev_hash': prev_hash}

        block['hash'] = self.hash(block)
        self.mempool = []
        self.chain.append(block)
        return block

    def get_previous_block(self):
        return self.chain[-1]

    def proof_of_work(self, previous_proof):
        new_proof = 1
        while True:
            hash_operation = hashlib.sha256(str(
                (new_proof ** 3 - new_proof ** (1 / 2)) - previous_proof * 781).encode()
                                            ).hexdigest()
            if not hash_operation.startswith('0000'):
                new_proof += 1
            else:
                print('You mined a block!')
                break

        return new_proof

    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def add_transaction(self, sender, receiver, amount):
        for node in self.nodes:
            current_mempool = requests.get(f'http://{node}/get_mempool')
            if current_mempool.status_code == 200:
                self.mempool += current_mempool.json()['mempool']

        params = {
            "latitude": "50.454701",
            "longitude": "30.5238",
            "current": "weather_code"
        }
        responses = openmeteo.weather_api(url, params=params)

        # Process first location. Add a for-loop for multiple locations or weather models
        response = responses[0]

        current = response.Current()
        current_weather_code = current.Variables(0).Value()

        self.mempool.append({
            'block_data': {
                'coordinates': [response.Latitude(), response.Longitude()],
                'weather_code': current_weather_code
            }
        })

        prev_block = self.get_previous_block()
        return prev_block[
            'index'] + 1  # індекс останнього замайненого блока + 1,тобто індекс не замайненого блока в який вставим транзакції

    def add_nodes(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        longest_chain = None
        max_length = len(self.chain)
        for node in self.nodes:
            current_chain = requests.get(f'http://{node}/get_chain')
            if current_chain.status_code == 200:
                chain = current_chain.json()['chain']
                length = current_chain.json()['length']
                if length > max_length:
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True

        return False


blockchain = Blockchain()

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

node_adress = str(uuid4()).replace('-', '')


@app.route('/mining_block', methods=['GET'])
def mining_block():
    blockchain.add_transaction(sender=node_adress, receiver='Andriy', amount=10)
    previous_proof = blockchain.get_previous_block()['proof']
    previous_hash = blockchain.get_previous_block()['hash']
    proof = blockchain.proof_of_work(previous_proof)
    block = blockchain.create_block(proof, previous_hash)

    for node in blockchain.nodes:
        requests.get(f'http://{node}/get_mempool').json()['mempool'] = []

    response = {'message': 'Congratulation! You are sucesfully mined a block! Proud of you',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'data': block['data'],
                'proof': block['proof'],
                'prev_hash': block['prev_hash'],
                'hash': blockchain.hash(block)}

    return jsonify(response), 200


@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/get_mempool', methods=['GET'])
def get_mempool():
    response = {'mempool': blockchain.mempool}
    return jsonify(response), 200


@app.route('/is_valid', methods=['GET'])
def is_valid():
    first_index = 0
    second_index = 1
    if len(blockchain.chain) == 1:
        return "Blockchain haven't mined yet."

    while second_index <= len(blockchain.chain) - 1:
        block = blockchain.chain[second_index]
        prev_block = blockchain.chain[first_index]
        hash_operation = hashlib.sha256(str(
            (block['proof'] ** 3 - block['proof'] ** (1 / 2)) - prev_block['proof'] * 781).encode()
                                        ).hexdigest()

        if block['prev_hash'] != prev_block['hash'] and not hash_operation.startswith('0000'):
            return 'Blockchain is invalid.'

        first_index += 1
        second_index += 1

    return 'Blockchain is valid.'


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json_file = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json_file for key in transaction_keys):
        return 'Houston, we have a problem. Some elements are missed.', 400  # помилка Bad Request

    index = blockchain.add_transaction(sender=json_file['sender'],
                                       receiver=json_file['receiver'],
                                       amount=json_file['amount'])
    response = {'message': f'The transaction added to Block {index}'}
    return jsonify(response), 201  # ми створили транзакцію в блок за допомогою метода POST, тому статус код 201


@app.route('/add_node', methods=['POST'])
def add_node():
    json_file = request.get_json()
    adresses = json_file.get('nodes')
    if not adresses:
        return 'The node not found.', 400

    for adress in adresses:
        blockchain.add_nodes(adress)
    response = {'message': 'All the nodes are added.',
                'total_number': len(blockchain.nodes),
                'nodes': list(blockchain.nodes)}

    return jsonify(response), 201


@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    chain_correct = blockchain.replace_chain()
    if chain_correct:
        response = {'message': 'We found longest chain. The chain are replaced now.',
                    'current_chain': blockchain.chain}
    else:
        response = {'message': 'All Good. The chain are no need to replace.',
                    'current_chain': blockchain.chain}

    return jsonify(response), 200


app.run(host='0.0.0.0', port=5002)
