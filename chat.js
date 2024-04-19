function typeMessage(fullText, type) {
  let index = 0;
  let container = document.getElementById('chat-messages');
  let messageDiv = document.createElement('div');
  messageDiv.classList.add('chat-message', type);

  // Füge das Profilbild nur zu eingehenden Nachrichten hinzu
  if (type === 'incoming') {
    const profilePicUrl = document.getElementById('chat-container').getAttribute('data-profile-pic-url');
    messageDiv.innerHTML = `
      <img src="${profilePicUrl}" class="profile-pic">
      <span class="sender-name">Chat-bot</span>
    `;
    const textSpan = document.createElement('span');
    textSpan.classList.add('message-text');
    messageDiv.appendChild(textSpan);
    container.appendChild(messageDiv);

    // Tippeffekt für die Nachricht
    function typeStep() {
      if (index < fullText.length) {
        textSpan.textContent += fullText[index++];
        setTimeout(typeStep, 20);
      }
    }
    typeStep();
  }
}

  
function displayMessage(text, type) {
  var messagesContainer = document.getElementById('chat-messages');
  var messageDiv = document.createElement('div');
  messageDiv.classList.add('chat-message', type);

  if (type === 'incoming') {
    const profilePicUrl = document.getElementById('chat-container').getAttribute('data-profile-pic-url');
    messageDiv.innerHTML = `
      <img src="${profilePicUrl}" class="profile-pic">
      <span class="sender-name">Chat-bot</span>
      <span class="message-text">${text}</span>
    `;
  } else {
    // Add user profile picture and name for outgoing messages
    const userPicUrl = "images/User_1.png"; 
    messageDiv.innerHTML = `
      <img src="${userPicUrl}" class="profile-pic">
      <span class="sender-name">Du</span>
      <span class="message-text">${text}</span>
    `;
  }

  messagesContainer.appendChild(messageDiv);
  messagesContainer.scrollTop = messagesContainer.scrollHeight; // Scroll to the newest message element
}





// sendMessage-Funktion, die Typewriter-Effekt für ausgehende Nachrichten verwendet
function sendMessage() {
  
}

// EventListener für das Senden bei Eingabe von Enter
function checkForEnter(event) {
  if (event.keyCode === 13) {
    event.preventDefault(); // Verhindert einen Zeilenumbruch
    sendMessage();
  }
}

// Eventuell kannst du hier eine Logik hinzufügen, um "Schnelle Antworten" zu implementieren
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

// Adjust this function to handle input field growth and shrinkage
function adjustInputHeight() {
  const input = document.getElementById('chat-input');
  // Reset the height to minimum to allow for proper shrinkage
  input.style.height = '42px'; // Set to your desired minimum height
  if (input.scrollHeight > input.clientHeight) {
    input.style.height = input.scrollHeight + 'px';
  }
}

// Event listener for input event on the textarea
document.getElementById('chat-input').addEventListener('input', adjustInputHeight);

// Make sure this function is called after defining it to adjust the height on page load
adjustInputHeight();

document.getElementById('chat-send').addEventListener('click', sendMessage);

// Zeige eine Begrüßungsnachricht beim Laden der Seite an
setTimeout(function() {
  typeMessage("Hallo, wie kann ich dir heute helfen?", 'incoming');
}, 1500);
