from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import uuid
import urllib3
from datetime import datetime, timezone
from azure.identity import InteractiveBrowserCredential

# 1. Hide the annoying "Insecure Request" warnings in the terminal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FOUNDRY_ENDPOINT = "https://Claims-Intake.services.ai.azure.com/api/projects/firstProject/applications/KbChatBot/protocols/activityprotocol?api-version=2025-11-15-preview"

# 2. Disable SSL verification for the Azure Login popup
credential = InteractiveBrowserCredential(connection_verify=False)

class ChatRequest(BaseModel):
    query: str
    userId: str = "manulife_ops_user"

@app.post("/api/chat")
def chat_endpoint(request: ChatRequest):
    try:
        print("Requesting secure token from Azure...")
        token_obj = credential.get_token("https://ai.azure.com/.default")
        token = token_obj.token

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        payload = {
            "type": "message",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channelId": "directline",
            "conversation": {"id": f"conv_{request.userId}"},
            "from": {"id": request.userId, "name": "User"},
            "text": request.query,
            "deliveryMode": "expectReplies" 
        }

        print("Sending message to Azure AI Foundry...")
        
        # 3. Disable SSL verification for the actual message we send to the bot (verify=False)
        response = requests.post(FOUNDRY_ENDPOINT, headers=headers, json=payload, verify=False)
        
        if response.status_code not in [200, 201, 202]:
            print(f"AZURE ERROR {response.status_code}: {response.text}")
            return {"answer": f"⚠️ Azure Error {response.status_code}. See Python terminal."}

        if not response.text.strip():
             return {"answer": "⚠️ Azure accepted the message but returned an empty response."}

        data = response.json()
        
        activities = data.get("activities", [])
        bot_replies = [act for act in activities if act.get("type") == "message" and act.get("from", {}).get("id") != request.userId]
        
        if bot_replies:
            return {"answer": bot_replies[-1].get("text", "Received blank text from Knowledge Base.")}
            
        if "error" in data:
             error_msg = data["error"].get("message", "Unknown Azure logic error")
             return {"answer": f"⚠️ Azure Bot Error: {error_msg}"}
            
        return {"answer": "The bot processed the query but returned no text."}

    except Exception as e:
        print(f"Python Error: {e}")
        return {"answer": f"⚠️ Python connection error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)