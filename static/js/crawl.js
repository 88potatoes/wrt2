// Handle CrawlForm submission
const crawlForm = document.getElementById('crawlForm');
crawlForm.addEventListener('submit', function (event) {
    event.preventDefault();
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