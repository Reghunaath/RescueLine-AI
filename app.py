
from fastapi import FastAPI, Request
from pymongo import MongoClient
from datetime import datetime
import certifi

app = FastAPI()

# MongoDB connection with SSL certificate
client = MongoClient(
    'mongodb+srv://pavithra:pavithra12345@cluster0.hu4prfg.mongodb.net/?appName=Cluster0',
    tlsCAFile=certifi.where()
)
db = client['emergency_calls']
collection = db['calls']

@app.post('/')

async def webhook(request: Request):
    data = await request.json()
    
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
        'call_duration': metadata.get('call_duration_secs', 0),
        'is_connected': False,
    }
    
    # Save to MongoDB
    result = collection.insert_one(call_data)
    print(f"✅ Saved to MongoDB with ID: {result.inserted_id}")
    print(f"Priority: {call_data['priority']}")
    
    return {'status': 'received'}

@app.get('/calls')
async def get_all_calls():
    """Get all emergency calls from the database"""
    calls = list(collection.find().sort('timestamp', -1))  # Sort by newest first
    print(calls)
    # Convert ObjectId to string for JSON serialization
    for call in calls:
        call['_id'] = str(call['_id'])
        # Convert datetime to ISO format string
        if 'timestamp' in call:
            call['timestamp'] = call['timestamp'].isoformat()
    
    return {
        'total': len(calls),
        'calls': calls
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, port=5001)
