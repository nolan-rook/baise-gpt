from slack_sdk import WebClient
import os

from dotenv import load_dotenv
load_dotenv() 

slack_client = None

def init_slack_client():
    global slack_client
    slack_client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))