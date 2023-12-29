import os
import time
import json
from dotenv import load_dotenv

from orquesta_sdk import OrquestaClient, OrquestaClientOptions
from orquesta_sdk.prompts import OrquestaPromptMetrics, OrquestaPromptMetricsEconomics
from orquesta_sdk.helpers import orquesta_openai_parameters_mapper
from orquesta_sdk.endpoints import OrquestaEndpointRequest


from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback

from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_bolt import App

# Initialize Orquesta client
from orquesta_sdk import OrquestaClient, OrquestaClientOptions

load_dotenv()

# Event API & Web API
app = App(token=os.getenv("SLACK_APP_TOKEN"))
slack_client = WebClient(os.getenv("SLACK_BOT_TOKEN"))

api_key = os.getenv("ORQUESTA_API_KEY")
options = OrquestaClientOptions(api_key=api_key, ttl=3600, environment="production")

client = OrquestaClient(options)

# Global variable to store the thread timestamp
current_thread_info = None
# This gets activated when the bot is tagged in a channel    
@app.event("app_mention")
def handle_message_events(body, logger):
    global current_thread_info
    event = body["event"]
    current_thread_info = {"thread_ts": event["ts"], "channel": event["channel"]}
    print(current_thread_info)
    # Log message
    print(str(body["event"]["text"]).split(">")[1])
    
    # Create prompt for ChatGPT
    prompt_user = str(body["event"]["text"]).split(">")[1]
    
    # Let thre user know that we are busy with the request 
    response = slack_client.chat_postMessage(channel=body["event"]["channel"], 
                                       thread_ts=body["event"]["event_ts"],
                                       text=f"Hallo vanaf Baise! :robot_face: \nBedankt voor je request, ik ga gelijk voor je aan de slag!")
    
    # Create an OrquestaEndpointRequest object
    request = OrquestaEndpointRequest(
        key="slack-app",
        metadata={"chain_id": "97db4100789b46bc8ef5bfb5d2869ff8"},
        variables={"prompt": prompt_user}
    )
    
    result = client.endpoints.query(
        request
    )
    
    # Reply to thread 
    response = slack_client.chat_postMessage(channel=body["event"]["channel"], 
                                       thread_ts=body["event"]["event_ts"],
                                       text=f"{result.content}")

# New event listener for messages
@app.event("message")
def handle_thread_messages(body, logger):
    global current_thread_info
    
    event = body["event"]
    
    # Avoid responding to bot's own messages using bot's user ID
    if event.get("user") == os.getenv("BOT_ID"):
        return
    
    # Check if the message is in the thread we're interested in
    if event.get("thread_ts") == current_thread_info.get("thread_ts"):
        
        user_message = event["text"]

        # Create an OrquestaEndpointRequest object with the user's message
        request = OrquestaEndpointRequest(
            key="slack-app",
            metadata={"chain_id": "97db4100789b46bc8ef5bfb5d2869ff8"},
            variables={"prompt": user_message}
        )
        
        # Query the OrquestaClient for a response
        result = client.endpoints.query(request)

        # Post the response back to the thread
        slack_client.chat_postMessage(
            channel=current_thread_info["channel"],
            thread_ts=current_thread_info["thread_ts"],
            text=result.content
        )

if __name__ == "__main__":
    SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN")).start()