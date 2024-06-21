document.addEventListener('DOMContentLoaded', () => {
    const sendButton = document.getElementById('send-button');
    const chatInput = document.getElementById('chat-input');
    const chatWindow = document.getElementById('chat-window');
    const pdfDisplay = document.getElementById('pdf-display');

    const greetings = [
        "Hallo! Wie kann ich dir heute helfen?",
        "Willkommen! Stell mir eine Frage zu deinem PDF.",
        "Hi! Was möchtest du über dein PDF wissen?",
        "Grüß dich! Wie kann ich dir mit deinem PDF helfen?"
    ];

    const urlParams = new URLSearchParams(window.location.search);
    const pdfFilename = urlParams.get('pdf');
    const pdfText = pdfDisplay.dataset.pdfText;

    if (pdfFilename) {
        const iframe = document.createElement('iframe');
        iframe.src = `/uploads/${pdfFilename}`;
        iframe.classList.add('w-100', 'h-100');
        pdfDisplay.innerHTML = '';
        pdfDisplay.appendChild(iframe);

        const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot-message');
        botMessageElement.innerHTML = `<div>${randomGreeting}</div>`;
        chatWindow.appendChild(botMessageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    const sendMessage = async () => {
        const message = chatInput.value;
        if (message.trim() !== '') {
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', 'user-message');
            messageElement.innerHTML = `<div>${message}</div>`;
            chatWindow.appendChild(messageElement);
            chatInput.value = '';
            chatWindow.scrollTop = chatWindow.scrollHeight;

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message, pdf_text: pdfText })
            });
            const data = await response.json();
            const botMessage = data.choices[0].message.content;

            const botMessageElement = document.createElement('div');
            botMessageElement.classList.add('message', 'bot-message');
            botMessageElement.innerHTML = `<div>${botMessage}</div>`;
            chatWindow.appendChild(botMessageElement);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }
    };

    sendButton.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();
            sendMessage();
        }
    });
});
