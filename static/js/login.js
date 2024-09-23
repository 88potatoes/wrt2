console.log('login.js is loaded');

document.addEventListener('DOMContentLoaded', function () {
    // Handle the form submission for session-based login and token generation
    document.getElementById('loginForm').addEventListener('submit', function (event) {
        event.preventDefault();  // Prevent default form submission

        console.log("Submitting form to /login for session-based login and token generation...");

        // Submit the form to Django's custom login endpoint
        const form = event.target;
        const formData = new FormData(form);
        
        fetch('/login', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Session-based login failed.');
            }
            return response.json();  // Expecting a JSON response with tokens
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }

            // Store the access and refresh tokens in localStorage
            localStorage.setItem('access_token', data.access_token);
            localStorage.setItem('refresh_token', data.refresh_token);

            // Redirect to the search page
            window.location.href = "/search_term";
        })
        .catch(error => {
            document.getElementById('errorMessage').textContent = error.message;
            console.error('Error:', error);
        });
    });
});
