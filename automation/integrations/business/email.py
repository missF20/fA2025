"""
Email Integration for Business Operations

This module provides email sending capabilities for various business operations
such as customer support, notifications, and marketing communications.
"""

import os
import logging
import smtplib
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Set up logging
logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "notifications@dana-ai.com")

async def send_email(to_email, subject, message, from_email=None, cc=None, bcc=None, attachments=None):
    """
    Send a plain text email
    
    Args:
        to_email: Recipient email or list of emails
        subject: Email subject
        message: Email message (plain text)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        cc: Carbon copy recipient(s)
        bcc: Blind carbon copy recipient(s)
        attachments: List of attachment file paths
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    return await send_html_email(
        to_email=to_email,
        subject=subject,
        html_message=f"<p>{message}</p>",
        from_email=from_email,
        cc=cc,
        bcc=bcc,
        attachments=attachments
    )

async def send_html_email(to_email, subject, html_message, from_email=None, cc=None, bcc=None, attachments=None):
    """
    Send an HTML email
    
    Args:
        to_email: Recipient email or list of emails
        subject: Email subject
        html_message: Email message (HTML)
        from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
        cc: Carbon copy recipient(s)
        bcc: Blind carbon copy recipient(s)
        attachments: List of attachment file paths
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Use mock email sending in development if no SMTP credentials
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured. Would have sent email:")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Message: {html_message[:100]}...")
        return True
    
    # Get sender email
    sender = from_email or DEFAULT_FROM_EMAIL
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    
    # Handle recipients
    if isinstance(to_email, list):
        msg['To'] = ', '.join(to_email)
    else:
        msg['To'] = to_email
    
    # Handle CC
    if cc:
        if isinstance(cc, list):
            msg['Cc'] = ', '.join(cc)
        else:
            msg['Cc'] = cc
    
    # Handle BCC
    if bcc:
        if isinstance(bcc, list):
            msg['Bcc'] = ', '.join(bcc)
        else:
            msg['Bcc'] = bcc
    
    # Add HTML content
    msg.attach(MIMEText(html_message, 'html'))
    
    # Add plain text alternative (simplified from HTML)
    plain_text = html_message.replace('<p>', '').replace('</p>', '\n\n')
    plain_text = plain_text.replace('<br>', '\n').replace('<br/>', '\n')
    plain_text = plain_text.replace('<strong>', '').replace('</strong>', '')
    plain_text = plain_text.replace('<em>', '').replace('</em>', '')
    plain_text = plain_text.replace('&nbsp;', ' ')
    msg.attach(MIMEText(plain_text, 'plain'))
    
    # Add attachments
    if attachments:
        for attachment in attachments:
            try:
                with open(attachment, 'rb') as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment))
                    part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment)}"'
                    msg.attach(part)
            except Exception as e:
                logger.error(f"Failed to attach {attachment}: {e}")
    
    # Send email asynchronously
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _send_email_sync, msg, to_email, cc, bcc, sender)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def _send_email_sync(msg, to_email, cc, bcc, sender):
    """
    Send email synchronously
    
    Args:
        msg: Email message
        to_email: Recipient email(s)
        cc: Carbon copy recipient(s)
        bcc: Blind carbon copy recipient(s)
        sender: Sender email
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    try:
        # Start connection
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Prepare recipients list
        recipients = []
        if isinstance(to_email, list):
            recipients.extend(to_email)
        else:
            recipients.append(to_email)
        
        if cc:
            if isinstance(cc, list):
                recipients.extend(cc)
            else:
                recipients.append(cc)
        
        if bcc:
            if isinstance(bcc, list):
                recipients.extend(bcc)
            else:
                recipients.append(bcc)
        
        # Send email
        server.sendmail(sender, recipients, msg.as_string())
        
        # Close connection
        server.quit()
        
        logger.info(f"Email sent to {to_email}: {msg['Subject']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False