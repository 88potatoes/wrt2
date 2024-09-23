document.addEventListener('DOMContentLoaded', function () {
    const accessToken = localStorage.getItem('access_token');
    const refreshToken = localStorage.getItem('refresh_token');

    if (refreshToken && !isTokenExpired(refreshToken)) {
        // Refresh token is valid, check if access token is there and valid
        if (!accessToken || isTokenExpired(accessToken)) {
            console.log("Access token is missing or expired. Attempting to refresh...");
            refreshAccessToken(refreshToken)
                .then(newAccessToken => {
                    console.log("Access token refreshed successfully.");
                    window.location.href = "/api/search-page/";  // Redirect after refresh
                })
                .catch(error => {
                    console.error('Error refreshing access token:', error);
                    // Keep the user on the login page if refreshing fails
                });
        } else {
            console.log("Access token is valid. Redirecting...");
            window.location.href = "/api/search-page/";  // Redirect if access token is valid
        }
    } else {
        // Refresh token is expired or missing, stay on login page
        console.log("Refresh token is missing or expired. Staying on login page.");
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

// Function to check if token is expired
function isTokenExpired(token) {
    const payload = JSON.parse(atob(token.split('.')[1]));  // Decode the token payload
    const expiration = payload.exp * 1000;  // Convert exp from seconds to milliseconds
    return Date.now() > expiration;
}

// Function to refresh the access token if expired
function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken || isTokenExpired(refreshToken)) {
        console.log("Refresh token expired or missing, redirecting to login...");
        window.location.href = "/";
        return Promise.reject('No valid refresh token available');
    }

    return fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
    })
        .then(response => {
            if (!response.ok) {
                console.log("Failed to refresh token, redirecting to login...");
                window.location.href = "/";
                throw new Error('Failed to refresh token');
            }
            return response.json();
        })
        .then(data => {
            if (data.access) {
                console.log("New access token received:", data.access);
                localStorage.setItem('access_token', data.access);
                return data.access;
            } else {
                console.log("Failed to refresh token, redirecting to login...");
                window.location.href = "/";
                throw new Error('Failed to refresh token');
            }
        })
        .catch(error => {
            console.error('Error refreshing token:', error);
            window.location.href = "/";
            throw new Error('Error refreshing token');
        });
}

