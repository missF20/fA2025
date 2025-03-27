"""
Webhook Routes for Dana AI

This module handles webhook routes for various platforms.
It receives webhook events from Facebook, Instagram, and WhatsApp.
"""

import logging
import asyncio
import json
from flask import Blueprint, request, jsonify

import automation

logger = logging.getLogger(__name__)

# Create blueprint
webhooks = Blueprint('webhooks', __name__)


# Helper function to run async code in Flask routes
def run_async(coro):
    """Run an async coroutine and return its result"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@webhooks.route('/facebook', methods=['GET', 'POST'])
def facebook_webhook():
    """Handle Facebook webhook"""
    if request.method == 'GET':
        # Handle verification request
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if not mode or not token:
            return 'Missing parameters', 400
            
        # Convert verification params to a format the connector can process
        verification_data = {
            'hub.mode': mode,
            'hub.verify_token': token,
            'hub.challenge': challenge
        }
        
        result = run_async(automation.handle_webhook('facebook', request.headers, json.dumps(verification_data).encode()))
        
        if 'challenge' in result:
            return result['challenge']
        elif 'error' in result:
            return result['error'], 400
        else:
            return 'Verification failed', 400
    
    # Handle webhook event
    try:
        result = run_async(automation.handle_webhook('facebook', request.headers, request.get_data()))
        
        if 'error' in result:
            logger.error(f"Error processing Facebook webhook: {result['error']}")
            return jsonify({'success': False, 'error': result['error']}), 400
            
        return jsonify({'success': True, 'results': result.get('results', [])})
        
    except Exception as e:
        logger.error(f"Error processing Facebook webhook: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@webhooks.route('/instagram', methods=['GET', 'POST'])
def instagram_webhook():
    """Handle Instagram webhook"""
    if request.method == 'GET':
        # Handle verification request
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        if not mode or not token:
            return 'Missing parameters', 400
            
        # Convert verification params to a format the connector can process
        verification_data = {
            'hub.mode': mode,
            'hub.verify_token': token,
            'hub.challenge': challenge
        }
        
        result = run_async(automation.handle_webhook('instagram', request.headers, json.dumps(verification_data).encode()))
        
        if 'challenge' in result:
            return result['challenge']
        elif 'error' in result:
            return result['error'], 400
        else:
            return 'Verification failed', 400
    
    # Handle webhook event
    try:
        result = run_async(automation.handle_webhook('instagram', request.headers, request.get_data()))
        
        if 'error' in result:
            logger.error(f"Error processing Instagram webhook: {result['error']}")
            return jsonify({'success': False, 'error': result['error']}), 400
            
        return jsonify({'success': True, 'results': result.get('results', [])})
        
    except Exception as e:
        logger.error(f"Error processing Instagram webhook: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@webhooks.route('/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle WhatsApp webhook"""
    try:
        result = run_async(automation.handle_webhook('whatsapp', request.headers, request.get_data()))
        
        if 'error' in result:
            logger.error(f"Error processing WhatsApp webhook: {result['error']}")
            return jsonify({'success': False, 'error': result['error']}), 400
            
        return jsonify({'success': True, 'results': result.get('results', [])})
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500