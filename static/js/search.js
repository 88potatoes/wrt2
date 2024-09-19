// Function to handle form submission
function submitForm(event, apiUrl, formData, successCallback) {
    event.preventDefault();
    const accessToken = localStorage.getItem('access_token');

    function submitRequest(token) {
        return fetch(apiUrl, {
            method: "POST",
            headers: {
                'Authorization': 'Bearer ' + token,
                'Content-Type': 'application/json',
                'X-CSRFToken': '{{ csrf_token }}'
            },
            body: JSON.stringify(formData)
        });
    }

    if (!accessToken) {
        console.log("No access token found. Redirecting to login...");
        window.location.href = "/"; // Redirect to login if no token
        return;
    }

    submitRequest(accessToken)
        .then(response => {
            if (response.ok) {
                console.log("Access token is valid. Processing response...");
                return response.json();
            } else if (response.status === 401) {
                console.log("Access token is invalid or expired. Attempting to refresh...");
                return refreshAccessToken().then(newAccessToken => {
                    console.log("Retrying request with new access token.");
                    return submitRequest(newAccessToken).then(retryResponse => {
                        if (retryResponse.ok) {
                            return retryResponse.json();
                        } else {
                            throw new Error('Retry failed.');
                        }
                    });
                });
            } else {
                console.log("RESPONSE DATA: " + response.data); // TODO Remove
                throw new Error('Something went wrong with the request.');
            }
        })
        .then(data => successCallback(data))
        .catch(error => console.error('Error:', error));
}

// Logout functionality
const logoutLink = document.getElementById('logoutLink');
logoutLink.addEventListener('click', function (event) {
    event.preventDefault();
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    console.log('Logged out, tokens cleared.');
    window.location.href = '/';
});

// Function to refresh the access token
function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    return fetch('/api/token/refresh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken })
    })
        .then(response => response.json())
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