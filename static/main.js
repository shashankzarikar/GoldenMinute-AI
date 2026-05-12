document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');
    const mapContainer = document.getElementById('map-container');
    let leafletMap = null;
    let userMarker = null;
    let volunteerMarker = null;
    let connectionLine = null;

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
            showVolunteerMap(location, data.volunteer);
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

            const chatResponse = await chatRequest;
            const data = await chatResponse.json();

            // Remove loading indicator
            chatBox.removeChild(loadingDiv);

            if (chatResponse.ok) {
                appendMessage(data.reply, 'ai-msg');

                if (typeof data.emergency === 'boolean') {
                    appendStatusBadge(data.emergency);
                }

                if (data.emergency && locationData) {
                    await requestVolunteer(locationData);
                }
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

    function appendStatusBadge(isEmergency) {
        const badge = document.createElement('div');
        badge.className = `status-badge ${isEmergency ? 'status-emergency' : 'status-non-emergency'}`;
        badge.textContent = isEmergency ? 'Emergency' : 'Non-emergency';
        chatBox.appendChild(badge);
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

    function showVolunteerMap(userLocation, volunteer) {
        if (!mapContainer) {
            return;
        }

        mapContainer.style.display = 'block';

        if (!leafletMap) {
            leafletMap = L.map('map');

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OpenStreetMap contributors'
            }).addTo(leafletMap);
        }

        const userLatLng = [userLocation.lat, userLocation.lng];
        const volunteerLatLng = [volunteer.lat, volunteer.lng];

        if (userMarker) {
            userMarker.setLatLng(userLatLng);
        } else {
            userMarker = L.marker(userLatLng).addTo(leafletMap).bindPopup('You are here');
        }

        const volunteerPopup = `${volunteer.name} (${volunteer.phone})`;

        if (volunteerMarker) {
            volunteerMarker.setLatLng(volunteerLatLng).bindPopup(volunteerPopup);
        } else {
            volunteerMarker = L.circleMarker(volunteerLatLng, {
                color: '#e74c3c',
                fillColor: '#e74c3c',
                fillOpacity: 0.9,
                radius: 8
            }).addTo(leafletMap).bindPopup(volunteerPopup);
        }

        if (connectionLine) {
            connectionLine.setLatLngs([userLatLng, volunteerLatLng]);
        } else {
            connectionLine = L.polyline([userLatLng, volunteerLatLng], {
                color: '#e74c3c',
                weight: 3
            }).addTo(leafletMap);
        }

        const bounds = L.latLngBounds([userLatLng, volunteerLatLng]);
        leafletMap.fitBounds(bounds, { padding: [40, 40] });
        leafletMap.invalidateSize();
    }
});
