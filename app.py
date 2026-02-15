from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime
import certifi

app = Flask(__name__)

# MongoDB connection with SSL certificate
client = MongoClient(
    'mongodb+srv://pavithra:pavithra12345@cluster0.hu4prfg.mongodb.net/?appName=Cluster0',
    tlsCAFile=certifi.where()
)
db = client['emergency_calls']
collection = db['calls']

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Extract the important info
    analysis = data['data']['analysis']
    metadata = data['data']['metadata']
    
    summary = analysis['transcript_summary']
    
    call_data = {
        'priority': analysis['data_collection_results'].get('PRIORITY', {}).get('value', 'Unknown'),
        'summary': summary,
        'title': analysis['call_summary_title'],
        'emergency_type': analysis['data_collection_results'].get('EMERGENCY_TYPE', {}).get('value', 'Unknown'),
        'location': analysis['data_collection_results'].get('LOCATION', {}).get('value', 'Unknown'),
        'timestamp': datetime.now(),
        'caller_number': metadata.get('phone_call', {}).get('external_number', 'Unknown'),
        'call_duration': metadata.get('call_duration_secs', 0)
    }
    
    # Save to MongoDB
    result = collection.insert_one(call_data)
    print(f"✅ Saved to MongoDB with ID: {result.inserted_id}")
    print(f"Priority: {call_data['priority']}")
    
    return jsonify({'status': 'received'}), 200

if __name__ == '__main__':
    app.run(port=5001)