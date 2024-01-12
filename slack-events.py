import os
import logging
from flask import Flask, request
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
from waitress import serve
import requests

# Define constants
INSTALLATIONS_DIR = './data/installations/'
STATES_DIR = './data/states/'
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
SIGNING_SECRET = os.getenv("SIGNING_SECRET")
SLACK_TOKEN = os.getenv("SLACK_TOKEN")
FIXED_API_ENDPOINT = os.getenv("FIXED_API_ENDPOINT")


# Set up directories
def setup_directory(dir_path):
  if not os.path.exists(dir_path):
    os.makedirs(dir_path)
  os.chmod(dir_path, 0o755)


setup_directory(INSTALLATIONS_DIR)
setup_directory(STATES_DIR)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# OAuth settings and app initialization
oauth_settings = OAuthSettings(
  client_id=CLIENT_ID,
  client_secret=CLIENT_SECRET,
  scopes=[
    "chat:write", "im:write", "im:history", "chat:write.public", "app_mentions:read", "commands",
  ],
  installation_store=FileInstallationStore(base_dir=INSTALLATIONS_DIR),
  state_store=FileOAuthStateStore(expiration_seconds=600, base_dir=STATES_DIR),
  redirect_uri=
  "https://slack.fyprr.com/slack/oauth_redirect",
)

app = App(signing_secret=SIGNING_SECRET, oauth_settings=oauth_settings)

# WebClient for sending messages
client = WebClient(token=SLACK_TOKEN)


# Event listener for DMs (Direct Messages) to the bot
@app.event("message")
def handle_direct_message(body, event, say):
  print(event)
  # if event.get("channel_type") == "im":
  message_text = event['text']
    # OPTIONAL: add 'thinking' message
  say("Hello from your bot! :robot_face:\nThanks for your request, I'm on it!")
  response = requests.get(FIXED_API_ENDPOINT + message_text)
  response_text = response.json(
  )['response'] if response.status_code == 200 else f"Request failed with status code {response.status_code}"
  say(response_text)

@app.event("app_mention")
def handle_direct_message(body, event, say):
  # if event.get("channel_type") == "im":
  try:
    channel_id = event.get("channel")
    message_text = event['text']
      # OPTIONAL: add 'thinking' message
    #say("Thinking...")
    response = requests.get(FIXED_API_ENDPOINT + message_text)
    response_text = response.json(
    )['response'] if response.status_code == 200 else f"Request failed with status code {response.status_code}"
    say(
        channel=channel_id,
        text=response_text,
        thread_ts=event.get("ts")
    )
  except SlackApiError as e:
      print(f"Error sending message: {e.response['error']}")


# Flask app and routes
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
  return handler.handle(request)


@flask_app.route("/slack/install", methods=["GET"])
def install():
  return handler.handle(request)


@flask_app.route("/slack/oauth_redirect", methods=["GET"])
def oauth_redirect():
  return handler.handle(request)


@flask_app.route('/')
def hello_world():
  return 'Hello from the Simplisafe Insight Hub Slack bot instance! Now trying OAuth'


# Run the app on Waitress server
if __name__ == "__main__":
  serve(flask_app, host='0.0.0.0', port=3030)