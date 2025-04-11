#!/usr/bin/env python3
import os
import sys
from flask import Flask
from app import app

def list_routes():
    """List all routes in the application"""
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods))
        output.append(f"{rule} ({methods})")
    
    # Sort routes for easier reading
    output.sort()
    
    # Print routes
    for route in output:
        print(route)

if __name__ == "__main__":
    list_routes()