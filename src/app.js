let tickIntervalId;
let messages;
let sockets;

function addMsg(to, msgId, text, receivedAt) {
  messages.add({to, msgId, text, receivedAt});
}

function initApp() {
  console.log("Hello HTML");

  // Set socket counter to 0
  const counter = document.getElementById("socket-counter")
  counter.innerHTML = 0;

  // Init messages 
  messages = new Messages();
  sockets = [];

  const amount = 5;
  for (let i = 0; i < amount; i++) {
    sockets.push([`login-1-${i+1}`, new SocketClient(`login-1-${i+1}`, "survey160", addMsg)])
  }

  httpClient = new HttpClient();
  // Initial update
  tick();

  document.getElementById("start").onclick = startSpamming;
  document.getElementById("done").onclick = shipLog;
  document.getElementById("clear").onclick = () => document.getElementById("message-box").innerText = "";

  // Destroy all socket connections when done
  document.getElementById("close").onclick = teardown;
  // Update app every second
  tickIntervalId = window.setInterval(tick, 1000);
  
  // Testing repeating incoming msg
  // let msgInterval = window.setInterval(() => {
  //   const id = Math.random().toString(36).slice(2, 7);
  //   sockets[0].incomingHandler({msgId: id, text: "this is a sample text!"});
  // }, 3000)
}

const startSpamming = () => {
  httpClient.start();
}

const shipLog = () => {
  httpClient.done();
}

function teardown() {
  for (const s of sockets) {
    s[1].teardown();
  }
}

function tick() {
  console.log("Updating app...");
  // Make the server check for lost acknowledgements
    httpClient.checkAck();

  // Get socket container, clear it, then create and populate socket list
  const socketContainerEl = document.getElementById("socket-agent-container");
  socketContainerEl.innerHTML = "";
  for (let s of sockets) {
    socketContainerEl.appendChild(createSocketRow(s[1]));
  }
  
  // Get the socket counter, and update with active socket count
  const counterEl = document.getElementById("socket-counter")
  counterEl.innerHTML = sockets.filter(s => s[1].connected).length;
  
  // Stop here if there are no unprocessed msgs
  if (!messages.dirty) {
    return;
  }
  
  // Update message box
  const messageBoxEl = document.getElementById("message-box");
  // Loop through unprocessed messages (getNewMessageList), create html, and append it

  // Find index of socket
  for (let m of messages.getNewMsgList()) {
    for (var i in sockets) {
      if (m.to === sockets[i][0]) {
        break;
      }
    }
    var rDate = new Date(m.receivedAt);
    const dateOpt = {timeZone: 'America/New_York', hourCycle: 'h23'};
    messageBoxEl.appendChild(createMessageRow(i, m.to, m.msgId, m.text, rDate.toLocaleString('en-US', dateOpt)));
  }
  // mark all messages processed
  messages.setClean();

  // Scroll to the bottom of the messages list
  messageBoxEl.lastChild.scrollIntoView();
}

if (typeof window !== "undefined") {
  window.onunload = teardown;
} else {
  print("No window");
}

// Actual socket logic
