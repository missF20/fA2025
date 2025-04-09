"""
Print all available routes in the application
"""
import main

app = main.app

print("Available routes:")
for rule in app.url_map.iter_rules():
    methods = ','.join(rule.methods)
    print(f"{rule} ({methods})")