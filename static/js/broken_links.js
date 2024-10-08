// Handle CrawlForm submission
const crawlForm = document.getElementById('crawlForm');
crawlForm.addEventListener('submit', function (event) {
    event.preventDefault();
    const csrfToken = document.getElementById('csrfToken').value;
    const crawlUrl = document.getElementById('crawlUrl').value;

    const formData = new FormData(crawlForm);
    const starting_links = formData.getAll('starting_links[]');
    const browser_info = navigator.userAgent;

    // Debug
    console.log("Starting Links: ", starting_links);

    fetch(crawlUrl, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            starting_links,
            browser_info
        })
    })
    .then(response => response.json())
    .then((data) => {
        console.log("data: " + data); 
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
                        <th colspan="2">Results for Website Range "${starting_links[0]}"</th>
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