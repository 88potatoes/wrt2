from typing import List
import urllib.parse
import requests
from .robots import process_robots, check_link_ok
from .search import search, search_without_highlighting
from .create_pattern import create_pattern
import re
import urllib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 5
MAX_OPTIONS = 10

def scrape(starting_links: List[str], search_text: str, browser_info: str) -> List[str]:
    """ Crawl each starting link and find websites that matches the query 
    string and links that require private access."""

    robots_item = '/robots.txt'
    to_visit = []
    broken_links = []
    queried_webpages = [] # Pages where search term was found
    output = {}  # Crawled pages organized by the starting URL
    requires_access = []  # Pages requiring access (401 or 403 status)
    pattern = create_pattern(search_text)
    search_str_webpages = [] # URLs with matched fragments (for highlighting browsers)

    # Determine if the browser supports text fragments (i.e., highlighting)
    use_highlighting = 'chrome' in browser_info.lower()

    # Iterate over each starting link
    for start_link in starting_links:
        try:
            page = requests.get(start_link)

            # Handle access-required pages or broken links
            if page.status_code == 401 or page.status_code == 403:
                print("requires access: ", start_link)
                requires_access.append(start_link)
                continue
            elif not (200 <= page.status_code <= 299):
                broken_links.append(start_link)
                print("new broken: ", start_link, ' code: ', page.status_code)
                continue
        except requests.exceptions.RequestException as request_exception:
            broken_links.append(start_link)
            continue
        pages_visited = 0
        visited = {}
        base = re.search('https?://[^/]+', start_link).group()

        # Fetch and process the robots.txt rules for the domain
        robots_url = base + robots_item
        robot_page = requests.get(robots_url)
        robot_rules = process_robots(robot_page.text)

        soup = BeautifulSoup(page.text, 'html.parser')
        
        # Search for the pattern in the page (with or without text fragments)
        fragments = []
        if use_highlighting:
            fragments = search(pattern, start_link)
        elif(not search_without_highlighting(soup, pattern)):
            fragments = None
        
        # If search results found, store them
        if fragments is not None and start_link not in queried_webpages:
            queried_webpages.append(start_link)

            # For highlighting browsers, append URL with fragment
            if use_highlighting:
                parsed_url = urllib.parse.urlparse(start_link)
                for fragment in fragments:
                    updated_url = parsed_url._replace(fragment=fragment)
                    final_url = urllib.parse.urlunparse(updated_url)
                    search_str_webpages.append(final_url)
            # For non-highlighting browsers, append only the URL (without duplicating)
            else:
                search_str_webpages.append(start_link)
        
        # Extract all links from the current page and add them to the to-visit list
        links = soup.findAll('a')
        pages_visited += 1

        # get new links
        for new_link in links:
            if "href" not in new_link.attrs:
                continue
            href = new_link['href']
            potential_link = urljoin(base, href)
            # only crawl standard web URLs
            if not (potential_link.startswith('http://') or potential_link.startswith('https://')):
                continue
            # check if link has the same subdomain
            if urlparse(base).netloc != urlparse(potential_link).netloc:
                continue
            # check if crawling abides by standard
            if not check_link_ok(robot_rules, href):
                continue
            to_visit.append(potential_link)
        visited[start_link] = True 
        
        # Continue crawling new links
        while to_visit:
            if pages_visited >= SAFE_PAGE_LIMIT:
                break
            link = to_visit.pop(0)

            try:
                # Fetch the webpage
                page = requests.get(link)

                # catch links that require access
                if page.status_code == 401 or page.status_code == 403:
                    print("requires acces: ", link)
                    requires_access.append(link)
                    continue
                # catch broken links
                elif not (200 <= page.status_code <= 299):
                    broken_links.append(link)
                    print("new broken: ", link)
                    continue
                
                # scraping code 
                soup = BeautifulSoup(page.text, 'html.parser')

                fragments = []
                if use_highlighting:
                    fragments = search(pattern, link)
                elif(not search_without_highlighting(soup, pattern)):
                    fragments = None

                if fragments is not None and link not in queried_webpages:
                    queried_webpages.append(link)

                    # For highlighting browsers, append URL with fragment
                    if use_highlighting:
                        parsed_url = urllib.parse.urlparse(link)
                        for fragment in fragments:
                            updated_url = parsed_url._replace(fragment=fragment)
                            final_url = urllib.parse.urlunparse(updated_url)
                            search_str_webpages.append(final_url)
                    # For non-highlighting browsers, append only the URL (without duplicating)
                    else:
                        search_str_webpages.append(link)

                if link in visited:
                    print(f"Link already visited: {link}")
                    continue

                # mark the item as visited, i.e., add to visited list, remove from to_visit
                visited[link] = True
                
                links = soup.findAll('a')
                print(f"Visiting: {link}, Pages visited: {pages_visited}")
                
                # get new links
                for new_link in links:
                    if "href" not in new_link.attrs:
                        continue
                    href = new_link['href']
                    potential_link = urljoin(base, href)
                    # only crawl standard web URLs
                    if not (potential_link.startswith('http://') or potential_link.startswith('https://')):
                        continue
                    # check if link has the same subdomain
                    if urlparse(base).netloc != urlparse(potential_link).netloc:
                        continue
                    # check if crawling abides by standard
                    if not check_link_ok(robot_rules, href):
                        continue
                    # if link has not been visited and is not to be visited 
                    if (potential_link not in visited) and (potential_link not in to_visit):
                        to_visit.append(potential_link)
                pages_visited += 1
            except requests.exceptions.RequestException as request_exception:
                broken_links.append(link)

        output[start_link] = sorted(visited.keys())

    return [search_str_webpages, requires_access, output]