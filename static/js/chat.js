document.addEventListener("DOMContentLoaded", function() {
    let selectedModel = 'intel-neural-chat-7b';  // Default model

    const messageContainer = document.getElementById('chat-messages');
    const inputElement = document.getElementById('chat-input');
    const sendButton = document.getElementById('chat-send');

    function typeMessage(fullText, type) {
        let index = 0;
        let messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', type);

        if (type === 'incoming') {
            messageDiv.innerHTML = `
              <img src="static/images/Chat-bot-profilbild.jpg" class="profile-pic">
              <span class="sender-name">FunkBot</span>
            `;
            const textSpan = document.createElement('span');
            textSpan.classList.add('message-text');
            messageDiv.appendChild(textSpan);
            messageContainer.appendChild(messageDiv);

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

    function sendMessage() {
        const message = inputElement.value;
        if (message.trim().length > 0) {
            console.log(`Sending message: "${message}" with model: ${selectedModel}`);
            fetch('/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: message }),
            })
            .then(response => response.json())
            .then(data => {
                typeMessage(data.response, 'incoming');
            })
            .catch(error => {
                console.error('Error:', error);
            });
            typeMessage(message, 'outgoing');
            inputElement.value = '';
        }
    }

    sendButton.addEventListener('click', sendMessage);

    inputElement.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            sendMessage();
            event.preventDefault();
        }
    });

    function adjustInputHeight() {
       const input = document.getElementById('chat-input');
      input.style.height = '42px';
      if (input.scrollHeight > input.clientHeight) {
          input.style.height = input.scrollHeight + 'px';
      }
    }

    document.getElementById('chat-input').addEventListener('input', adjustInputHeight);
    adjustInputHeight();

    setTimeout(function() {
        typeMessage("Hallo, wie kann ich dir heute helfen?", 'incoming');
    }, 1500);

    // Event listener for model selection
    document.querySelectorAll('.dropdown-content a').forEach(item => {
        item.addEventListener('click', event => {
            selectedModel = event.target.getAttribute('data-model');
            console.log(`Selected model: ${selectedModel}`);
            alert(`Modell gewechselt zu: ${selectedModel}`);

            // Send a request to change the model on the server
            fetch('/set_model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model: selectedModel }),
            })
            .then(response => response.json())
            .then(data => {
                console.log(`Server response: ${data.status}, model: ${data.model}`);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
