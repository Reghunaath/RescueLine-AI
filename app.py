from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import certifi

app = FastAPI()

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== MongoDB ==========
client = MongoClient(
    'mongodb+srv://pavithra:pavithra12345@cluster0.hu4prfg.mongodb.net/?appName=Cluster0',
    tlsCAFile=certifi.where()
)
db = client['emergency_calls']
collection = db['calls']

# ========== Single Dashboard Connection ==========
dashboard_ws: WebSocket | None = None


# ========== Helpers ==========
def derive_status(priority: str) -> str:
    if priority in ("P0", "P1"):
        return "human_agent"
    return "waitlist"


def serialize_call(call: dict) -> dict:
    return {
        "id": str(call["_id"]),
        "priority": call.get("priority", "Unknown"),
        "emergency_type": call.get("emergency_type", "Unknown"),
        "caller_number": call.get("caller_number", "Unknown"),
        "location": call.get("location", "Unknown"),
        "summary": call.get("summary", ""),
        "title": call.get("title", ""),
        "timestamp": call["timestamp"].isoformat() if isinstance(call.get("timestamp"), datetime) else str(call.get("timestamp", "")),
        "status": call.get("status", "waitlist"),
        "call_duration": call.get("call_duration", 0),
    }


# ========== Routes ==========

@app.post("/")
@app.post("//")
async def webhook(request: Request):
    global dashboard_ws

    data = await request.json()

    analysis = data["data"]["analysis"]
    metadata = data["data"]["metadata"]
    priority = analysis["data_collection_results"].get("PRIORITY", {}).get("value", "Unknown")

    call_data = {
        "priority": priority,
        "summary": analysis["transcript_summary"],
        "title": analysis["call_summary_title"],
        "emergency_type": analysis["data_collection_results"].get("EMERGENCY_TYPE", {}).get("value", "Unknown"),
        "location": analysis["data_collection_results"].get("LOCATION", {}).get("value", "Unknown"),
        "timestamp": datetime.now(),
        "caller_number": metadata.get("phone_call", {}).get("external_number", "Unknown"),
        "call_duration": metadata.get("call_duration_secs", 0),
        "status": derive_status(priority),
    }

    result = collection.insert_one(call_data)
    call_data["_id"] = result.inserted_id
    print(f"✅ Saved: {call_data['priority']} → {call_data['status']}")

    # Push to dashboard if connected
    if dashboard_ws:
        try:
            await dashboard_ws.send_json({
                "type": "new_call",
                "data": serialize_call(call_data),
            })
            print("📡 Sent to dashboard")
        except Exception:
            dashboard_ws = None
            print("📡 Dashboard disconnected")

    return {"status": "received"}


@app.get("/calls")
async def get_all_calls():
    calls = list(collection.find().sort("timestamp", -1))
    serialized = [serialize_call(call) for call in calls]
    return {"total": len(serialized), "calls": serialized}


@app.patch("/calls/{call_id}/status")
async def update_call_status(call_id: str, request: Request):
    global dashboard_ws
    from bson import ObjectId

    body = await request.json()
    new_status = body.get("status")

    if new_status not in ("ai_agent", "waitlist", "human_agent", "completed"):
        return {"error": "Invalid status"}, 400

    collection.update_one({"_id": ObjectId(call_id)}, {"$set": {"status": new_status}})

    if dashboard_ws:
        try:
            await dashboard_ws.send_json({
                "type": "status_update",
                "data": {"id": call_id, "status": new_status},
            })
        except Exception:
            dashboard_ws = None

    return {"status": "updated"}


# ========== WebSocket ==========

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    global dashboard_ws

    await websocket.accept()
    dashboard_ws = websocket
    print("📡 Dashboard connected")

    # Send all existing calls on connect
    calls = list(collection.find().sort("timestamp", -1))
    await websocket.send_json({
        "type": "initial_state",
        "data": [serialize_call(call) for call in calls],
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        dashboard_ws = None
        print("📡 Dashboard disconnected")


# ========== Run ==========

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
