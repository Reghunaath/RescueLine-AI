from flask import Flask, request, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
client = MongoClient('mongodb://localhost:27017/')
db = client['emergency_calls']
collection = db['calls']

def extract_location(summary, transcript):
    """Extract location from summary or transcript"""
    import re
    
    # Try to find address patterns
    address_pattern = r'\d+\s+[\w\s]+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Pleasant|Mount)'
    match = re.search(address_pattern, summary, re.IGNORECASE)
    if match:
        return match.group(0)
    
    # Check agent_message in tool_calls for location
    if 'transcript' in transcript:
        for turn in transcript:
            if 'tool_calls' in turn and turn['tool_calls']:
                for tool in turn['tool_calls']:
                    if 'params_as_json' in tool:
                        import json
                        params = json.loads(tool['params_as_json'])
                        if 'agent_message' in params:
                            location_match = re.search(r'Location:\s*([^.]+)', params['agent_message'])
                            if location_match:
                                return location_match.group(1).strip()
    
    return "Unknown"

def extract_emergency_type(summary):
    """Extract emergency type from summary"""
    summary_lower = summary.lower()
    
    if any(word in summary_lower for word in ['chest pain', 'heart attack', 'cardiac', 'breathing', 'stroke']):
        return 'Medical - Cardiac'
    elif any(word in summary_lower for word in ['fire', 'smoke', 'burning', 'flames']):
        return 'Fire'
    elif any(word in summary_lower for word in ['accident', 'crash', 'collision', 'vehicle']):
        return 'Accident'
    elif any(word in summary_lower for word in ['assault', 'attack', 'robbery', 'threat']):
        return 'Crime'
    elif any(word in summary_lower for word in ['injury', 'bleeding', 'broken', 'pain']):
        return 'Medical - Injury'
    else:
        return 'Medical - General'

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    
    # Extract the important info
    analysis = data['data']['analysis']
    metadata = data['data']['metadata']
    transcript = data['data'].get('transcript', [])
    
    summary = analysis['transcript_summary']
    
    call_data = {
        'priority': analysis['data_collection_results']['PRIORITY']['value'],
        'summary': summary,
        'title': analysis['call_summary_title'],
        'emergency_type': extract_emergency_type(summary),
        'location': extract_location(summary, transcript),
        'timestamp': datetime.now(),
        'caller_number': metadata['phone_call']['external_number'],
        'call_duration': metadata['call_duration_secs']
    }
    
    # Save to MongoDB
    result = collection.insert_one(call_data)
    print(f"✅ Saved to MongoDB with ID: {result.inserted_id}")
    print(f"Priority: {call_data['priority']}")
    print(f"Type: {call_data['emergency_type']}")
    print(f"Location: {call_data['location']}")
    print(f"Summary: {call_data['summary']}")
    
    return jsonify({'status': 'received'}), 200

if __name__ == '__main__':
    app.run(port=5001)