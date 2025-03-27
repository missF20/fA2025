# Slack Integration Setup Guide

This guide provides step-by-step instructions for setting up the Slack integration with the Dana AI platform. By following these steps, you'll be able to connect your Slack workspace to Dana AI, enabling real-time messaging and notifications.

## Prerequisites

- Administrative access to a Slack workspace
- Dana AI account with appropriate permissions
- Basic understanding of Slack app concepts

## Step 1: Create a Slack App

1. Go to [Slack API: Applications](https://api.slack.com/apps) and sign in with your Slack account
2. Click the "Create New App" button
3. Choose "From scratch" when prompted
4. Enter a name for your app (e.g., "Dana AI Integration")
5. Select the Slack workspace where you want to install the app
6. Click "Create App"

## Step 2: Configure Bot Permissions

1. In the left sidebar, select "OAuth & Permissions"
2. Scroll down to the "Scopes" section
3. Under "Bot Token Scopes", click "Add an OAuth Scope"
4. Add the following scopes:
   - `chat:write` - To send messages to channels
   - `channels:history` - To read message history in public channels
   - `groups:history` - To read message history in private channels
   - `im:history` - To read direct message history
   - `reactions:read` - To view reactions on messages

## Step 3: Install App to Workspace

1. Scroll to the top of the "OAuth & Permissions" page
2. Click the "Install to Workspace" button
3. Review the requested permissions and click "Allow"
4. After installation, you'll see a "Bot User OAuth Token" that starts with `xoxb-`
5. Copy this token as you'll need it later for configuration

## Step 4: Invite Bot to Channel

1. Open Slack and navigate to the channel where you want to receive Dana AI messages
2. Type `/invite @YourAppName` (replace "YourAppName" with the name of your app)
3. Press Enter to invite the bot to the channel

## Step 5: Get Channel ID

1. Open Slack in a web browser
2. Navigate to the channel where you invited the bot
3. Look at the URL in your browser. It will look like:
   `https://app.slack.com/client/T01A2B3C4D5/C01A2B3C4D5`
4. The last part of the URL (`C01A2B3C4D5`) is your channel ID
5. Copy this channel ID as you'll need it for configuration

## Step 6: Configure Dana AI with Slack Credentials

1. In your Dana AI application, set the following environment variables:
   - `SLACK_BOT_TOKEN`: The Bot User OAuth Token you copied in Step 3 (starts with `xoxb-`)
   - `SLACK_CHANNEL_ID`: The channel ID you copied in Step 5 (starts with `C`)

   You can set these environment variables by:
   ```
   export SLACK_BOT_TOKEN=xoxb-your-token
   export SLACK_CHANNEL_ID=C01A2B3C4D5
   ```

2. Restart your Dana AI application to apply the changes

## Step 7: Verify the Integration

1. Test the integration using the provided command-line utility:
   ```bash
   python slack_demo.py verify
   ```
   
2. If successful, you should see output similar to:
   ```json
   {
     "valid": true,
     "message": "Slack credentials are valid",
     "team": "Your Team Name",
     "bot_id": "B01A2B3C4D5",
     "channel_name": "your-channel"
   }
   ```

3. Test sending a message to Slack:
   ```bash
   python slack_demo.py send "Hello from Dana AI!"
   ```

4. Check your Slack channel to confirm the message was received

## Advanced Configuration Options

### Custom Message Formatting

When sending messages to Slack, you can use Slack's message formatting syntax:

- *Bold*: `*text*`
- _Italic_: `_text_`
- ~Strikethrough~: `~text~`
- `Code`: `` `code` ``
- ```Code blocks```: ` ```code blocks``` `
- Links: `<https://example.com|Link Text>`

### Working with Threads

To reply to a message thread, you need the timestamp of the parent message:

1. Send an initial message:
   ```bash
   python slack_demo.py send "Initial message"
   ```

2. From the response, note the `timestamp` value

3. Use this timestamp to get thread replies:
   ```bash
   python slack_demo.py thread 1615982330.000200
   ```

### Rate Limiting Considerations

The Slack API has rate limits that vary by endpoint. For production environments, consider implementing:

- Exponential backoff for retries
- Request queuing to avoid rate limit errors
- Monitoring of API usage

## Troubleshooting

### Common Issues

| Issue | Possible Solutions |
|-------|-------------------|
| "Invalid authentication" error | Check that your SLACK_BOT_TOKEN is correct and hasn't expired |
| "Channel not found" error | Verify the SLACK_CHANNEL_ID is correct and that the bot has been invited to the channel |
| "Not in channel" error | Type `/invite @YourAppName` in the channel to invite the bot |
| "Missing scope" error | Review the OAuth scopes for your app and ensure all required permissions are added |
| Rate limiting errors | Implement backoff strategies, or reduce the frequency of API calls |

### Debugging Tools

Use the following commands to help diagnose integration issues:

```bash
# Verify credentials and connections
python slack_demo.py verify

# View recent messages to check if API access is working
python slack_demo.py messages --limit 5
```

## Security Best Practices

- Never hardcode the Slack Bot Token in your source code
- Use environment variables or a secure secrets management system
- Regularly rotate your Slack API tokens
- Apply the principle of least privilege when assigning OAuth scopes
- Monitor and audit access to the Slack integration

## Additional Resources

- [Slack API Documentation](https://api.slack.com/docs)
- [Slack SDK for Python](https://slack.dev/python-slack-sdk/)
- [Message Formatting Guide](https://api.slack.com/reference/surfaces/formatting)
- [Slack App Security Guidelines](https://api.slack.com/authentication/best-practices)

---

If you encounter any issues or need additional assistance, please contact Dana AI support.