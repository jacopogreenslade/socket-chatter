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
    sockets.push(new SocketClient(`login-1-${i+1}`, "survey160", addMsg))
  }

  httpClient = new HttpClient();
  // Initial update
  tick();

  // Start the Spmmer GOT
  document.getElementById("start").onclick = startSpamming;

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

function teardown() {
  for (const s of sockets) {
    s.teardown();
  }
}

function tick() {
  console.log("Updating app...");

  // Get socket container, clear it, then create and populate socket list
  const socketContainerEl = document.getElementById("socket-agent-container");
  socketContainerEl.innerHTML = "";
  for (let s of sockets) {
    socketContainerEl.appendChild(createSocketRow(s));
  }
  
  // Get the socket counter, and update with active socket count
  const counterEl = document.getElementById("socket-counter")
  counterEl.innerHTML = sockets.filter(s => s.connected).length;
  
  // Stop here if there are no unprocessed msgs
  if (!messages.dirty) {
    return;
  }
  
  // Update message box
  const messageBoxEl = document.getElementById("message-box");
  // Loop through unprocessed messages (getNewMessageList), create html, and append it
  for (let m of messages.getNewMsgList()) {
    messageBoxEl.appendChild(createMessageRow(m.to, m.msgId, m.text, m.receivedAt));
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
