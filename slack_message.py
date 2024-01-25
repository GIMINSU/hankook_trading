import logging
import os
# Import WebClient from Python SDK (github.com/slackapi/python-slack-sdk)
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from config import SlackConfig


# ID of channel you want to post message to
class SendMessageSlack(SlackConfig):
    def __init__(self, SlackConfig):
        # WebClient instantiates a client that can call API methods
        # When using Bolt, you can use either `app.client` or the `client` passed to listeners.
        self.client = WebClient(token=SlackConfig.TOKEN)
        self.logger = logging.getLogger(__name__)
        self.channel_id = SlackConfig.CHANNEL_ID

    def send_simple_message(self, message):    

        try:
            # Call the conversations.list method using the WebClient
            result = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message
                # You could also use a blocks[] array to send richer content
            )
            # Print result, which includes information about the message (like TS)
            print(result)

        except SlackApiError as e:
            print(f"Error: {e}")