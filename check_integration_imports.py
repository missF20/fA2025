#!/usr/bin/env python
"""
Check Integration Imports

A simple direct check if the email_integration_bp is being imported correctly
"""

import sys
import os
import logging

# Suppress all logging so we get clean output
logging.basicConfig(level=logging.ERROR)

# Directly print if email_integration_bp exists
try:
    from routes.integrations.email import email_integration_bp
    print("SUCCESS: email_integration_bp exists in routes.integrations.email")
    print(f"url_prefix: {email_integration_bp.url_prefix}")
except Exception as e:
    print(f"ERROR in email module: {str(e)}")

# Check if it's exported by the package
try:
    from routes.integrations import email_integration_bp
    print("\nSUCCESS: email_integration_bp is exported by routes.integrations")
except Exception as e:
    print(f"\nERROR in package export: {str(e)}")

print("\nDone")