document.addEventListener('DOMContentLoaded', () => {
    const greetings = [
        "Hallo! Wie kann ich dir heute helfen?",
        "Willkommen! Stell mir eine Frage zu deinem PDF.",
        "Hi! Was möchtest du über dein PDF wissen?",
        "Grüß dich! Wie kann ich dir mit deinem PDF helfen?"
    ];

    const urlParams = new URLSearchParams(window.location.search);
    const pdfFilename = urlParams.get('pdf');
    const pdfText = pdfDisplay.dataset.pdfText;

    const chatWindow = document.getElementById('chat-window');
    const pdfDisplay = document.getElementById('pdf-display');

    if (pdfFilename) {
        const iframe = document.createElement('iframe');
        iframe.src = `/uploads/${pdfFilename}`;
        iframe.classList.add('w-100', 'h-100');
        pdfDisplay.innerHTML = '';
        pdfDisplay.appendChild(iframe);

        // Zufälligen Begrüßungstext auswählen
        const randomGreeting = greetings[Math.floor(Math.random() * greetings.length)];
        const botMessageElement = document.createElement('div');
        botMessageElement.classList.add('message', 'bot-message');
        botMessageElement.innerHTML = `<img src="/static/images/Chat-bot-profilbild.jpg" alt="Bot" class="profile-pic"> <div>${randomGreeting}</div>`;
        chatWindow.appendChild(botMessageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    const sendButton = document.getElementById('send-button');
    const chatInput = document.getElementById('chat-input');

    sendButton.addEventListener('click', () => {
        const userMessage = chatInput.value.trim();

        if (userMessage === '') {
            return;
        }

        const userMessageElement = document.createElement('div');
        userMessageElement.classList.add('message', 'user-message');
        userMessageElement.textContent = userMessage;
        chatWindow.appendChild(userMessageElement);
        chatWindow.scrollTop = chatWindow.scrollHeight;

        // Clear input
        chatInput.value = '';

        // Simulate bot response after 1 second
        setTimeout(() => {
            const botResponse = 'Ich bin leider noch im Entwicklungsstadium und verstehe deine Frage nicht richtig. Kannst du sie anders formulieren?';
            const botMessageElement = document.createElement('div');
            botMessageElement.classList.add('message', 'bot-message');
            botMessageElement.innerHTML = `<img src="/static/images/Chat-bot-profilbild.jpg" alt="Bot" class="profile-pic"> <div>${botResponse}</div>`;
            chatWindow.appendChild(botMessageElement);
            chatWindow.scrollTop = chatWindow.scrollHeight;
        }, 1000);
    });

    const downloadJsonButton = document.getElementById('download-json-button');

    downloadJsonButton.addEventListener('click', () => {
        const data = {
            model: 'intel-neural-chat-7b',
            prompt: pdfText,
            max_tokens: 500
        };

        fetch('/extract-key-values', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(jsonData => {
            // Process the JSON data here
            console.log('Received JSON data:', jsonData);
            const jsonText = JSON.stringify(jsonData, null, 2);
            const blob = new Blob([jsonText], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'extracted_data.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error fetching JSON:', error);
        });
    });
});
