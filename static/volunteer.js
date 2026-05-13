document.addEventListener('DOMContentLoaded', () => {
    const volunteerForm = document.getElementById('volunteer-form');
    const volunteerMessage = document.getElementById('volunteer-message');
    const locationMessage = document.getElementById('location-message');
    const useLocationButton = document.getElementById('use-location');
    const latInput = document.getElementById('vol-lat');
    const lngInput = document.getElementById('vol-lng');

    if (!volunteerForm) {
        return;
    }

    function setLocationMessage(text) {
        if (locationMessage) {
            locationMessage.textContent = text;
        }
    }

    async function fillCurrentLocation() {
        if (!navigator.geolocation) {
            setLocationMessage('Geolocation is not supported by this browser.');
            return;
        }

        setLocationMessage('Fetching your location...');

        navigator.geolocation.getCurrentPosition(
            (position) => {
                if (latInput) {
                    latInput.value = position.coords.latitude.toFixed(6);
                }
                if (lngInput) {
                    lngInput.value = position.coords.longitude.toFixed(6);
                }
                setLocationMessage('Location updated.');
            },
            () => {
                setLocationMessage('Unable to fetch location. Allow location access.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    if (useLocationButton) {
        useLocationButton.addEventListener('click', fillCurrentLocation);
    }

    volunteerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const payload = {
            name: document.getElementById('vol-name').value.trim(),
            phone: document.getElementById('vol-phone').value.trim(),
            email: document.getElementById('vol-email').value.trim(),
            skill: document.getElementById('vol-skill').value.trim(),
            lat: latInput ? latInput.value.trim() : '',
            lng: lngInput ? lngInput.value.trim() : ''
        };

        const response = await fetch('/api/register-volunteer', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (volunteerMessage) {
            volunteerMessage.textContent = response.ok
                ? data.message
                : (data.error || 'Unable to register volunteer');
        }

        if (response.ok) {
            volunteerForm.reset();
        }
    });
});
