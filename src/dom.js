
function createSocketRow (s) {
  const statusClass = s.connected ? "active" : "inactive";
  const item = document.createElement("div", {});
  
  item.innerHTML = `
  <div class='socket ${statusClass}' >
  <span class='name'>${s.userid}</span>
  <span class='id'>${s.id ? s.id : ""}</span>
  <span class='status'>${statusClass}</span>
  </div>
  `
  return item;
}

function createMessageRow (userId, msgId, text, receivedAt) {
  const item = document.createElement("div", {});
  
  item.innerHTML = `
  <div class='message'>
    <span class='name'>${userId}</span>
    <span class='id'>${msgId}</span>
    <span class='text'>${text}</span>
    <span class='text'>${receivedAt}</span>
  </div>
  `
  return item;
} 