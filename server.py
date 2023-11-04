import eventlet
eventlet.monkey_patch()

import time
from random import choice, randint
from flask import Flask, request, Response, send_file, g, jsonify
from flask_socketio import SocketIO, join_room, leave_room



REDIS_HOST = "redis://localhost:6379"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", message_queue=REDIS_HOST, logger=True)

# Long running task
from concurrent.futures import ThreadPoolExecutor
executor = None


@socketio.on("connect")
def connect_socket():
    socket_ids.append(request.sid)
    print(socket_ids)

    app.logger.info(f'SOCKET CONNECTED {request.sid}')

@socketio.on('join_room')
def setup_connection(data):
    # Add this (the connection it came from) to the specified room.
    room = data["room"]
    userid = data["userid"]

    join_room(room)
    app.logger.info(f'JOIN ROOM (userid={userid},room={room})')

@socketio.on('leaveroom')
def shutdown_connection(data):  
    # Removes this (the connection it came from) to the specified room.
    room = data["room"]
    userid = data["userid"]

    leave_room(room)
    app.logger.info(f'LEAVE ROOM (userid={userid},room={room})')

@socketio.on("disconnect")
def socket_client_disconnected():
    socket_ids.remove(request.sid)
    app.logger.info(f"CLIENT DISCONNECTED {request.sid}")

@socketio.on_error()
def handle_error(e):
    app.logger.error(f"SOCKET.IO ERROR {e}")

socket_ids = []

from string import ascii_uppercase


def create_random_message(sid):
    s = ''.join(choice(ascii_uppercase) for i in range(12))
    return { "msgSid": sid, "text": s}

def send_messages(end_delay_seconds, msg_per_sec):
    """Send out msgs at the given rate and stop after the given amount of time"""
    app.logger.info("STARTED SPAMMER BOT")
    end = time.time() + end_delay_seconds
    while time.time() < end:
        for n in range(0, msg_per_sec):
            sid = socket_ids[randint(0, len(socket_ids)-1)]
            socketio.call("incoming", data=create_random_message(sid), to=sid, timeout=30)
            app.logger.info(f"EMIT MESSAGE sid={sid}")
        
        # Wait 1 second each time
        time.sleep(1)

    app.logger.info("ENDED SPAMMER BOT")
    

@app.route("/start/<count>")
def start(count: int):
    # Start spamming the clients with messages
    if len(socket_ids) == 0:
        return "No connected clients.", 400

    send_messages(60, 3)

    return "Done", 200

@app.route("/end")
def end_messaging(count: int):
    # Start spamming the clients with messages
    executor.shutdown()

    return "Done", 200


@app.route("/")
def ping():
    return "", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0')
