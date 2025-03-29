"""
Slack Integration Demo Script

This script provides a simple test for the Slack integration.
It posts a message to Slack using the configured bot token and channel ID.
"""

import os
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_slack_connection():
    """
    Test the Slack connection by checking the bot token and channel ID.
    """
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
    
    if not slack_token:
        logger.error("SLACK_BOT_TOKEN environment variable not set")
        return False, "SLACK_BOT_TOKEN environment variable not set"
        
    if not slack_channel_id:
        logger.error("SLACK_CHANNEL_ID environment variable not set")
        return False, "SLACK_CHANNEL_ID environment variable not set"
    
    try:
        # Initialize Slack client
        client = WebClient(token=slack_token)
        
        # Call auth.test to verify the token
        auth_test = client.auth_test()
        
        if not auth_test.get('ok'):
            logger.error(f"Authentication failed: {auth_test.get('error')}")
            return False, f"Authentication failed: {auth_test.get('error')}"
            
        # Get bot info
        bot_info = auth_test.get('user')
        team_info = auth_test.get('team')
        
        # Check if channel exists
        try:
            channel_info = client.conversations_info(channel=slack_channel_id)
            channel_name = channel_info.get('channel', {}).get('name')
            
            logger.info(f"Successfully connected to Slack as {bot_info} for team {team_info}")
            logger.info(f"Channel configured: #{channel_name} ({slack_channel_id})")
            
            return True, {
                "bot_name": bot_info,
                "team_name": team_info,
                "channel_name": channel_name,
                "channel_id": slack_channel_id
            }
            
        except SlackApiError as e:
            if e.response.get('error') == 'channel_not_found':
                logger.error(f"Channel ID {slack_channel_id} not found")
                return False, f"Channel ID {slack_channel_id} not found"
            else:
                logger.error(f"Error getting channel info: {str(e)}")
                return False, f"Error getting channel info: {str(e)}"
                
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
        return False, f"Slack API error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error testing Slack connection: {str(e)}")
        return False, f"Error testing Slack connection: {str(e)}"

def send_test_message():
    """
    Send a test message to the configured Slack channel.
    """
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
    
    if not slack_token or not slack_channel_id:
        logger.error("Slack credentials not properly configured")
        return False, "Slack credentials not properly configured"
    
    try:
        # Initialize Slack client
        client = WebClient(token=slack_token)
        
        # Send a message
        response = client.chat_postMessage(
            channel=slack_channel_id,
            text="Hello from Dana AI! This is a test message from the Slack integration.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Hello from Dana AI!* :wave:"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "This is a test message from the Slack integration. If you can see this, the integration is working correctly."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Sent from Dana AI on " + os.environ.get('REPL_SLUG', 'Replit')
                        }
                    ]
                }
            ]
        )
        
        if response.get('ok'):
            logger.info(f"Test message sent successfully: {response.get('ts')}")
            return True, {
                "message_ts": response.get('ts'),
                "channel": response.get('channel')
            }
        else:
            logger.error(f"Failed to send message: {response.get('error')}")
            return False, f"Failed to send message: {response.get('error')}"
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
        return False, f"Slack API error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error sending test message: {str(e)}")
        return False, f"Error sending test message: {str(e)}"

def get_recent_messages():
    """
    Get recent messages from the configured Slack channel.
    """
    slack_token = os.environ.get('SLACK_BOT_TOKEN')
    slack_channel_id = os.environ.get('SLACK_CHANNEL_ID')
    
    if not slack_token or not slack_channel_id:
        logger.error("Slack credentials not properly configured")
        return False, "Slack credentials not properly configured"
    
    try:
        # Initialize Slack client
        client = WebClient(token=slack_token)
        
        # Get channel history
        response = client.conversations_history(
            channel=slack_channel_id,
            limit=10
        )
        
        if response.get('ok'):
            messages = response.get('messages', [])
            logger.info(f"Retrieved {len(messages)} messages from Slack")
            
            return True, messages
        else:
            logger.error(f"Failed to get messages: {response.get('error')}")
            return False, f"Failed to get messages: {response.get('error')}"
            
    except SlackApiError as e:
        logger.error(f"Slack API error: {str(e)}")
        return False, f"Slack API error: {str(e)}"
        
    except Exception as e:
        logger.error(f"Error getting recent messages: {str(e)}")
        return False, f"Error getting recent messages: {str(e)}"

if __name__ == "__main__":
    print("\nDana AI - Slack Integration Test\n" + "="*30)
    
    print("\nTesting Slack connection...")
    connection_result, connection_details = test_slack_connection()
    
    if connection_result:
        print(f"✅ Connection successful!")
        print(f"Bot: {connection_details.get('bot_name')}")
        print(f"Team: {connection_details.get('team_name')}")
        print(f"Channel: #{connection_details.get('channel_name')} ({connection_details.get('channel_id')})")
        
        # Ask user if they want to send a test message
        send_msg = input("\nDo you want to send a test message? (y/n): ").strip().lower()
        
        if send_msg == 'y':
            print("\nSending test message...")
            message_result, message_details = send_test_message()
            
            if message_result:
                print("✅ Message sent successfully!")
                
                # Ask user if they want to get recent messages
                get_msgs = input("\nDo you want to retrieve recent messages? (y/n): ").strip().lower()
                
                if get_msgs == 'y':
                    print("\nRetrieving recent messages...")
                    messages_result, messages = get_recent_messages()
                    
                    if messages_result:
                        print("✅ Messages retrieved successfully!")
                        print("\nMost recent messages:")
                        
                        for i, msg in enumerate(messages):
                            user = msg.get('user', 'Unknown')
                            text = msg.get('text', 'No text')
                            ts = msg.get('ts', 'Unknown time')
                            
                            print(f"{i+1}. [{ts}] {user}: {text[:50]}...")
                    else:
                        print(f"❌ Error retrieving messages: {messages}")
                else:
                    print("Skipping message retrieval.")
            else:
                print(f"❌ Error sending message: {message_details}")
        else:
            print("Skipping test message.")
    else:
        print(f"❌ Connection failed: {connection_details}")
        
    print("\nSlack integration test complete.")