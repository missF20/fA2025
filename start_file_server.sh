#!/bin/bash
export UPLOAD_SERVER_PORT=5005
python new_file_upload_server.py > file_server.log 2>&1 &
echo "File server started with PID $!"