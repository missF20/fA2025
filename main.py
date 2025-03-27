from app import app, socketio
import logging

logging.basicConfig(level=logging.DEBUG)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)
