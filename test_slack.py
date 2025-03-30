import json
import slack
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test-slack-status')
def test_slack_status():
    status = slack.check_slack_status()
    return jsonify(status)

@app.route('/test-slack-message')
def test_slack_message():
    result = slack.post_message("Test message from Dana AI Platform")
    return jsonify(result)

@app.route('/test-slack-history')
def test_slack_history():
    result = slack.get_channel_history(limit=5)
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)