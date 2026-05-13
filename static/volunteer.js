document.addEventListener('DOMContentLoaded', () => {
    const volunteerForm = document.getElementById('volunteer-form');
    const volunteerMessage = document.getElementById('volunteer-message');

    if (!volunteerForm) {
        return;
    }

    volunteerForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const payload = {
            name: document.getElementById('vol-name').value.trim(),
            phone: document.getElementById('vol-phone').value.trim(),
            email: document.getElementById('vol-email').value.trim(),
            skill: document.getElementById('vol-skill').value.trim(),
            lat: document.getElementById('vol-lat').value.trim(),
            lng: document.getElementById('vol-lng').value.trim()
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
