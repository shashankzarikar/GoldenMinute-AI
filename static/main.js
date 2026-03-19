document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const messageText = userInput.value.trim();
        if (!messageText) return;

        // Add user message to UI
        appendMessage(messageText, 'user-msg');
        userInput.value = '';

        // Add loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'loading';
        loadingDiv.textContent = 'GoldenMinute AI is processing...';
        loadingDiv.style.display = 'block';
        chatBox.appendChild(loadingDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            // Send request to backend
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: messageText })
            });

            const data = await response.json();
            
            // Remove loading indicator
            chatBox.removeChild(loadingDiv);

            if (response.ok) {
                appendMessage(data.reply, 'ai-msg');
            } else {
                appendMessage(data.error || 'An error occurred while connecting to the AI.', 'system-msg');
            }
            
        } catch (error) {
            // Remove loading indicator
            chatBox.removeChild(loadingDiv);
            appendMessage('Network error. Please try again.', 'system-msg');
            console.error('Error:', error);
        }
    });

    function appendMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${className}`;
        
        // Use textContent for safety, though we style it with white-space: pre-wrap
        messageDiv.textContent = text;
        
        chatBox.appendChild(messageDiv);
        
        // Auto-scroll to bottom
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
