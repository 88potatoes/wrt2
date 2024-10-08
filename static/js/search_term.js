const searchForm = document.getElementById('searchForm');
searchForm.addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent the default form submission
    const csrfToken = document.getElementById('csrfToken').value;
    const searchUrl = document.getElementById('searchUrl').value;

    const formData = new FormData(searchForm);
    const searchText = formData.get('search_text');
    const startingLinks = formData.getAll('starting_links[]'); // Ensure you're getting the right input
    const browserInfo = navigator.userAgent; // Use userAgent to get browser info

    fetch(searchUrl, {
        method: "POST",
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            search_text: searchText,
            starting_links: startingLinks,
            browser_info: browserInfo
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error('Network response was not ok');
        }
        return res.json(); // Call .json() method to parse response
    })
    .then(data => {
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
            data[0].forEach(result => {
                const [searchTerm, link] = result;
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${searchTerm}</td>
                    <td><a href="${link}" target="_blank">${link}</a></td>
                `;
                tableBody.appendChild(row);
            });

            console.log('Table of Results shown');

            table.appendChild(tableBody);
            searchResultsDiv.appendChild(table);

            console.log('Now adding buttons:');

            // Create export buttons
            const buttons = createExportButtons(data[0], data[1], data[2]);
            console.log("Search Results:", data[0]);
            console.log("Broken Links:", data[1]);
            console.log("Access Required Links:", data[2]);

            // Select the export buttons container
            const exportButtonsDiv = document.getElementById('exportButtons');

            // Clear any existing buttons before adding new ones
            exportButtonsDiv.innerHTML = '';

            // Append buttons to the export buttons div
            exportButtonsDiv.appendChild(buttons[0]);
            exportButtonsDiv.appendChild(buttons[1]);
            console.log('Buttons added to the export buttons div');
        } else if (data[0].length == 0) {
            // Create export buttons
            const buttons = createExportButtons(data[0], data[1], data[2]);
            console.log("Search Results:", data[0]);
            console.log("Broken Links:", data[1]);
            console.log("Access Required Links:", data[2]);

            // Select the export buttons container
            const exportButtonsDiv = document.getElementById('exportButtons');

            // Clear any existing buttons before adding new ones
            exportButtonsDiv.innerHTML = '';

            // Append buttons to the export buttons div
            exportButtonsDiv.appendChild(buttons[0]);
            exportButtonsDiv.appendChild(buttons[1]);
            
            searchResultsDiv.innerHTML = `
                <p>No match found!</p>
                `;
        } else if (data.message) {
            searchResultsDiv.innerHTML = `<p>${data.message}</p>`;
        }
    })
    .catch(error => {
        console.error('Error:', error); // Handle errors
    });
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

function exportResults(searchResults, brokenLinks, accessRequired, exportType) {
    const requestBody = {
        search_results: searchResults,
        broken_links: brokenLinks,
        access_required_links: accessRequired,
        export_type: exportType
    };

    console.log(requestBody);

    fetch("{% url 'download' %}", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}' // Include CSRF token
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        const filename = data.file_url.split('/').pop();
        window.location.href = `/download/${filename}/`;
    })
    .catch(error => console.error('Error:', error));
}

function createExportButtons(searchResults, accessRequired, brokenLinks) {
    const exportPdfButton = document.createElement('button');
    exportPdfButton.textContent = 'Export to PDF';
    exportPdfButton.classList.add('button', 'is-link', 'export-pdf');
    exportPdfButton.style.marginRight = '10px';
    exportPdfButton.addEventListener('click', () => {
        console.log('Export to PDF button clicked');
        exportResults(searchResults, brokenLinks, accessRequired, 'pdf');
    });

    const exportExcelButton = document.createElement('button');
    exportExcelButton.textContent = 'Export to Excel';
    exportExcelButton.classList.add('button', 'is-link', 'export-excel');
    exportExcelButton.addEventListener('click', () => {
        console.log('Export to Excel button clicked');
        exportResults(searchResults, brokenLinks, accessRequired, 'excel');
    });

    return [exportPdfButton, exportExcelButton];
}