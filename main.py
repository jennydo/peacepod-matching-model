# main.py
from flask import Flask, jsonify, request
import json
from pairing_model import get_pairings

app = Flask(__name__)

@app.route('/', methods=['GET'])
def default():
    return "Hello World!"

@app.route('/matchPairs', methods=['GET'])
def get_match_pairs():
    pairings = get_pairings()
    pairing_json = json.dumps(pairings) #returns a string
    return jsonify(pairing_json)

@app.route('/matchPairs', methods=['POST'])
def add_match_pair():
    data = request.get_json()
    pairings = get_pairings()
    if 'key' in data and 'value' in data:
        pairings[data['key']] = data['value']
        return jsonify({"message": "Pair added successfully"}), 201
    else:
        return jsonify({"error": "Invalid data"}), 400

if __name__ == '__main__':
    app.run(host='localhost', port = 5002, debug=True)