# RescueLine AI 

Real-time emergency call triage dashboard for disaster response coordination.

## Details

- **Problem:** Emergency helplines get overwhelmed during disasters. RescueLine AI uses an AI voice agent to instantly triage incoming calls, prioritize life-threatening emergencies, and route them to human responders while managing non-critical cases on a waitlist.

- **Tech Stack:**
  - Frontend: React + Tailwind CSS with WebSocket for real-time updates
  - Backend: Node.js/Express with MongoDB Atlas
  - AI Integration: ElevenLabs conversational AI agent for call triage
  - Infrastructure: Twilio for telephony, ngrok for webhook handling

- **Extension Type:** Full-stack dashboard with real-time data synchronization using MongoDB change streams

- **Future Improvements:**
  - Add call recording playback
  - Implement dispatcher assignment workflow
  - Build analytics dashboard for call volume trends
  - Add manual status override with drag-and-drop

## Set Up Instructions

### Prerequisites
- Node.js 18+
- MongoDB Atlas account
- ElevenLabs account (for AI agent)
- Twilio account (for phone number)

### Dashboard Installation

1. Clone the repository:
```bash
git clone https://github.com/Reghunaath/RescueLine-AI.git
cd RescueLineAI
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run FastAPI Server

```bash
uvicorn main:app --reload --port 5001
```

4. Expose Backend with ngrok

Open a new terminal and run:

```bash
ngrok http 5001
```
You will see a public HTTPS URL like:

```
https://abcd1234.ngrok-free.app
```

Copy this URL — it will be used in ElevenLabs webhook.

# 5. ElevenLabs Setup

1. Go to ElevenLabs Dashboard
2. Create a new AI Agent
3. Enable:
   - Call Analysis
   - Transcript Summary
   - Data Collection Fields:
     - PRIORITY
     - EMERGENCY_TYPE
     - LOCATION

---

## 5.1 Set Webhook URL in ElevenLabs

Inside the Agent settings, configure:

Webhook URL:

```
https://your-ngrok-url/

```

# 6. Twilio Setup

1. Buy a Twilio phone number
2. Go to Twilio Console → Phone Numbers
3. Select your number
4. Under **Voice Configuration**
5. Set:

```
When a call comes in:
→ Webhook URL → Your ElevenLabs Agent URL
```

Now the call flow works like this:

```
User calls Twilio number
→ Twilio forwards call to ElevenLabs agent
→ ElevenLabs handles AI conversation
→ After call ends, ElevenLabs sends webhook to FastAPI (via ngrok)
→ FastAPI stores data in MongoDB
→ Dashboard updates in real time via WebSocket
```



## Architecture

```
ElevenLabs AI Agent → Twilio → ngrok Backend → MongoDB Atlas
                                                     ↓
                                          MongoDB Change Stream
                                                     ↓
                                            Local Express Server
                                                     ↓
                                              WebSocket
                                                     ↓
                                            React Dashboard
```

- **Call Flow:** Caller → Twilio number → ElevenLabs AI → Priority assignment (P0-P3)
- **Data Flow:** AI agent → webhook → MongoDB → change stream → dashboard (real-time)
- **Priority Logic:** P0/P1 calls route to human agents, P2/P3 go to waitlist

## Collaborators

- Reghunaath
- Naga Pavithra
