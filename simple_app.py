from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "name": "Dana AI API",
        "version": "1.0.0",
        "status": "online",
        "message": "This is a simplified version of the Dana AI API."
    })

@app.route('/api')
def api_index():
    return jsonify({
        "routes": [
            "/api/status",
            "/api/knowledge",
            "/api/integrations"
        ],
        "documentation": "See API_REFERENCE.md for full documentation"
    })

@app.route('/api/status')
def status():
    return jsonify({
        "status": "online",
        "database": "configured",
        "services": {
            "ai": "available",
            "slack": "configured",
            "email": "available"
        }
    })

@app.route('/integrations')
def integrations():
    integrations_list = [
        {
            "id": "slack",
            "name": "Slack",
            "description": "Connect to your Slack workspace",
            "status": "active",
            "icon": "slack-icon.svg"
        },
        {
            "id": "zendesk",
            "name": "Zendesk",
            "description": "Integrate with your Zendesk account",
            "status": "available",
            "icon": "zendesk-icon.svg"
        },
        {
            "id": "shopify",
            "name": "Shopify",
            "description": "Connect to your Shopify store",
            "status": "available",
            "icon": "shopify-icon.svg"
        }
    ]
    
    return jsonify({"integrations": integrations_list})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)