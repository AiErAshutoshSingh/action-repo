from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

client = MongoClient(os.getenv("MONGO_URI"))
db = client.github_events
collection = db.events

@app.route('/')
def home():
    return "✅ Flask Webhook Listener Active"

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    ts = datetime.utcnow().strftime("%b %d %Y - %I:%M %p UTC")
    e = {}
    if 'commits' in payload and 'ref' in payload:
        e = {"action_type":"PUSH", "author":payload["pusher"]["name"],
             "to_branch":payload["ref"].split('/')[-1], "timestamp":ts}
    elif payload.get("action")=="opened" and payload.get("pull_request"):
        pr = payload["pull_request"]
        e = {"action_type":"PULL_REQUEST", "author":pr["user"]["login"],
             "from_branch":pr["head"]["ref"], "to_branch":pr["base"]["ref"], "timestamp":ts}
    elif payload.get("action")=="closed" and payload.get("pull_request",{}).get("merged"):
        pr = payload["pull_request"]
        e = {"action_type":"MERGE", "author":pr["user"]["login"],
             "from_branch":pr["head"]["ref"], "to_branch":pr["base"]["ref"], "timestamp":ts}
    if e:
        collection.insert_one(e)
        return jsonify({"msg":"Event stored"}),200
    return jsonify({"msg":"Not tracked"}),400

@app.route('/events')
def events():
    docs = list(collection.find({},{"_id":0}).sort("_id",-1).limit(10))
    return jsonify(docs)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
