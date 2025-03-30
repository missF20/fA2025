# Dana AI Platform - Slack Integration Setup Guide

This guide will walk you through the process of setting up and connecting your Slack workspace to the Dana AI Platform.

## Prerequisites

Before beginning the setup process, ensure you have:

1. Admin access to your Slack workspace
2. A Dana AI Platform account with appropriate permissions
3. Your Dana AI Platform API credentials

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and sign in with your Slack account.
2. Click the "Create New App" button.
3. Select "From scratch" when prompted.
4. Enter a name for your app (e.g., "Dana AI Platform") and select the workspace where you want to install it.
5. Click "Create App".

## Step 2: Configure Bot Permissions

1. In the sidebar menu, click on "OAuth & Permissions".
2. Scroll down to the "Scopes" section.
3. Under "Bot Token Scopes", add the following permissions:
   - `channels:history` - To view messages in public channels
   - `channels:read` - To view basic information about public channels
   - `chat:write` - To send messages as the app
   - `chat:write.public` - To send messages to channels the app isn't in

4. Save your changes.

## Step 3: Install App to Workspace

1. Scroll up to the top of the "OAuth & Permissions" page.
2. Click the "Install to Workspace" button.
3. Review the permissions and click "Allow" to authorize the app.
4. After installation, you'll be redirected back to the "OAuth & Permissions" page.
5. Copy the "Bot User OAuth Token" (it starts with `xoxb-`). You'll need this token for the Dana AI Platform.

## Step 4: Create a Channel for Integration

1. In your Slack workspace, create a new channel specifically for Dana AI integration (e.g., #dana-ai).
2. Invite your newly created bot to the channel by typing `/invite @YourBotName` in the channel.
3. Note the channel ID - you can find it by right-clicking on the channel in the sidebar and selecting "Copy link". The channel ID is the part that starts with "C" in the URL.

## Step 5: Connect to Dana AI Platform

1. Log in to your Dana AI Platform account.
2. Navigate to "Settings" > "Integrations".
3. Find and select "Slack" from the available integrations.
4. Enter the following information:
   - Bot Token: The Bot User OAuth Token you copied earlier (starts with `xoxb-`)
   - Channel ID: The ID of the channel you created (starts with "C")
5. Click "Connect" to establish the connection.
6. The system will verify your credentials and confirm the connection.

## Step 6: Test the Integration

1. In the Dana AI Platform, navigate to the Slack integration dashboard.
2. Click on "Send Test Message".
3. Enter a test message and click "Send".
4. Verify that the message appears in your designated Slack channel.
5. You can also test retrieving messages by clicking "Get Recent Messages".

## Troubleshooting

If you encounter issues during setup:

- **Connection Fails**: Ensure your Bot Token and Channel ID are correct and that the bot has been invited to the channel.
- **Permission Errors**: Verify that you've added all the required scopes to your Slack app.
- **Message Sending Fails**: Confirm that the bot has permission to post in the channel.
- **No Messages Retrieved**: Check that the bot can access the channel history.

## Additional Configuration

### Customize Notification Settings

1. In the Dana AI Platform, navigate to "Settings" > "Notifications".
2. Configure which events should trigger Slack notifications.
3. Customize message templates for different notification types.

### Setup Automated Workflows

1. Navigate to "Automation" > "Workflows".
2. Create workflows that include Slack actions such as:
   - Send notification when new client messages arrive
   - Post daily summaries of platform activity
   - Alert team members about urgent support requests

## Support

If you need assistance with your Slack integration, please contact Dana AI support at support@dana-ai.com or refer to the [API Reference Documentation](./API_REFERENCE_SLACK.md) for detailed technical information.