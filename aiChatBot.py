# Created and Owened by Luca Buselli. Do not use without permission.(c) 2024

import os
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
import canvasapi

# Load environment variables
if load_dotenv("C:\\Users\\Luca.Buselli\\Desktop\\Lib_Databse\\aiChatBot\\aiChatBot.env"):
    print("Environment variables loaded successfully.")
else:
    print("Failed to load environment variables from aiChatBot.env.")

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# Dictionary to store conversation histories
conversation_histories = {}

def query_openai(user_input, user_id, user_display_name):
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {openai_api_key}",
        "Content-Type": "application/json",
    }

    # Prepare messages for the API call, including history if available
    messages = [
        {"role": "system", "content": f"You are an AI Teaching Assistant created by Luca Buselli to help {user_display_name}. You are a virtual TA with 30 years experience with MSSQL and Python along with UI/UX design skills with Tkinter and other UI/UX python libraries. You are supporting Prof.Leo with INFO-3140 and INFO-3240. The name of the person you are working with is {user_display_name}. "}
    ]
    
    # Add conversation history if present
    if user_id in conversation_histories:
        messages.extend(conversation_histories[user_id])
    
    # Add the latest message from the user
    messages.append({"role": "user", "content": user_input})

    data = {
        "model": "gpt-4-0125-preview",
        "messages": messages,
        "temperature": 0,
        "max_tokens": 3500
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    
    if response.status_code == 200:
        # Extracting the text from the response and updating the conversation history
        bot_response = response.json()["choices"][0]["message"]["content"]
        # Update the conversation history with the latest exchange
        conversation_histories.setdefault(user_id, []).append({"role": "user", "content": user_input})
        conversation_histories[user_id].append({"role": "assistant", "content": bot_response})
        return bot_response
    else:
        print(f"Failed to fetch response: HTTP {response.status_code} - {response.text}")
        return "Sorry, I couldn't fetch a response. Please try again."

@app.message(".*")


def message_handler(message, say, client: WebClient):
    user_id = message['user']
    channel_id = message['channel']
    user_input = message['text']
    
    try:
        user_info_response = client.users_info(user=user_id)
        if user_info_response["ok"]:
            user_display_name = user_info_response["user"]["profile"]["display_name"]
            if not user_display_name:  # Fallback to real name if display name is empty
                user_display_name = user_info_response["user"]["real_name"]
        else:
            user_display_name = "there"  # Fallback greeting if user info can't be fetched
    except SlackApiError as e:
        print(f"Error fetching user info: {e}")
        user_display_name = "there"  # Fallback greeting in case of an error


    # Send a temporary "thinking" message with a spinner emoji
    try:
        result = client.chat_postMessage(
            channel=channel_id,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f":thinking_face: Give me a moment to think {user_display_name} ..."
                    }
                }
            ]
        )
    except SlackApiError as e:
        print(f"Error posting message: {e}")

    # Simulate processing time
    # bot_response = query_openai(user_input, user_id)
    bot_response = query_openai(user_input, user_id, user_display_name)

    # Update the original message with the actual response
    try:
        client.chat_update(
            channel=channel_id,
            ts=result['ts'],  # Timestamp of the message we want to update
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text":  bot_response
                    }
                }
            ],
            text= "Something is wrong, please contact Luca"
        )
    except SlackApiError as e:
        print(f"Error updating message: {e}")



if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
