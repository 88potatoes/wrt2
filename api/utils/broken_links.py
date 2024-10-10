from typing import List

import requests
from .robots import process_robots, check_link_ok
from .response import BrokenLinksResponse

import re
from urllib.parse import urljoin
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 5


def crawl(starting_links: List[str]) -> List[str]:
    """Crawl each url in the starting_link list, and output
    the broken links and links that require private access. All links
    crawled stored in JSON file"""

    robots_item = "/robots.txt"
    to_visit = []
    response = BrokenLinksResponse()

    # search for base urls
    for start_link in starting_links:
        try:
            page = requests.get(start_link)
            # catch links that require access
            if page.status_code == 401 or page.status_code == 403:
                print("requires acces: ", start_link)
                response.requires_access.append(start_link)
                continue
            # catch broken links
            elif not (200 <= page.status_code <= 299):
                response.broken_links.append(start_link)
                print("new broken: ", start_link)
                continue
        except requests.exceptions.RequestException:
            response.broken_links.append(start_link)
            continue

        pages_visited = 0
        visited = {}
        base = re.search("https?://[^/]+", start_link).group()
        robots_url = base + robots_item
        robot_page = requests.get(robots_url)
        robot_rules = process_robots(robot_page.text)

        soup = BeautifulSoup(page.text, "html.parser")

        links = soup.findAll("a")
        pages_visited += 1

        # get new links
        for new_link in links:
            if "href" not in new_link.attrs:
                continue
            href = new_link["href"]
            potential_link = urljoin(base, href)
            # only crawl standard web URLs
            if not (
                potential_link.startswith("http://")
                or potential_link.startswith("https://")
            ):
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
            if pages_visited == SAFE_PAGE_LIMIT:
                break
            link = to_visit.pop(0)

            try:
                # Fetch the webpage
                page = requests.get(link)

                # catch links that require access
                if page.status_code == 401 or page.status_code == 403:
                    print("requires acces: ", link)
                    response.requires_access.append(link)
                    continue
                # catch broken links
                elif not (200 <= page.status_code <= 299):
                    response.broken_links.append(link)
                    print("new broken: ", link)
                    continue

                # scraping code
                soup = BeautifulSoup(page.text, "html.parser")

                if link in visited:
                    print(f"Link already visited: {link}")
                    continue

                # mark the item as visited, i.e., add to visited list, remove from to_visit
                visited[link] = True

                links = soup.findAll("a")

                # get new links
                for new_link in links:
                    if "href" not in new_link.attrs:
                        continue
                    href = new_link["href"]
                    potential_link = urljoin(base, href)
                    # only crawl standard web URLs
                    if not (
                        potential_link.startswith("http://")
                        or potential_link.startswith("https://")
                    ):
                        continue
                    # check if link has the same subdomain
                    if urlparse(base).netloc != urlparse(potential_link).netloc:
                        continue
                    # check if crawling abides by standard
                    if not check_link_ok(robot_rules, href):
                        continue
                    # if link has not been visited and is not to be visited
                    if (potential_link not in visited) and (
                        potential_link not in to_visit
                    ):
                        to_visit.append(potential_link)
                pages_visited += 1
            except requests.exceptions.RequestException:
                response.broken_links.append(link)

        response.output[start_link] = sorted(visited.keys())

    return response

