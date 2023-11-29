import eventlet
eventlet.monkey_patch()

import time
from random import choice, randint
from flask import Flask, request, Response, send_file, g, jsonify
from flask_socketio import SocketIO, join_room, leave_room



REDIS_HOST = "redis://localhost:6379"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", message_queue=REDIS_HOST,
                    logger=True, engineio_logger=True)

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
    print(socket_ids)
    app.logger.info(f"CLIENT DISCONNECTED {request.sid}")

@socketio.on_error()
def handle_error(e):
    app.logger.error(f"SOCKET.IO ERROR {e}")

socket_ids = []

from string import ascii_uppercase


def create_random_message(sid):
    s = ''.join(choice(ascii_uppercase) for i in range(12))
    return { "msgSid": sid, "text": s}

def send_messages(end_delay_seconds, msg_per_sec, step=1):
    """Send out msgs at the given rate and stop after the given amount of time"""
    app.logger.info("STARTED SPAMMER BOT")
    end = time.time() + end_delay_seconds
    for t in range(0, end_delay_seconds, step):
        for i in range(0, msg_per_sec):
            app.logger.info(f"MESSAGE SET {t}/{end_delay_seconds}")
            if len(socket_ids) > 1:
                sid = socket_ids[randint(0, len(socket_ids)-1)]
                socketio.call("incoming", data=create_random_message(sid), to=sid)
                app.logger.info(f"  EMIT MESSAGE {i}/{msg_per_sec}, sid={sid}")

        # Wait 1 second each time
        time.sleep(step)

    app.logger.info("ENDED SPAMMER BOT")
    

@app.route("/start/<countArg>")
def start(countArg: int):
    # Start spamming the clients with messages
    if len(socket_ids) == 0:
        return "No connected clients.", 400
    count = int(countArg)
    send_messages(count, 3)

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
    socketio.run(app, host='0.0.0.0', port=3000)
