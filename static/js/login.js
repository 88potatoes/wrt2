document.addEventListener('DOMContentLoaded', function () {
    // Handle the form submission for session-based login and token generation
    document.getElementById('loginForm').addEventListener('submit', function (event) {
        event.preventDefault();  // Prevent default form submission

        console.log("Submitting form to /login for session-based login...");

        // Submit the form to Django's login endpoint
        const form = event.target;
        const username = form.querySelector('[name=username]').value;
        const password = form.querySelector('[name=password]').value;

        // Authenticate first with your custom login view if necessary (optional)
        fetch('/login', {
            method: 'POST',
            body: new FormData(form),
            headers: {
                'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
            }
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Login failed. Please check your credentials.');
                }
                return response.json();  // Proceed to fetch tokens after successful login
            })
            .then(data => {
                // Now fetch the tokens using /api/token/
                return fetch('/api/token/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({ username: username, password: password })
                });
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Token fetch failed. Please check your credentials.');
                }
                return response.json();  // Expecting a JSON response with tokens
            })
            .then(data => {
                // Store the access and refresh tokens in localStorage
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);

                // Redirect to the search page
                window.location.href = "/search_term";  // Update this to your desired URL
            })
            .catch(error => {
                document.getElementById('errorMessage').textContent = error.message;
                console.error('Error:', error);
            });
    });
});

document.addEventListener("DOMContentLoaded", function () {
    const createUserButton = document.getElementById("create-user-button");

    createUserButton.addEventListener("click", function () {
        console.log("Create User button clicked");
        window.location.href = "/create_user";
    });
});