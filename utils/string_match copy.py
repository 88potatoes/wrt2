import json
from typing import List

import requests
from .robots import process_robots, check_link_ok

from collections import defaultdict as dd
import re
from urllib.parse import urljoin
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 5

def scrape(starting_links: List[str], search_text) -> List[str]:
    """ Crawl each starting link and find websites that matches the query 
    string and links that require private access. All links crawled stored 
    in JSON file"""

    robots_item = '/robots.txt'
    to_visit = []
    broken_links = []
    queried_webpages = []
    output = {}
    requires_access = []

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
        if search(soup, search_text) and start_link not in queried_webpages:
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
                if search(soup, search_text) and link not in queried_webpages:
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
    
    return [queried_webpages, requires_access, output]


def search(soup, search_text):
    soup = soup.get_text(separator = ' ')

    # change all characters to their casefolded form
    soup = soup.casefold()

    # replace non-alphabetic characters to single-space characters
    pattern = r'[^a-zA-Z\s\\]'
    soup = re.sub(pattern, ' ', soup)
    
    # convert all spacing characters such as tabs and newlines into single-space characters
    soup = re.sub(r'\s+', ' ',soup)

    # text is converted to explicit tokens 
    tokens = soup.split()

    res = False
    search_text = search_text.lower()
    search = search_text.split()
    search_text_len = len(search)

    for j in range(len(tokens) - search_text_len + 1):
        if tokens[j] == search[0]:
            for i in range(1, search_text_len):
                if tokens[j + i] != search[i]:
                    break
            else:
                res = True
                return res
    return res
