import os
import threading
from flask import Flask, request, jsonify, redirect, session, url_for
from dotenv import load_dotenv
from orquesta_sdk import OrquestaClient, OrquestaClientOptions
from orquesta_sdk.endpoints import OrquestaEndpointRequest
from slack_sdk import WebClient
from slack_sdk.oauth import AuthorizeUrlGenerator
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
import requests

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")  # Set a secret key for session management

# Initialize Slack client
slack_client = WebClient()

# Initialize Orquesta client
api_key = os.getenv("ORQUESTA_API_KEY")
options = OrquestaClientOptions(api_key=api_key, ttl=3600, environment="production")
client = OrquestaClient(options)

# Slack OAuth settings
client_id = os.getenv("SLACK_CLIENT_ID")
client_secret = os.getenv("SLACK_CLIENT_SECRET")
scopes = ["app_mentions:read", "channels:history", "channels:read", "chat:write"]
redirect_uri = os.getenv("SLACK_REDIRECT_URI")
#state_store = FileOAuthStateStore(expiration_seconds=300, base_dir="./data/states")
#installation_store = FileInstallationStore(base_dir="./data/installations")
authorize_url_generator = AuthorizeUrlGenerator(
    client_id=client_id,
    scopes=scopes,
    redirect_uri=redirect_uri
)
# Route to start the OAuth process
@app.route('/slack/install', methods=['GET'])
def pre_install():
    # Directly generate the authorization URL without a state parameter
    url = authorize_url_generator.generate()
    return redirect(url)

# Route to handle the OAuth callback
@app.route('/slack/oauth_redirect', methods=['GET'])
def post_install():
    code = request.args['code']

    # Initialize a WebClient for the OAuth process
    oauth_client = WebClient()

    # Exchange the code for an access token using the oauth.v2.access API method
    oauth_response = oauth_client.oauth_v2_access(
        client_id=client_id,
        client_secret=client_secret,
        code=code,
        redirect_uri=redirect_uri
    )

    if not oauth_response.get("ok"):
        return f"Error during OAuth: {oauth_response.get('error')}", 500

    # Extract the bot token from the OAuth response
    bot_token = oauth_response.get("access_token")

    # Print the bot token to the console (stdout)
    print(f"Bot token: {bot_token}")
    
    return "Auth completed! You can now use the Slack app."
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

    # Send an immediate response to Slack indicating that the request is being processed
    slack_client.token =  os.getenv("SLACK_BOT_TOKEN")  # Use the token from the session
    slack_client.chat_postMessage(
        channel=event['channel'],
        thread_ts=event['ts'],  # Ensure this is the original message timestamp
        text="Processing your request, please wait..."
    )

    # Start a new thread to handle the long-running Orquesta API call
    threading.Thread(target=query_orquesta, args=(event, prompt_user)).start()

def query_orquesta(event, prompt_user):
    # Create an OrquestaEndpointRequest object
    orquesta_request = OrquestaEndpointRequest(
        key="slack-app",
        variables={"prompt": prompt_user}
    )

    # Query the OrquestaClient for a response
    result = client.endpoints.query(orquesta_request)

    # Reply to the thread with the result from Orquesta
    slack_client.chat_postMessage(
        channel=event['channel'],
        thread_ts=event['ts'],  # Ensure this is the original message timestamp
        text=result.content
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)