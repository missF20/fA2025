"""
Email Integration Module

This module provides functionality for connecting to and interacting with email
services like Gmail and Outlook.
"""

import os
import logging
import base64
import email
import re
import json
import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)


class EmailClient:
    """Base class for email service clients"""

    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize email client with credentials
        
        Args:
            credentials: Dictionary with authentication credentials
        """
        self.credentials = credentials
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to email service
        
        Returns:
            True if connection successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement connect()")
        
    def disconnect(self) -> None:
        """Disconnect from email service"""
        raise NotImplementedError("Subclasses must implement disconnect()")
        
    def get_messages(self, folder: str = "INBOX", limit: int = 10, 
                    since: Optional[datetime] = None, search_criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from specified folder
        
        Args:
            folder: Folder name (default: "INBOX")
            limit: Maximum number of messages to return
            since: Only return messages since this date
            search_criteria: Search criteria for filtering messages
            
        Returns:
            List of message dictionaries
        """
        raise NotImplementedError("Subclasses must implement get_messages()")
        
    def send_message(self, to: Union[str, List[str]], subject: str, 
                    body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email message
        
        Args:
            to: Recipient email address or list of addresses
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            
        Returns:
            True if send successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement send_message()")


class GmailClient(EmailClient):
    """Client for connecting to Gmail"""
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize Gmail client
        
        Args:
            credentials: Dictionary with authentication credentials
            {
                "email": "user@gmail.com",
                "password": "app_password"  # Gmail app password
            }
        """
        super().__init__(credentials)
        self.imap = None
        self.smtp = None
        
    def connect(self) -> bool:
        """
        Connect to Gmail IMAP and SMTP servers
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to IMAP
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com")
            self.imap.login(self.credentials["email"], self.credentials["password"])
            
            # Connect to SMTP
            self.smtp = smtplib.SMTP("smtp.gmail.com", 587)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.credentials["email"], self.credentials["password"])
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Gmail: {str(e)}")
            self.disconnect()
            return False
            
    def disconnect(self) -> None:
        """Disconnect from Gmail IMAP and SMTP servers"""
        try:
            if self.imap:
                self.imap.logout()
                self.imap = None
                
            if self.smtp:
                self.smtp.quit()
                self.smtp = None
                
            self.connected = False
            
        except Exception as e:
            logger.error(f"Error disconnecting from Gmail: {str(e)}")
            
    def get_messages(self, folder: str = "INBOX", limit: int = 10, 
                    since: Optional[datetime] = None, search_criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from Gmail
        
        Args:
            folder: Folder name (default: "INBOX")
            limit: Maximum number of messages to return
            since: Only return messages since this date
            search_criteria: Search criteria for filtering messages
            
        Returns:
            List of message dictionaries
        """
        if not self.connected or not self.imap:
            if not self.connect():
                return []
                
        try:
            # Select folder
            self.imap.select(folder)
            
            # Build search criteria
            search_query = "(ALL)"
            
            if since:
                # Format date for IMAP search
                date_str = since.strftime("%d-%b-%Y")
                search_query = f'(SINCE "{date_str}")'
                
            if search_criteria:
                search_query = f'(SUBJECT "{search_criteria}" OR TEXT "{search_criteria}")'
                
            # Search messages
            _, data = self.imap.search(None, search_query)
            message_ids = data[0].split()
            
            # Sort message IDs in reverse order (newest first)
            message_ids = message_ids[::-1]
            
            # Limit number of messages
            message_ids = message_ids[:limit]
            
            # Fetch message data
            messages = []
            for msg_id in message_ids:
                try:
                    _, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    
                    # Parse email message
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract data
                    message = {
                        "id": msg_id.decode(),
                        "subject": self._decode_header(msg["Subject"]),
                        "from": self._decode_header(msg["From"]),
                        "to": self._decode_header(msg["To"]),
                        "date": self._decode_header(msg["Date"]),
                        "body": self._get_email_body(msg),
                        "html_body": self._get_email_body(msg, "html"),
                        "attachments": self._get_attachments(msg)
                    }
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.error(f"Error parsing message {msg_id}: {str(e)}")
                    continue
                    
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages from Gmail: {str(e)}")
            return []
            
    def send_message(self, to: Union[str, List[str]], subject: str, 
                    body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email message via Gmail
        
        Args:
            to: Recipient email address or list of addresses
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            
        Returns:
            True if send successful, False otherwise
        """
        if not self.connected or not self.smtp:
            if not self.connect():
                return False
                
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.credentials["email"]
            
            # Handle recipients
            if isinstance(to, list):
                msg["To"] = ", ".join(to)
                recipients = to
            else:
                msg["To"] = to
                recipients = [to]
                
            # Add plain text body
            msg.attach(MIMEText(body, "plain"))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
                
            # Send message
            self.smtp.sendmail(self.credentials["email"], recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message via Gmail: {str(e)}")
            return False
            
    def _decode_header(self, header: Optional[str]) -> str:
        """
        Decode email header
        
        Args:
            header: Email header to decode
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
            
        try:
            decoded_header = email.header.decode_header(header)
            parts = []
            
            for decoded_text, charset in decoded_header:
                if isinstance(decoded_text, bytes):
                    try:
                        if charset:
                            parts.append(decoded_text.decode(charset))
                        else:
                            parts.append(decoded_text.decode())
                    except:
                        parts.append(decoded_text.decode('utf-8', errors='replace'))
                else:
                    parts.append(decoded_text)
                    
            return "".join(parts)
            
        except Exception as e:
            logger.error(f"Error decoding header: {str(e)}")
            return header
            
    def _get_email_body(self, msg: email.message.Message, content_type: str = "plain") -> str:
        """
        Extract email body of specified content type
        
        Args:
            msg: Email message
            content_type: Content type to extract (plain or html)
            
        Returns:
            Body content as string
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                # Get content type
                part_content_type = part.get_content_type()
                
                if part_content_type == f"text/{content_type}":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                        break
                    except Exception as e:
                        logger.error(f"Error decoding email body: {str(e)}")
                        continue
                        
        elif msg.get_content_type() == f"text/{content_type}":
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception as e:
                logger.error(f"Error decoding email body: {str(e)}")
                
        return body
        
    def _get_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """
        Extract attachments from email message
        
        Args:
            msg: Email message
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            
            if "attachment" in content_disposition:
                try:
                    filename = part.get_filename()
                    
                    if filename:
                        # Clean up filename
                        filename = self._decode_header(filename)
                        
                        # Get content type
                        content_type = part.get_content_type()
                        
                        # Get attachment data
                        payload = part.get_payload(decode=True)
                        
                        attachment = {
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(payload)
                        }
                        
                        attachments.append(attachment)
                        
                except Exception as e:
                    logger.error(f"Error processing attachment: {str(e)}")
                    continue
                    
        return attachments


class OutlookClient(EmailClient):
    """Client for connecting to Outlook/Office 365"""
    
    def __init__(self, credentials: Dict[str, str]):
        """
        Initialize Outlook client
        
        Args:
            credentials: Dictionary with authentication credentials
            {
                "email": "user@outlook.com",
                "password": "password"
            }
        """
        super().__init__(credentials)
        self.imap = None
        self.smtp = None
        
    def connect(self) -> bool:
        """
        Connect to Outlook IMAP and SMTP servers
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Connect to IMAP
            self.imap = imaplib.IMAP4_SSL("outlook.office365.com")
            self.imap.login(self.credentials["email"], self.credentials["password"])
            
            # Connect to SMTP
            self.smtp = smtplib.SMTP("smtp.office365.com", 587)
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.credentials["email"], self.credentials["password"])
            
            self.connected = True
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to Outlook: {str(e)}")
            self.disconnect()
            return False
            
    def disconnect(self) -> None:
        """Disconnect from Outlook IMAP and SMTP servers"""
        try:
            if self.imap:
                self.imap.logout()
                self.imap = None
                
            if self.smtp:
                self.smtp.quit()
                self.smtp = None
                
            self.connected = False
            
        except Exception as e:
            logger.error(f"Error disconnecting from Outlook: {str(e)}")
            
    def get_messages(self, folder: str = "INBOX", limit: int = 10, 
                    since: Optional[datetime] = None, search_criteria: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get messages from Outlook
        
        Args:
            folder: Folder name (default: "INBOX")
            limit: Maximum number of messages to return
            since: Only return messages since this date
            search_criteria: Search criteria for filtering messages
            
        Returns:
            List of message dictionaries
        """
        if not self.connected or not self.imap:
            if not self.connect():
                return []
                
        try:
            # Select folder
            self.imap.select(folder)
            
            # Build search criteria
            search_query = "(ALL)"
            
            if since:
                # Format date for IMAP search
                date_str = since.strftime("%d-%b-%Y")
                search_query = f'(SINCE "{date_str}")'
                
            if search_criteria:
                search_query = f'(SUBJECT "{search_criteria}" OR TEXT "{search_criteria}")'
                
            # Search messages
            _, data = self.imap.search(None, search_query)
            message_ids = data[0].split()
            
            # Sort message IDs in reverse order (newest first)
            message_ids = message_ids[::-1]
            
            # Limit number of messages
            message_ids = message_ids[:limit]
            
            # Fetch message data
            messages = []
            for msg_id in message_ids:
                try:
                    _, msg_data = self.imap.fetch(msg_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    
                    # Parse email message
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract data
                    message = {
                        "id": msg_id.decode(),
                        "subject": self._decode_header(msg["Subject"]),
                        "from": self._decode_header(msg["From"]),
                        "to": self._decode_header(msg["To"]),
                        "date": self._decode_header(msg["Date"]),
                        "body": self._get_email_body(msg),
                        "html_body": self._get_email_body(msg, "html"),
                        "attachments": self._get_attachments(msg)
                    }
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.error(f"Error parsing message {msg_id}: {str(e)}")
                    continue
                    
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages from Outlook: {str(e)}")
            return []
            
    def send_message(self, to: Union[str, List[str]], subject: str, 
                    body: str, html_body: Optional[str] = None) -> bool:
        """
        Send email message via Outlook
        
        Args:
            to: Recipient email address or list of addresses
            subject: Email subject
            body: Plain text email body
            html_body: HTML email body (optional)
            
        Returns:
            True if send successful, False otherwise
        """
        if not self.connected or not self.smtp:
            if not self.connect():
                return False
                
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.credentials["email"]
            
            # Handle recipients
            if isinstance(to, list):
                msg["To"] = ", ".join(to)
                recipients = to
            else:
                msg["To"] = to
                recipients = [to]
                
            # Add plain text body
            msg.attach(MIMEText(body, "plain"))
            
            # Add HTML body if provided
            if html_body:
                msg.attach(MIMEText(html_body, "html"))
                
            # Send message
            self.smtp.sendmail(self.credentials["email"], recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message via Outlook: {str(e)}")
            return False
            
    def _decode_header(self, header: Optional[str]) -> str:
        """
        Decode email header
        
        Args:
            header: Email header to decode
            
        Returns:
            Decoded header string
        """
        if not header:
            return ""
            
        try:
            decoded_header = email.header.decode_header(header)
            parts = []
            
            for decoded_text, charset in decoded_header:
                if isinstance(decoded_text, bytes):
                    try:
                        if charset:
                            parts.append(decoded_text.decode(charset))
                        else:
                            parts.append(decoded_text.decode())
                    except:
                        parts.append(decoded_text.decode('utf-8', errors='replace'))
                else:
                    parts.append(decoded_text)
                    
            return "".join(parts)
            
        except Exception as e:
            logger.error(f"Error decoding header: {str(e)}")
            return header
            
    def _get_email_body(self, msg: email.message.Message, content_type: str = "plain") -> str:
        """
        Extract email body of specified content type
        
        Args:
            msg: Email message
            content_type: Content type to extract (plain or html)
            
        Returns:
            Body content as string
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                # Get content type
                part_content_type = part.get_content_type()
                
                if part_content_type == f"text/{content_type}":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        body = part.get_payload(decode=True).decode(charset, errors='replace')
                        break
                    except Exception as e:
                        logger.error(f"Error decoding email body: {str(e)}")
                        continue
                        
        elif msg.get_content_type() == f"text/{content_type}":
            try:
                charset = msg.get_content_charset() or 'utf-8'
                body = msg.get_payload(decode=True).decode(charset, errors='replace')
            except Exception as e:
                logger.error(f"Error decoding email body: {str(e)}")
                
        return body
        
    def _get_attachments(self, msg: email.message.Message) -> List[Dict[str, Any]]:
        """
        Extract attachments from email message
        
        Args:
            msg: Email message
            
        Returns:
            List of attachment dictionaries
        """
        attachments = []
        
        for part in msg.walk():
            content_disposition = str(part.get("Content-Disposition", ""))
            
            if "attachment" in content_disposition:
                try:
                    filename = part.get_filename()
                    
                    if filename:
                        # Clean up filename
                        filename = self._decode_header(filename)
                        
                        # Get content type
                        content_type = part.get_content_type()
                        
                        # Get attachment data
                        payload = part.get_payload(decode=True)
                        
                        attachment = {
                            "filename": filename,
                            "content_type": content_type,
                            "size": len(payload)
                        }
                        
                        attachments.append(attachment)
                        
                except Exception as e:
                    logger.error(f"Error processing attachment: {str(e)}")
                    continue
                    
        return attachments


def create_email_client(provider: str, credentials: Dict[str, str]) -> Optional[EmailClient]:
    """
    Create an email client for the specified provider
    
    Args:
        provider: Email provider ("gmail" or "outlook")
        credentials: Authentication credentials
        
    Returns:
        Email client instance or None if provider not supported
    """
    provider = provider.lower()
    
    if provider == "gmail":
        return GmailClient(credentials)
    elif provider in ["outlook", "office365"]:
        return OutlookClient(credentials)
    else:
        logger.error(f"Unsupported email provider: {provider}")
        return None