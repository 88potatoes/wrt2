document.addEventListener('DOMContentLoaded', function () {


    // Function to refresh the access token
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

    // Function to validate the access token
    function validateAccessToken() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');
    
        // First, check if the refresh token is expired or missing
        if (!refreshToken || isTokenExpired(refreshToken)) {
            console.log("Refresh token expired or missing, redirecting to login...");
            localStorage.removeItem('access_token');  // Clear access token
            localStorage.removeItem('refresh_token');  // Clear refresh token
            window.location.href = "/";  // Redirect to login
            return;
        }
    
        // If refresh token is valid, check if the access token is expired
        if (!accessToken || isTokenExpired(accessToken)) {
            console.log("Access token expired. Attempting to refresh...");
            refreshAccessToken()
                .then(newAccessToken => {
                    console.log("Access token refreshed successfully.");
                    localStorage.setItem('access_token', newAccessToken);  // Update the access token
    
                    // Proceed to validate the new access token by making the API call
                    return fetch('/api/search-page/', {
                        method: 'GET',
                        headers: {
                            'Authorization': 'Bearer ' + newAccessToken,
                            'Content-Type': 'application/json'
                        }
                    });
                })
                .then(response => {
                    if (!response.ok) {
                        console.log("Token validation failed. Redirecting to login...");
                        window.location.href = "/";  // Redirect to login if token validation fails
                    } else {
                        console.log("Access token is valid.");
                    }
                })
                .catch(error => {
                    console.error('Error during token refresh or API call:', error);
                    window.location.href = "/";  // Redirect to login on error
                });
        } else {
            // If the access token is still valid, make the API call directly
            console.log("Access token is valid. Proceeding with the API call...");
            fetch('/api/search-page/', {
                method: 'GET',
                headers: {
                    'Authorization': 'Bearer ' + accessToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => {
                if (!response.ok) {
                    console.log("Token validation failed, redirecting to login...");
                    window.location.href = "/";  // Redirect if the token is invalid or expired
                } else {
                    console.log("Access token is valid.");
                }
            })
            .catch(error => {
                console.error('Error verifying token:', error);
                window.location.href = "/";  // Redirect on error
            });
        }
    }

    // Function to handle form submission
    function submitForm(event, apiUrl, formData, successCallback) {
        event.preventDefault();
        const accessToken = localStorage.getItem('access_token');
        
        if (!accessToken) {
            console.log("No access token found. Redirecting to login...");
            window.location.href = "/";
            return;
        }
    
        // Create a common request function
        const submitRequest = (token) => {
            return fetch(apiUrl, {
                method: "POST",
                headers: {
                    'Authorization': 'Bearer ' + token,
                    'Content-Type': 'application/json',
                    'X-CSRFToken': '{{ csrf_token }}'
                },
                body: JSON.stringify(formData)
            });
        };
    
        submitRequest(accessToken)
            .then(response => {
                if (response.status === 401) {
                    console.log("Access token expired. Attempting to refresh...");
                    return refreshAccessToken().then(newAccessToken => submitRequest(newAccessToken));
                }
                return response;
            })
            .then(response => response.ok ? response.json() : Promise.reject('Request failed'))
            .then(data => successCallback(data))
            .catch(error => {
                console.error('Error:', error);
                alert("Session expired. Please log in again.");
                window.location.href = "/";
            });
    }

    // Handle SearchForm submission
    const searchForm = document.getElementById('searchForm');
    searchForm.addEventListener('submit', function (event) {
        event.preventDefault();

        const formData = new FormData(searchForm);
        const searchText = formData.get('search_text');
        const startingLinks = formData.getAll('starting_links[]');

        // Debug
        console.log("Starting Links: ", startingLinks);
        console.log("Search Text: ", searchText);

        submitForm(event, '/api/search/', { search_text: searchText, starting_links: startingLinks }, (data) => {
            // given successful request, display data
            console.log("Data received from the server:", data);
            const searchResultsDiv = document.getElementById('searchResults');

            if (data.length > 0 && data[0].length > 0) {
                // clears previous results
                searchResultsDiv.innerHTML = '';

                const resultsTitle = document.createElement('h2');
                resultsTitle.classList.add('results');
                resultsTitle.textContent = 'Results - Strings Matched';
                searchResultsDiv.appendChild(resultsTitle);

                const table = document.createElement('table');
                table.classList.add('table', 'is-bordered', 'is-fullwidth', 'is-hoverable');
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Matched String</th>
                            <th>Page URL</th>
                        </tr>

                        <tr class="urlRange">
                            <th colspan="2">Results for Website Range "${startingLinks[0]}"</th>
                        </tr>
                    </thead>
                `;

                const tableBody = document.createElement('tbody');

                data[0].forEach(link => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${searchText}</td>
                        <td><a href="${link}" target="_blank">${link}</a></td>
                    `;
                    tableBody.appendChild(row);
                });

                table.appendChild(tableBody);
                searchResultsDiv.appendChild(table);
            } else if (data[0].length == 0) {
                searchResultsDiv.innerHTML = `
                <p>No results found!</p>
                `;
            } else if (data.message) {
                searchResultsDiv.innerHTML = `<p>${data.message}</p>`;
            }
        })
    });

    // Handle CrawlForm submission
    const crawlForm = document.getElementById('crawlForm');
    crawlForm.addEventListener('submit', function (event) {
        const formData = new FormData(crawlForm);
        const startingLinks = formData.getAll('starting_links[]');

        // Debug
        console.log("Starting Links: ", startingLinks);

        submitForm(event, '/api/crawl/', { starting_links: startingLinks }, (data) => {
            console.log(data);

            const crawlResultsDiv = document.getElementById('crawlResults');

            if (data.length > 0 && data[0].length > 0) {
                // clears previous results
                crawlResultsDiv.innerHTML = '';

                const resultsTitle = document.createElement('h2');
                resultsTitle.classList.add('results');
                resultsTitle.textContent = 'Results - Strings Matched';
                crawlResultsDiv.appendChild(resultsTitle);

                const table = document.createElement('table');
                table.classList.add('table', 'is-bordered', 'is-fullwidth', 'is-hoverable');
                table.innerHTML = `
                    <thead>
                        <tr>
                            <th>Matched String</th>
                            <th>Page URL</th>
                        </tr>

                        <tr class="urlRange">
                            <th colspan="2">Results for Website Range "${startingLinks[0]}"</th>
                        </tr>
                    </thead>
                `;

                const tableBody = document.createElement('tbody');

                data[0].forEach(link => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${searchText}</td>
                        <td><a href="${link}" target="_blank">${link}</a></td>
                    `;
                    tableBody.appendChild(row);
                });

                table.appendChild(tableBody);
                crawlResultsDiv.appendChild(table);
            } else if (data[0].length == 0) {
                crawlResultsDiv.innerHTML = `
                <p>No results found!</p>
                `;
            } else if (data.message) {
                crawlResultsDiv.innerHTML = `<p>${data.message}</p>`;
            }
        });
    });

    // Logout functionality
    const logoutLink = document.getElementById('logoutLink');
    logoutLink.addEventListener('click', function (event) {
        event.preventDefault();
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        console.log('Logged out, tokens cleared.');
        window.location.href = '/';
    });

    validateAccessToken();
});

// Checking token expiration
function isTokenExpired(token) {
    const payload = JSON.parse(atob(token.split('.')[1])); 
    const expiration = payload.exp * 1000; 
    return Date.now() > expiration;
}

// Tab switching function
function showTab(tabId) {
    var tabContents = document.getElementsByClassName("tab-content");
    for (var i = 0; i < tabContents.length; i++) {
        tabContents[i].style.display = "none";
    }
    document.getElementById(tabId).style.display = "block";

    var tabLinks = document.querySelectorAll(".tabs-is-centered ul li");
    tabLinks.forEach(function (link) {
        link.classList.remove("is-active");
    });
    document.querySelector(`.tabs-is-centered ul li a[onclick="showTab('${tabId}')"]`).parentNode.classList.add("is-active");
}

document.addEventListener('DOMContentLoaded', function () {
    // Handle adding input fields for Search Form
    const addSearchInputBtn = document.getElementById('addSearchInputBtn');
    const searchUrlInputContainer = document.getElementById('searchUrlInputContainer');

    addSearchInputBtn.addEventListener('click', function () {
        const newFieldDiv = document.createElement('div');
        newFieldDiv.classList.add('control');
        newFieldDiv.style.marginTop = '10px';

        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = "X";
        deleteBtn.classList.add("delete-btn");
        deleteBtn.addEventListener('click', () => {
            newFieldDiv.remove();
        })

        newFieldDiv.innerHTML = `
            <input class="input" type="text" name="starting_links[]" placeholder="Enter a URL defining the search range...">
        `;
        newFieldDiv.appendChild(deleteBtn);
        searchUrlInputContainer.appendChild(newFieldDiv);
    });

    // Handle adding input fields for Crawl Form
    const addCrawlInputBtn = document.getElementById('addCrawlInputBtn');
    const crawlUrlInputContainer = document.getElementById('crawlUrlInputContainer');

    addCrawlInputBtn.addEventListener('click', function () {
        const newFieldDiv = document.createElement('div');
        newFieldDiv.classList.add('control');
        newFieldDiv.style.marginTop = '10px';

        newFieldDiv.innerHTML = `
            <input class="input" type="text" name="starting_links[]" placeholder="Enter a URL defining the search range...">
        `;
        crawlUrlInputContainer.appendChild(newFieldDiv);
    });
});

function enableTooltip(tooltipIconId, tooltipTextId) {
    const tooltipIcon = document.getElementById(tooltipIconId);
    const tooltipText = tooltipIcon.querySelector('.tooltip');

    tooltipIcon.addEventListener('mouseenter', function () {
        tooltipText.classList.add('tooltip-visible');
    });

    tooltipIcon.addEventListener('mouseleave', function () {
        tooltipText.classList.remove('tooltip-visible');
    });
}

enableTooltip('tooltipIcon1');
enableTooltip('tooltipIcon2');
enableTooltip('tooltipIcon3');