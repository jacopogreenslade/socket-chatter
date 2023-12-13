import json
from copy import deepcopy
import datetime
import logging
import socket

import eventlet
eventlet.monkey_patch()

import time
from random import choice, randint
from flask import Flask, request, Response, send_file, g, jsonify
from flask_socketio import SocketIO, join_room, leave_room, socketio as fsio

REDIS_HOST = "redis://localhost:6379"

app = Flask(__name__)
# Create a stream handler to add timestamp to log messages
formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
app.logger.addHandler(stream_handler)


logging.basicConfig(filename="logs/socket.log", filemode="w", level=logging.WARNING)
logging.getLogger('socketio').setLevel(logging.ERROR)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*", message_queue=REDIS_HOST,
                    logger=True, engineio_logger=True, ping_timeout=10, ping_interval=10)

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
    app.logger.error(f"SOCKET.IO ERROR FFFFF {e}")

socket_ids = []
open_msgs = {}

from string import ascii_uppercase


def create_random_message(sid):
    s = ''.join(choice(ascii_uppercase) for i in range(12))
    return { "msgSid": sid, "text": s}

def send_messages(end_delay_seconds:int, msg_per_sec:int, method:str, step=1):
    """Send out msgs at the given rate and stop after the given amount of time"""
    app.logger.warning("STARTED SPAMMER BOT")
    end = time.time() + end_delay_seconds
    for t in range(0, end_delay_seconds, step):
        for i in range(0, msg_per_sec):
            if len(socket_ids) > 1:
                now = datetime.datetime.now()
                sid = socket_ids[randint(0, len(socket_ids)-1)]
                msg = create_random_message(sid)
                if method == 'call':
                    # For call() must catch the Timeout exception to know if you must keep retrying
                    countdown = 3
                    while countdown > 0:
                        try:
                            app.logger.warning(f"  SEND-CALL {now.strftime('%m/%d/%Y %H:%M:%S')} Group {t+1}/{end_delay_seconds}, Msg {i+1}/{msg_per_sec} {msg['text']} sid {sid}")
                            socketio.call("incoming", data=msg, to=sid, timeout=10)
                        except fsio.exceptions.TimeoutError as te:
                            countdown -= 1 # Decrement
                            app.logger.warning(f"CALL-TIMEOUT {4-countdown} {now.strftime('%m/%d/%Y %H:%M:%S')} Msg {msg['text']}  ")
                        else:
                            countdown = -1 # Set to SUCCESS
                            app.logger.warning(f"CALL-ACK {now.strftime('%m/%d/%Y %H:%M:%S')} Msg {msg['text']}")
                    if countdown == 0:
                        app.logger.warning(f"CALL-UNACKED {now.strftime('%m/%d/%Y %H:%M:%S')} Msg {msg['text']}")

                else:
                    # For emit() there is no timeout. Keep track of Acknowledgement by the callback
                    open_msgs[msg['text']] = [now, sid, json.dumps(msg), 0]
                    app.logger.warning(f"  SEND-EMIT {now.strftime('%m/%d/%Y %H:%M:%S')} Group {t+1}/{end_delay_seconds}, Msg {i+1}/{msg_per_sec} {msg['text']} sid {sid}")
                    socketio.emit("incoming", data=msg, to=sid, callback=emit_callback)

                    # Re-send all unacknowledged emits but wait 1s for this one to acknowledge
                    time.sleep(1)
                    msgs_in_process = list(open_msgs.items())
                    if len(msgs_in_process) > 0:
                        for msgtext, msgdetail in msgs_in_process:
                            if msgdetail[3] < 10:
                                time.sleep(0.5)
                                msgdetail[3] = msgdetail[3] + 1
                                print("      RE-EMIT-P: " + msgtext)
                                socketio.emit("incoming", data=json.loads(msgdetail[2]), to=msgdetail[1], callback=emit_callback)
                            else:
                                app.logger.warning(f"EMIT-UNACKED {now.strftime('%m/%d/%Y %H:%M:%S')} Msg {msg['text']}")
                                del open_msgs[msgtext]

        # Wait 1 second each time
        time.sleep(step)

    app.logger.warning("ENDED SPAMMER BOT")

def emit_callback(*args):
    ack_msg = args[0]
    if ack_msg in open_msgs:
        now = datetime.datetime.now()
        app.logger.warning(f"EMIT-ACK {now.strftime('%m/%d/%Y %H:%M:%S')} Msg {ack_msg}")
        del open_msgs[ack_msg]


@app.route("/start", methods = ['GET'])
def start():
    # Start spamming the clients with messages
    if len(socket_ids) == 0:
        return "No connected clients.", 400
    count = int(request.values['count'])
    method = request.values['method']
    send_messages(count, 3, method)

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
    method = "????"
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
        ackedMsgs = []
        noackedMsgs = []
        for sline in slf.readlines():
            # '  EMIT Set 3/10; Message 1/3, sid=CLI1NuFsMqU_fla-AAAB\n'
            if ('SEND-CALL' in sline) or ('SEND-EMIT' in sline):
                pieces = sline.strip().split()
                try:
                    _, method, sdate, stime, _, _, _, _, stext, _, sid = pieces
                except:
                    print(pieces)
                suser = userMap[sid] if sid in userMap else sid
                setorappend(serverEvents, stext, ['Sent', sdate, stime, suser, sid])
                if stext in clientEvents:
                    clientAck = clientEvents[stext]
                    if sid == clientAck[3]:
                        setorappend(serverEvents, stext, ['ClientACK', clientAck[0], clientAck[1]])
                    else:
                        setorappend(serverEvents, stext, ['NOClientACK','NO',"NO"])
            elif 'EMIT-ACK' in sline:
                pieces = sline.strip().split()
                _, adate, atime, _, stext = pieces
                setorappend(serverEvents, stext, ['EmitACK', adate, atime])
                ackedMsgs.append(stext)
            elif 'EMIT-UNACKED' in sline:
                pieces = sline.strip().split()
                _, adate, atime, _, stext = pieces
                setorappend(serverEvents, stext, ['NOEmitACK', adate, atime])
                noackedMsgs.append(stext)
            elif 'CALL-ACK' in sline:
                pieces = sline.strip().split()
                _, adate, atime, _, stext = pieces
                setorappend(serverEvents, stext, ['CallACK', adate, atime])
                ackedMsgs.append(stext)
            elif 'CALL-TIMEOUT' in sline:
                pieces = sline.strip().split()
                _, timeoutcounter, adate, atime, _, stext = pieces
                setorappend(serverEvents, stext, ['Call-timer '+timeoutcounter, adate, atime])
            elif 'CALL-UNACKED' in sline:
                pieces = sline.strip().split()
                _, adate, atime, _, stext = pieces
                setorappend(serverEvents, stext, ['NOCallACK ', adate, atime])
                noackedMsgs.append(stext)

        cscf.write(method + "\n")
        cscf.write(f"A: {len(ackedMsgs)}\n")
        cscf.write(f"N: {len(noackedMsgs)}\n")
        cscf.write(f"T: {len(ackedMsgs)+len(noackedMsgs)}\n")
        cscf.write("\n")
        for stext, events in serverEvents.items():
            outline = stext
            for event in events:
                for elt in event:
                    outline += ' ' + elt
                outline += ';'

            cscf.write(outline+"\n")

    return "Done", 200

def setorappend(thedict:dict, key:str, val:list):
    if key in thedict:
        thedict[key].append(val)
    else:
        thedict[key] = [val]

@app.route("/end")
def end_messaging(count: int):
    # Stop long running task run
    executor.shutdown()

    return "Done", 200

@app.route("/")
def ping():
    return "", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)
