
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

let msgCount = {}
function createMessageRow (n, userId, msgId, text, receivedAt) {
  const item = document.createElement("div", {});

  if (n in msgCount) {
    msgCount[n]++;
  } else {
    msgCount[n] = 1;
  }

  const spacing = '&nbsp;&nbsp;&nbsp;'.repeat(n+1);
  item.innerHTML = `
  <div class='message'>
    <span class='text'>${receivedAt}:</span>${spacing}
    <span class='name'>${userId}</span>&nbsp;&nbsp;<span class='text'>${text}</span>
    <span> (${msgCount[n]})</span>
  </div>
  `
//    <span class='id'>${msgId}</span>
  return item;
} 