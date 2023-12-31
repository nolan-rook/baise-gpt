import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv

from orquesta_sdk import OrquestaClient, OrquestaClientOptions
from orquesta_sdk.endpoints import OrquestaEndpointRequest
from slack_sdk import WebClient

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize Slack client
slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

# Initialize Orquesta client
api_key = os.getenv("ORQUESTA_API_KEY")
options = OrquestaClientOptions(api_key=api_key, ttl=3600, environment="production")
client = OrquestaClient(options)

# Route for handling Slack events
@app.route('/slack/events', methods=['POST'])
def slack_events():
    data = request.json

    # Slack sends a challenge parameter in the initial verification request
    if 'challenge' in data:
        return jsonify({'challenge': data['challenge']})

    event = data.get('event', {})

    # Handle app_mention events
    if event.get('type') == 'app_mention':
        handle_app_mention(event)

    # Handle message events
    elif event.get('type') == 'message':
        handle_message(event)

    return '', 200  # HTTP 200 with empty body

def handle_app_mention(event):
    # Extract the text mentioned to the bot
    prompt_user = event.get('text', '').split('>')[1].strip()

    # Acknowledge the mention in the channel
    slack_client.chat_postMessage(
        channel=event['channel'],
        thread_ts=event['ts'],
        text=f"Hallo vanaf Baise! :robot_face:nBedankt voor je request, ik ga gelijk voor je aan de slag!"
    )

    # Create an OrquestaEndpointRequest object
    request = OrquestaEndpointRequest(
        key="slack-app",
        metadata={"chain_id": "97db4100789b46bc8ef5bfb5d2869ff8"},
        variables={"prompt": prompt_user}
    )

    # Query the OrquestaClient for a response
    result = client.endpoints.query(request)

    # Reply to the thread with the result
    slack_client.chat_postMessage(
        channel=event['channel'],
        thread_ts=event['ts'],
        text=result.content
    )

def handle_message(event):
    # Avoid responding to bot's own in a thread
    if event.get('thread_ts'):
        user_message = event['text']

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
            channel=event['channel'],
            thread_ts=event['thread_ts'],
            text=result.content
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)