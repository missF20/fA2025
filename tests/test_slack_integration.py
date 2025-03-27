"""
Slack Integration Tests

This module contains tests for the Slack integration functionality,
testing both the core slack.py module and the enhanced SlackIntegration class.
"""

import os
import unittest
from unittest.mock import patch, MagicMock

import slack
from automation.integrations.business.slack_integration import SlackIntegration


class MockSlackResponse:
    """Mock response object for Slack API calls"""
    
    def __init__(self, data):
        self.data = data
        
    def get(self, key, default=None):
        return self.data.get(key, default)
        

class TestSlackModule(unittest.TestCase):
    """Test the core slack.py module functions"""
    
    @patch('slack.slack_client')
    def setUp(self, mock_client):
        """Set up test environment"""
        self.mock_client = mock_client
        # Temporary set environment variables for testing
        os.environ['SLACK_BOT_TOKEN'] = 'xoxb-test-token'
        os.environ['SLACK_CHANNEL_ID'] = 'C1234567890'
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables after testing
        if 'SLACK_BOT_TOKEN' in os.environ:
            del os.environ['SLACK_BOT_TOKEN']
        if 'SLACK_CHANNEL_ID' in os.environ:
            del os.environ['SLACK_CHANNEL_ID']
    
    def test_post_message(self):
        """Test posting a message to Slack"""
        # Setup mock response
        self.mock_client.chat_postMessage.return_value = {
            'ok': True,
            'channel': 'C1234567890',
            'ts': '1503435956.000247'
        }
        
        # Call function
        result = slack.post_message('Test message')
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Message posted successfully')
        self.assertEqual(result['timestamp'], '1503435956.000247')
        self.assertEqual(result['channel'], 'C1234567890')
        
        # Verify mock was called correctly
        self.mock_client.chat_postMessage.assert_called_once_with(
            channel='C1234567890',
            text='Test message'
        )
    
    def test_get_channel_history(self):
        """Test getting channel history from Slack"""
        # Setup mock response
        self.mock_client.conversations_history.return_value = {
            'ok': True,
            'messages': [
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Test message 1',
                    'ts': '1503435956.000247'
                },
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Test message 2',
                    'ts': '1503435957.000248'
                }
            ],
            'has_more': False
        }
        
        # Call function
        result = slack.get_channel_history(limit=10)
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['text'], 'Test message 1')
        
        # Verify mock was called correctly
        self.mock_client.conversations_history.assert_called_once_with(
            channel='C1234567890',
            limit=10,
            oldest=None,
            latest=None
        )
    
    def test_get_thread_replies(self):
        """Test getting thread replies from Slack"""
        # Setup mock response
        self.mock_client.conversations_replies.return_value = {
            'ok': True,
            'messages': [
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Parent message',
                    'ts': '1503435956.000247'
                },
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Reply 1',
                    'ts': '1503435957.000248',
                    'thread_ts': '1503435956.000247'
                }
            ],
            'has_more': False
        }
        
        # Call function
        result = slack.get_thread_replies('1503435956.000247')
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['text'], 'Reply 1')
        
        # Verify mock was called correctly
        self.mock_client.conversations_replies.assert_called_once_with(
            channel='C1234567890',
            ts='1503435956.000247',
            limit=100
        )
    
    def test_verify_slack_credentials(self):
        """Test verifying Slack credentials"""
        # Setup mock responses
        self.mock_client.auth_test.return_value = {
            'ok': True,
            'team': 'Test Team',
            'bot_id': 'B012C3D4E5'
        }
        
        self.mock_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': 'C1234567890',
                'name': 'test-channel'
            }
        }
        
        # Call function
        result = slack.verify_slack_credentials()
        
        # Assertions
        self.assertTrue(result['valid'])
        self.assertEqual(result['message'], 'Slack credentials are valid')
        self.assertEqual(result['team'], 'Test Team')
        self.assertEqual(result['channel_name'], 'test-channel')
        
        # Verify mocks were called correctly
        self.mock_client.auth_test.assert_called_once()
        self.mock_client.conversations_info.assert_called_once_with(channel='C1234567890')


class TestSlackIntegration(unittest.TestCase):
    """Test the enhanced SlackIntegration class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a mock WebClient
        self.mock_client = MagicMock()
        
        # Set environment variables for testing
        os.environ['SLACK_BOT_TOKEN'] = 'xoxb-test-token'
        os.environ['SLACK_CHANNEL_ID'] = 'C1234567890'
        
        # Create SlackIntegration with patch
        with patch('automation.integrations.business.slack_integration.WebClient', return_value=self.mock_client):
            self.slack_integration = SlackIntegration()
            # Override SLACK_SDK_AVAILABLE
            self.slack_integration.client = self.mock_client
    
    def tearDown(self):
        """Clean up test environment"""
        # Remove environment variables after testing
        if 'SLACK_BOT_TOKEN' in os.environ:
            del os.environ['SLACK_BOT_TOKEN']
        if 'SLACK_CHANNEL_ID' in os.environ:
            del os.environ['SLACK_CHANNEL_ID']
    
    def test_is_configured(self):
        """Test checking if Slack integration is configured"""
        # Test with mock client (should be configured)
        self.assertTrue(self.slack_integration.is_configured())
        
        # Test with missing token
        with patch('automation.integrations.business.slack_integration.WebClient', return_value=self.mock_client):
            integration = SlackIntegration(token=None, channel_id='C1234567890')
            integration.client = self.mock_client
            self.assertFalse(integration.is_configured())
    
    def test_send_message(self):
        """Test sending a message to Slack"""
        # Setup mock response
        self.mock_client.chat_postMessage.return_value = {
            'ok': True,
            'channel': 'C1234567890',
            'ts': '1503435956.000247'
        }
        
        # Call function
        result = self.slack_integration.send_message('Test message')
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Message sent successfully')
        self.assertEqual(result['timestamp'], '1503435956.000247')
        
        # Verify mock was called correctly
        self.mock_client.chat_postMessage.assert_called_once_with(
            channel='C1234567890',
            text='Test message'
        )
    
    def test_get_messages(self):
        """Test getting messages from Slack"""
        # Setup mock response
        self.mock_client.conversations_history.return_value = {
            'ok': True,
            'messages': [
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Test message 1',
                    'ts': '1503435956.000247'
                },
                {
                    'type': 'message',
                    'user': 'U012AB3CDE',
                    'text': 'Test message 2',
                    'ts': '1503435957.000248'
                }
            ],
            'has_more': False
        }
        
        # Call function
        result = self.slack_integration.get_messages(limit=10)
        
        # Assertions
        self.assertTrue(result['success'])
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['messages'][0]['text'], 'Test message 1')
        
        # Verify mock was called correctly
        self.mock_client.conversations_history.assert_called_once_with(
            channel='C1234567890',
            limit=10,
            oldest=None,
            latest=None
        )
    
    def test_create_message_blocks(self):
        """Test creating formatted message blocks"""
        # Test with all parameters
        blocks = self.slack_integration.create_message_blocks(
            header='Test Header',
            text='Test message text',
            fields=[
                {'title': 'Field 1', 'value': 'Value 1'},
                {'title': 'Field 2', 'value': 'Value 2'}
            ],
            actions=[
                {'text': 'Button 1', 'value': 'value1'},
                {'text': 'Button 2', 'value': 'value2'}
            ]
        )
        
        # Assertions
        self.assertEqual(len(blocks), 5)  # Header, text, fields, actions, divider
        self.assertEqual(blocks[0]['type'], 'header')
        self.assertEqual(blocks[0]['text']['text'], 'Test Header')
        self.assertEqual(blocks[1]['type'], 'section')
        self.assertEqual(blocks[1]['text']['text'], 'Test message text')
        self.assertEqual(len(blocks[2]['fields']), 2)
        self.assertEqual(len(blocks[3]['elements']), 2)
        
        # Test with minimal parameters
        blocks = self.slack_integration.create_message_blocks(text='Just text')
        self.assertEqual(len(blocks), 2)  # Text, divider
        self.assertEqual(blocks[0]['type'], 'section')
        self.assertEqual(blocks[0]['text']['text'], 'Just text')


if __name__ == '__main__':
    unittest.main()