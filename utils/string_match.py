import json
from typing import List

import requests
from .robots import process_robots, check_link_ok

from collections import defaultdict as dd
import re
from urllib.parse import urljoin
from urllib.parse import quote
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 1
MAX_OPTIONS = 10


def scrape(starting_links: List[str], json_filename: str, search_text) -> List[str]:
    """ Crawl each starting link and find websites that matches the query 
    string and links that require private access. All links crawled stored 
    in JSON file"""

    robots_item = '/robots.txt'
    to_visit = []
    broken_links = []
    queried_webpages = []
    output = {}
    requires_access = []
    pattern = create_pattern(search_text)

    # search for base urls
    for start_link in starting_links:
        try:
            page = requests.get(start_link)
            # catch links that require access
            if page.status_code == 401 or page.status_code == 403:
                print("requires acces: ", start_link)
                requires_access.append(start_link)
                continue
            # catch broken links
            elif not (200 <= page.status_code <= 299):
                broken_links.append(start_link)
                print("new broken: ", start_link)
                continue
        except requests.exceptions.RequestException as request_exception:
            broken_links.append(start_link)
            continue
        pages_visited = 0
        visited = {}
        base = re.search('https?://[^/]+', start_link).group()
        robots_url = base + robots_item
        robot_page = requests.get(robots_url)
        robot_rules = process_robots(robot_page.text)

        soup = BeautifulSoup(page.text, 'html.parser')
        
        # see if queried text is on webpage
        if search(soup, pattern):
            queried_webpages.append(start_link)
        
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
        
        # crawling
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

                # see if queried text is on webpage
                if search(soup, pattern):
                    queried_webpages.append(link)

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
    
    # create json output file
    with open(json_filename, "w") as outfile:
        json.dump(output, outfile)

    print(pattern)
    print(queried_webpages)

    return [queried_webpages, requires_access]


def validate_brackets(search_term):
    balance = 0
    in_brackets = False
    # keep track of the last open bracket index
    last_open_index = -1  
    for i, char in enumerate(search_term):
        if char == '[':
            # found a '[' before closing the previous '['
            if in_brackets: 
                raise ValueError("Unbalanced or nested brackets found.")
            in_brackets = True
            balance += 1
            # update the position of the last open bracket
            last_open_index = i  
        elif char == ']':
            if not in_brackets:
                raise ValueError("Closing bracket ']' found before any opening bracket '['.")
            # check if the content between the last '[' and this ']' is completely empty
            if i == last_open_index + 1:
                raise ValueError("Empty brackets found.")
            in_brackets = False
            balance -= 1

    if balance != 0:
        raise ValueError("Unbalanced brackets detected.")
    return True

def create_pattern(search_term):
    if not validate_brackets(search_term):
        raise ValueError(f"Invalid bracket syntax.")

    search_term = search_term.replace(r'\%', '<PERCENT>')
    search_term = search_term.replace(r'\?', '<QUESTION_MARK>')
    search_term = search_term.replace(r'\[', '<LITERAL_OPEN_BRACKET>')
    search_term = search_term.replace(r'\]', '<LITERAL_CLOSE_BRACKET>')
    search_term = search_term.replace(r'\|', '<LITERAL_PIPE>')
    
    # escape all other regex special characters
    search_term = re.sub(r'([.^$*+{}\\()])', r'\\\1', search_term)
    
    # replace unescaped % with regex equivalent (any sequence of characters)
    search_term = search_term.replace('%', '.*')
    
    # replace unescaped ? with regex equivalent (any single character)
    search_term = search_term.replace('?', '.')

    # handle alternation for multiple options with any characters
    search_term = re.sub(r'\[([^\]]+)\]', lambda m: f"({m.group(1)})", search_term)
    options = search_term.split('|')
    if len(options) > MAX_OPTIONS:
        raise ValueError(f"Too many options in alternation. Limit is {MAX_OPTIONS}.")
    
    # replace placeholders back to their literal characters
    search_term = search_term.replace('<PERCENT>', r'%')
    search_term = search_term.replace('<QUESTION_MARK>', r'\?')
    search_term = search_term.replace('<LITERAL_OPEN_BRACKET>', r'\[')
    search_term = search_term.replace('<LITERAL_CLOSE_BRACKET>', r'\]')
    search_term = search_term.replace('<LITERAL_PIPE>', r'\|')

    no_leading_boundary = search_term.startswith('.*')
    if not re.match(r'^[a-zA-Z0-9_?]', search_term[0]):
        no_leading_boundary = True
    no_trailing_boundary = search_term.endswith('.*')
    if not re.match(r'^[a-zA-Z0-9_?]', search_term[-1]):
        no_trailing_boundary = True

    print("NO LEADING \\b: ", no_leading_boundary)
    print("NO TRAILING \\b: ", no_trailing_boundary)

    # no word boundaries if both ends have wildcards
    if no_leading_boundary and no_trailing_boundary:
        pattern = search_term
    # no leading word boundary
    elif no_leading_boundary:
        pattern = search_term + r'\b'
    # no trailing word boundary
    elif no_trailing_boundary:
        pattern = r'\b' + search_term
    # use word boundaries on both sides
    else:
        pattern = r'\b' + search_term + r'\b'

    return pattern


def search(soup, pattern):
    results = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
    if results: 
        return True
    return False
