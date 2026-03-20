document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');

    function getUserLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocation is not supported by this browser.'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    });
                },
                (error) => {
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }
            );
        });
    }

    async function requestVolunteer(location) {
        const response = await fetch('/api/find-volunteer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ lat: location.lat, lng: location.lng })
        });

        const data = await response.json();

        if (response.ok && data.volunteer) {
            appendVolunteerAlert(data.volunteer);
        } else {
            appendMessage(data.error || 'Unable to find a volunteer right now.', 'system-msg');
        }
    }

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
            let locationData = null;

            try {
                locationData = await getUserLocation();
            } catch (locationError) {
                appendMessage('Location not available. Volunteer search may be limited.', 'system-msg');
                console.warn('Location error:', locationError);
            }

            const chatPayload = { message: messageText };

            if (locationData) {
                chatPayload.lat = locationData.lat;
                chatPayload.lng = locationData.lng;
            }

            const chatRequest = fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(chatPayload)
            });

            const volunteerRequest = locationData
                ? requestVolunteer(locationData)
                : Promise.resolve();

            const [chatResponse] = await Promise.all([chatRequest, volunteerRequest]);
            const data = await chatResponse.json();

            // Remove loading indicator
            chatBox.removeChild(loadingDiv);

            if (chatResponse.ok) {
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

    function appendVolunteerAlert(volunteer) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'message volunteer-alert';

        const title = document.createElement('div');
        title.className = 'volunteer-title';
        title.textContent = '🚨 Nearest Volunteer Found!';
        alertDiv.appendChild(title);

        const addLine = (label, value, valueClass) => {
            const line = document.createElement('div');
            line.className = 'volunteer-line';

            const labelSpan = document.createElement('span');
            labelSpan.className = 'volunteer-label';
            labelSpan.textContent = `${label} `;

            const valueSpan = document.createElement('span');
            if (valueClass) {
                valueSpan.className = valueClass;
            }
            valueSpan.textContent = value;

            line.appendChild(labelSpan);
            line.appendChild(valueSpan);
            alertDiv.appendChild(line);
        };

        addLine('Name:', volunteer.name, 'volunteer-name');
        addLine('Skill:', volunteer.skill);
        addLine('Distance:', `${volunteer.distance_km} km`);
        addLine('Phone:', volunteer.phone);

        const footer = document.createElement('div');
        footer.className = 'volunteer-footer';
        footer.textContent = 'Please call immediately!';
        alertDiv.appendChild(footer);

        chatBox.appendChild(alertDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});
