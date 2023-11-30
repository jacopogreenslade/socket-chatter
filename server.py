import datetime
import logging

import eventlet
eventlet.monkey_patch()

import time
from random import choice, randint
from flask import Flask, request, Response, send_file, g, jsonify
from flask_socketio import SocketIO, join_room, leave_room


REDIS_HOST = "redis://localhost:6379"

app = Flask(__name__)

logging.basicConfig(filename="logs/socket.log", filemode="w", level=logging.WARNING)
logging.getLogger('socketio').setLevel(logging.ERROR)
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

    app.logger.warning(f'SOCKET CONNECTED {request.sid}')

@socketio.on('join_room')
def setup_connection(data):
    # Add this (the connection it came from) to the specified room.
    room = data["room"]
    userid = data["userid"]

    join_room(room)
    app.logger.warning(f'JOIN ROOM (userid={userid},room={room})')

@socketio.on('leaveroom')
def shutdown_connection(data):  
    # Removes this (the connection it came from) to the specified room.
    room = data["room"]
    userid = data["userid"]

    leave_room(room)
    app.logger.warning(f'LEAVE ROOM (userid={userid},room={room})')

@socketio.on("disconnect")
def socket_client_disconnected():
    socket_ids.remove(request.sid)
    print(socket_ids)
    app.logger.warning(f"CLIENT DISCONNECTED {request.sid}")

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
    app.logger.warning("STARTED SPAMMER BOT")
    end = time.time() + end_delay_seconds
    for t in range(0, end_delay_seconds, step):
        for i in range(0, msg_per_sec):
            if len(socket_ids) > 1:
                now = datetime.datetime.now()
                sid = socket_ids[randint(0, len(socket_ids)-1)]
                msg = create_random_message(sid)
                socketio.call("incoming", data=msg, to=sid)
                app.logger.warning(f"  EMIT {now.strftime('%m/%d/%Y %H:%M:%S')} Group {t+1}/{end_delay_seconds}, Msg {i+1}/{msg_per_sec} {msg['text']} sid {sid}")

        # Wait 1 second each time
        time.sleep(step)

    app.logger.warning("ENDED SPAMMER BOT")
    

@app.route("/start/<countArg>")
def start(countArg: int):
    # Start spamming the clients with messages
    if len(socket_ids) == 0:
        return "No connected clients.", 400
    count = int(countArg)
    send_messages(count, 3)

    return "Done", 200

@app.route("/clientLog", methods = ['POST'])
def clientLog():
    try:
        clientLogText = request.values['logText']
        response = trylog(clientLogText)
        return response
    except Exception as e:
        print(str(e))
        return "ERROR: "+str(e), 400
def trylog(clientLogText):
    '''
    Read server log for Message Emits
    For each emit, find the message text in the client.
    Validate the sid=cid
    Confirm ACK was received by server to
    Calculate elapsed time
    '''
    lines = clientLogText.split('\r\n')
    clientEvents = {}
    userMap = {}
    for cline in lines:
        # ['11/30/2023,', '08:24:11:', 'login-1-3', 'apZKxdBYr3eX1wLpAAAD', '-', 'ATWLJURNOBWD', '(5)']
        ldate, ltime, userid, cid, _, ctext,_  = cline.split()
        clientEvents[ctext] = (ldate[1:-1], ltime, userid, cid)
        if cid not in userMap:
            userMap[cid] = userid

    with open("logs/compare.txt", "w") as cscf, open("logs/socket.log") as slf:
        serverEvents = {}
        for sline in slf.readlines():
            # '  EMIT Set 3/10; Message 1/3, sid=CLI1NuFsMqU_fla-AAAB\n'
            if 'EMIT' in sline:
                pieces = sline.strip().split()
                _, _, sdate, stime, _, _, _, _, stext, _, sid = pieces
                suser = userMap[sid] if sid in userMap else sid
                setorappend(serverEvents, stext, [sdate, stime, suser, sid])
                if stext in clientEvents:
                    clientAck = clientEvents[stext]
                    if sid == clientAck[3]:
                        setorappend(serverEvents, stext, ['ClientACK', clientAck[0], clientAck[1]])
                    else:
                        setorappend(serverEvents, stext, ['ClientACK','NO',"NO"])

        for stext, events in serverEvents.items():
            outline = stext
            for event in events:
                if type(event) is list:
                    for elt in event:
                        outline += ' ' + elt
                else:
                    outline += ' ' + event

            cscf.write(outline+"\n")

    return "Done", 200

def setorappend(thedict:dict, key:str, val:list):
    if key in thedict:
        thedict[key].append(val)
    else:
        thedict[key] = val

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
