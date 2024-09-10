document.addEventListener('DOMContentLoaded', function () {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (accessToken && refreshToken) {
        const nextUrl = "/api/search-page/";
        window.location.href = nextUrl;
        return; 
    }

    // Handle the form submission using AJAX
    document.getElementById('loginForm').addEventListener('submit', function (event) {
        event.preventDefault();

        const username = document.querySelector('input[name="username"]').value;
        const password = document.querySelector('input[name="password"]').value;

        // Send login request to /api/token/ to get JWT tokens
        fetch("/api/token/", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify({ username: username, password: password })
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Login failed. Please check your credentials.');
                }
                return response.json();
            })
            .then(data => {
                // Store the access and refresh tokens
                localStorage.setItem('access_token', data.access);
                localStorage.setItem('refresh_token', data.refresh);

                // Redirect to the search page
                const nextUrl = "/api/search-page/";
                window.location.href = nextUrl;
            })
            .catch(error => {
                document.getElementById('errorMessage').textContent = error.message;
                console.error('Error:', error);
            });
    });
});