const SOCKET_SERVER_URL = "http://localhost:3000";

class HttpClient {
  start = () => {
    const Http = new XMLHttpRequest();
    const url=`${SOCKET_SERVER_URL}/start/3`;
    Http.open("GET", url);
    Http.send();

    Http.onreadystatechange = (e) => {
      console.log(Http.responseText)
    }
  }
}

class SocketClient {
  constructor(userid, room, addMsgToList) {
    this.userid = userid;
    this.room = room;
    this.id = null;
    this.connected = false;
    this.addMsgToList = addMsgToList

    // this.socket = io(SOCKET_SERVER_URL, {
    //   "force new connection": false,
    //   transports: ["websocket"],
    // });

    this.socket = io.connect(SOCKET_SERVER_URL, {
      "force new connection": false,
      transports: ["websocket"],
    });

    const handlers = [{ eventName: "connect", handler: this.connectHandler }, {eventName: "incoming", handler: this.incomingHandler}];

    handlers.forEach((h) => {
      this.socket.on(h.eventName, h.handler);
    });
  }

  connectHandler = () => {
    this.connected = true;
    this.socket.emit("join_room", {
      userid: this.userid,
      room: this.room,
      socketId: this.id,
    });
    
    this.id = this.socket.id;
    console.log(
      "Socket connection made. Joined room: ",
      this.room,
      "socket id: ",
      this.id
    );
  };

  incomingHandler = (data, callback) => {
    // console.log(a);
    const { msgSid, text } = data;
    console.log("Incoming message received by socket id: ", this.id,", message id: ", msgSid, ", text", text);

    this.addMsgToList(this.userid, msgSid, text, Date());
    
    callback();
  }

  teardown = () => {
    this.socket.emit("leave_room", {
      userid: this.userid,
      room: this.room,
    });
    this.socket.disconnect();
    this.connected = false;
    this.id = null;
  }

}


class Messages {
  constructor() {
    this.messages = [];
    this.dirty = false;
    this.currentIndex = 0;
  }
  
  add(msg) {
    this.messages.push(msg);

    if (!this.dirty) {
      this.dirty = true;
    }
  }

  getNewMsgList() {
    if (this.dirty) {
      return this.messages.slice(this.currentIndex);
    }
    return [];
  }

  setClean () {
    this.currentIndex = this.messages.length;
    this.dirty = false;
  }
}
