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
    return pair_results

@app.route('/matchPairs', methods=['POST'])
def add_match_pair():
    global pair_results  # Declare pair_results as global
    pairings = get_pairings()
    pairs_jsonify = jsonify(pairings)
    pair_results = pairs_jsonify
    return pair_results

if __name__ == '__main__':
    app.run(host='localhost', port = 5002, debug=True)