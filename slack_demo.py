#!/usr/bin/env python3
"""
Slack Demo - CLI application to test Slack integration

This is a simple command-line application to demonstrate the Slack integration
capabilities for the Dana AI platform.
"""

import argparse
import json
from datetime import datetime
import slack

def main():
    parser = argparse.ArgumentParser(description='Dana AI Slack Integration Demo')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Verify credentials command
    verify_parser = subparsers.add_parser('verify', help='Verify Slack credentials')
    
    # Send message command
    send_parser = subparsers.add_parser('send', help='Send a message to Slack')
    send_parser.add_argument('message', help='Message to send')
    
    # Get messages command
    messages_parser = subparsers.add_parser('messages', help='Get recent messages from Slack')
    messages_parser.add_argument('--limit', type=int, default=10, help='Maximum number of messages to retrieve')
    
    # Get thread replies command
    thread_parser = subparsers.add_parser('thread', help='Get replies in a thread')
    thread_parser.add_argument('thread_ts', help='Thread timestamp to get replies from')
    thread_parser.add_argument('--limit', type=int, default=20, help='Maximum number of replies to retrieve')
    
    args = parser.parse_args()
    
    # If no command is provided, show help
    if not args.command:
        parser.print_help()
        return
    
    # Execute the requested command
    if args.command == 'verify':
        result = slack.verify_slack_credentials()
        print_json(result)
        
    elif args.command == 'send':
        result = slack.post_message(args.message)
        print_json(result)
        
    elif args.command == 'messages':
        messages = slack.get_channel_history(limit=args.limit)
        if messages:
            print_json({"count": len(messages), "messages": messages})
        else:
            print_json({"error": "Failed to retrieve messages"})
            
    elif args.command == 'thread':
        replies = slack.get_thread_replies(args.thread_ts, limit=args.limit)
        if replies:
            print_json({"count": len(replies), "thread_ts": args.thread_ts, "replies": replies})
        else:
            print_json({"error": "Failed to retrieve thread replies"})

def print_json(data):
    """Print data as formatted JSON"""
    print(json.dumps(data, indent=2))

if __name__ == '__main__':
    print(f"Dana AI Slack Demo - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check if Slack is properly configured
    if not slack.slack_token or not slack.slack_channel_id:
        missing = []
        if not slack.slack_token:
            missing.append("SLACK_BOT_TOKEN")
        if not slack.slack_channel_id:
            missing.append("SLACK_CHANNEL_ID")
        print(f"⚠️ Warning: Slack is not fully configured. Missing environment variables: {', '.join(missing)}")
        print("Please set these environment variables to use the Slack integration.")
    
    main()