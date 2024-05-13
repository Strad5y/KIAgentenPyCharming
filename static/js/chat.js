document.addEventListener("DOMContentLoaded", function() {
  const socket = io.connect('https://kiagentenpycharming.cloud/');

  const messageContainer = document.getElementById('chat-messages');
  const inputElement = document.getElementById('chat-input');
  const sendButton = document.getElementById('chat-send');

  // Funktion zum Anzeigen von Nachrichten mit Typisierungseffekt
  function typeMessage(fullText, type) {
      let index = 0;
      let messageDiv = document.createElement('div');
      messageDiv.classList.add('chat-message', type);

      // Füge das Profilbild nur zu eingehenden Nachrichten hinzu
      if (type === 'incoming') {
          messageDiv.innerHTML = `
            <img src="static/images/Chat-bot-profilbild.jpg" class="profile-pic">
            <span class="sender-name">FunkBot</span>
          `;
          const textSpan = document.createElement('span');
          textSpan.classList.add('message-text');
          messageDiv.appendChild(textSpan);
          messageContainer.appendChild(messageDiv);

          // Tippeffekt für die Nachricht
          function typeStep() {
              if (index < fullText.length) {
                  textSpan.textContent += fullText[index++];
                  setTimeout(typeStep, 20);
              }
          }
          typeStep();
      } else {
          messageDiv.innerHTML = `
            <img src="static/images/User_1.png" class="profile-pic">
            <span class="sender-name">Du</span>
            <span class="message-text">${fullText}</span>
          `;
          messageContainer.appendChild(messageDiv);
      }
      messageContainer.scrollTop = messageContainer.scrollHeight;
  }

  // Funktion zum Senden einer Nachricht
  function sendMessage() {
      const message = inputElement.value;
      if (message.trim().length > 0) {
          socket.emit('message', message);
          typeMessage(message, 'outgoing'); // Verwende typeMessage für ausgehende Nachrichten
          inputElement.value = '';
      }
  }

  // Nachrichten vom Server empfangen
  socket.on('message', function(msg) {
      typeMessage(msg, 'incoming'); // Verwende typeMessage für eingehende Nachrichten
  });

  sendButton.addEventListener('click', sendMessage);

  inputElement.addEventListener('keypress', function(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
          sendMessage();
          event.preventDefault();
      }
  });

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

    // Funktion zur Anpassung der Eingabefeldhöhe
  function adjustInputHeight() {
     const input = document.getElementById('chat-input');
    // Setzt die Höhe zurück, um eine korrekte Schrumpfung zu ermöglichen
    input.style.height = '42px'; // Setze auf die gewünschte Mindesthöhe
    if (input.scrollHeight > input.clientHeight) {
        input.style.height = input.scrollHeight + 'px';
    }
  }

  document.getElementById('chat-input').addEventListener('input', adjustInputHeight);
  adjustInputHeight(); // Stelle sicher, dass diese Funktion nach der Definition aufgerufen wird, um die Höhe beim Laden der Seite anzupassen


  // Zeige eine Begrüßungsnachricht beim Laden der Seite an
  setTimeout(function() {
      typeMessage("Hallo, wie kann ich dir heute helfen?", 'incoming');
  }, 1500);
});
