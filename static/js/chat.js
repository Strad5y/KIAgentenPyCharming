const socket = io(); // Verbindet mit dem Socket.IO-Server

function typeMessage(fullText, type) {
  let index = 0;
  let container = document.getElementById('chat-messages');
  let messageDiv = document.createElement('div');
  messageDiv.classList.add('chat-message', type);

  const profilePicUrl = type === 'incoming' ?
                        document.getElementById('chat-container').getAttribute('data-profile-pic-url') :
                        "/static/images/User_1.png";

  messageDiv.innerHTML = `
    <img src="${profilePicUrl}" class="profile-pic">
    <span class="sender-name">${type === 'incoming' ? 'Chat-bot' : 'Du'}</span>
  `;
  const textSpan = document.createElement('span');
  textSpan.classList.add('message-text');
  messageDiv.appendChild(textSpan);
  container.appendChild(messageDiv);

  function typeStep() {
    if (index < fullText.length) {
      textSpan.textContent += fullText[index++];
      setTimeout(typeStep, 20);
    }
  }
  typeStep();
}

function displayMessage(text, type) {
  var messagesContainer = document.getElementById('chat-messages');
  var messageDiv = document.createElement('div');
  messageDiv.classList.add('chat-message', type);

  const profilePicUrl = type === 'incoming' ?
                        document.getElementById('chat-container').getAttribute('data-profile-pic-url') :
                        "/static/images/User_1.png";

  messageDiv.innerHTML = `
    <img src="${profilePicUrl}" class="profile-pic">
    <span class="sender-name">${type === 'incoming' ? 'Chat-bot' : 'Du'}</span>
    <span class="message-text">${text}</span>
  `;
  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

socket.on('message', function(msg) {
  displayMessage(msg, 'incoming'); // Verwendet displayMessage für sofortiges Anzeigen
});

function sendMessage(message) {
  if (message.trim() !== '') {
    socket.emit('message', message); // Sendet die Nachricht an den Server
    displayMessage(message, 'outgoing'); // Zeigt die Nachricht sofort im UI als ausgehende Nachricht
  }
}

function checkForEnter(event) {
  if (event.keyCode === 13) {
    event.preventDefault(); // Verhindert einen Zeilenumbruch
    sendMessage(event.target.value);
    event.target.value = ''; // Nachrichtenfeld leeren
  }
}

function adjustInputHeight() {
  const input = document.getElementById('chat-input');
  input.style.height = '42px'; // Setzt die Höhe auf ein Minimum
  if (input.scrollHeight > input.clientHeight) {
    input.style.height = input.scrollHeight + 'px'; // Passt die Höhe an den Inhalt an
  }
}

function addQuickReplies(options) {
  const container = document.getElementById('chat-messages');
  const repliesDiv = document.createElement('div');
  repliesDiv.classList.add('quick-replies');

  options.forEach(option => {
    const button = document.createElement('button');
    button.textContent = option.label;
    button.onclick = function() { sendMessage(option.message); };
    repliesDiv.appendChild(button);
  });

  container.appendChild(repliesDiv);
}

document.getElementById('chat-input').addEventListener('input', adjustInputHeight);
document.getElementById('chat-send').addEventListener('click', function() {
  sendMessage(document.getElementById('chat-input').value);
  document.getElementById('chat-input').value = ''; // Nachrichtenfeld leeren
});
document.getElementById('chat-input').addEventListener('keypress', checkForEnter);

setTimeout(function() {
  displayMessage("Hallo, wie kann ich dir heute helfen?", 'incoming');
}, 1500);