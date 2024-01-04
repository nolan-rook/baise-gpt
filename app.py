import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from orquesta_sdk import OrquestaClient, OrquestaClientOptions
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

    return '', 200  # HTTP 200 with empty body

def handle_app_mention(event):
    # Extract the text mentioned to the bot
    prompt_user = event.get('text', '').split('>')[1].strip()

    # Create an OrquestaEndpointRequest object
    request = OrquestaEndpointRequest(
        key="slack-app",
        variables={"prompt": prompt_user}
    )

    # Query the OrquestaClient for a response
    result = client.endpoints.query(request)

    # Reply to the thread with the result
    slack_client.chat_postMessage(
        channel=event['channel'],
        thread_ts=event['ts'],
        text="Processing your request, please wait..."
    )

    # Since Orquesta might take a while to respond, consider handling this asynchronously
    # For now, we'll simulate a delay with a placeholder message
    # In a real-world scenario, you would use a background task queue like Celery
    # to handle the long-running operation

    # Placeholder for asynchronous processing
    # Here you would send the request to Orquesta and wait for the response
    # Once the response is received from Orquesta, send another message to Slack

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)