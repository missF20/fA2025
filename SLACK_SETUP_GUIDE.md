# Slack Integration Setup Guide

This guide will help you set up and configure the Slack integration for the Dana AI Platform.

## Overview

The Dana AI Platform's Slack integration allows you to:

- Send notifications to Slack about important system events
- Monitor user signups and logins
- Track subscription changes
- Report system errors and status updates
- Interact with Slack channels programmatically

## Prerequisites

Before you begin, you'll need:

1. A Slack workspace where you have admin permissions
2. Access to your Dana AI Platform instance
3. Ability to set environment variables

## Step 1: Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App"
3. Choose "From scratch"
4. Enter a name for your app (e.g., "Dana AI Platform")
5. Select the workspace where you want to install the app
6. Click "Create App"

## Step 2: Configure Bot Permissions

1. In the left sidebar, click on "OAuth & Permissions"
2. Scroll down to "Scopes" section
3. Under "Bot Token Scopes", add the following scopes:
   - `channels:history` - View messages and other content in public channels
   - `channels:read` - View basic information about public channels
   - `chat:write` - Send messages as the app
   - `chat:write.public` - Send messages to channels the app isn't in
   - `reactions:read` - View emoji reactions and their associated content

## Step 3: Install the App to Your Workspace

1. Scroll back to the top of the "OAuth & Permissions" page
2. Click "Install to Workspace"
3. Review the permissions and click "Allow"
4. After installation, you'll be redirected back to the "OAuth & Permissions" page
5. Copy the "Bot User OAuth Token" (it starts with `xoxb-`) - you'll need this later

## Step 4: Create a Slack Channel for Notifications

1. In your Slack workspace, create a new channel for Dana AI notifications
   - We recommend naming it something like `#dana-ai-notifications` or `#dana-ai-alerts`
2. Invite your newly created Slack app to the channel
   - Type `/invite @YourAppName` in the channel

## Step 5: Get the Channel ID

1. Right-click on the channel name in the sidebar and select "Copy Link"
2. The link will look something like `https://yourworkspace.slack.com/archives/C04XXXXXXXXX`
3. The part after the last `/` is your Channel ID (e.g., `C04XXXXXXXXX`)

## Step 6: Configure Environment Variables

Add the following environment variables to your Dana AI Platform instance:

1. `SLACK_BOT_TOKEN`: The Bot User OAuth Token you copied in Step 3
2. `SLACK_CHANNEL_ID`: The Channel ID you obtained in Step 5

### Setting Environment Variables

#### On a Hosted Platform

If your Dana AI Platform is hosted on a platform like Heroku, AWS, or similar:

1. Navigate to your platform's environment variables or config vars section
2. Add the variables mentioned above
3. Restart your application if necessary

#### Local Development

For local development, you can:

1. Add these to your `.env` file:
   ```
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_CHANNEL_ID=C04XXXXXXXXX
   ```
2. Or export them in your terminal:
   ```bash
   export SLACK_BOT_TOKEN=xoxb-your-token
   export SLACK_CHANNEL_ID=C04XXXXXXXXX
   ```

## Step 7: Verify the Integration

1. Start or restart your Dana AI Platform instance
2. Navigate to the Slack integration dashboard at `/api/slack/dashboard`
3. Click "Check Connection" to verify that your Slack integration is properly configured
4. If the connection is successful, you'll see a green "Connected" status
5. Try sending a test message to confirm that the integration is working properly

## Testing the Integration

You can use the Slack integration dashboard to test different notification types:

1. **User Notifications**: Test signup and login notifications
2. **Subscription Notifications**: Test new subscription, subscription change, and cancellation notifications
3. **System Notifications**: Test status updates and warnings

## Troubleshooting

### Connection Failed

If the connection check fails:

1. Verify that your environment variables are set correctly
2. Ensure that the Bot Token is valid and not expired
3. Check that your Slack app has the required permissions
4. Confirm that the app is invited to the channel specified by the Channel ID

### Messages Not Appearing

If messages aren't appearing in your Slack channel:

1. Verify that the Channel ID is correct
2. Ensure the Slack app is still a member of the channel
3. Check your application logs for any Slack API errors
4. Verify that your network allows outbound connections to Slack's API servers

### Permission Errors

If you're seeing permission errors:

1. Review the Bot Token Scopes you've granted to your app
2. Make sure you're using the Bot Token (starts with `xoxb-`) and not another type of token
3. Reinstall the app to your workspace to refresh permissions

## Advanced Configuration

### Customizing Notifications

You can customize the Slack notifications by modifying the templates in `utils/slack_notifications.py`. Each notification type has its own method that defines the message format.

### Adding New Notification Types

To add a new notification type:

1. Add a new handler method in `utils/slack_notifications.py`
2. Update the relevant notification dispatcher method to call your new handler

### Using Slack Blocks

The Slack integration supports [Block Kit](https://api.slack.com/block-kit) for rich message formatting. You can customize the block layouts in the notification handlers to create more interactive and informative messages.

## Next Steps

- Explore the [Slack Integration API Reference](API_REFERENCE_SLACK.md) for more details on available endpoints
- Review the sample code in `slack_demo.py` and `subscription_slack_demo.py` for examples of using the Slack integration programmatically