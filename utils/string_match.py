import json
from typing import List
import urllib.parse

import requests
from .robots import process_robots, check_link_ok

from collections import defaultdict as dd
import re
import urllib
from urllib.parse import urljoin
from urllib.parse import quote
from urllib.parse import urlparse
from bs4 import BeautifulSoup

# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 1
MAX_OPTIONS = 10


def scrape(starting_links: List[str], search_text) -> List[str]:
    """ Crawl each starting link and find websites that matches the query 
    string and links that require private access."""

    robots_item = '/robots.txt'
    to_visit = []
    broken_links = []
    queried_webpages = []
    output = {}
    requires_access = []
    pattern = create_pattern(search_text)
    search_str_webpages = []

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
        # if search(soup, pattern):
        #     queried_webpages.append(start_link)

        fragments = search(soup, pattern)
        if fragments and start_link not in queried_webpages:
            queried_webpages.append(start_link)
            parsed_url = urllib.parse.urlparse(start_link)
            for fragment in fragments:
                updated_url = parsed_url._replace(fragment=fragment)
                final_url = urllib.parse.urlunparse(updated_url)
                search_str_webpages.append(final_url)
        
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
                # if search(soup, pattern):
                #     queried_webpages.append(link)

                fragments = search(soup, pattern)
                if fragments and link not in queried_webpages:
                    queried_webpages.append(link)
                    parsed_url = urllib.parse.urlparse(link)
                    for fragment in fragments:
                        updated_url = parsed_url._replace(fragment=fragment)
                        final_url = urllib.parse.urlunparse(updated_url)
                        search_str_webpages.append(final_url)

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
    
    print(pattern)
    print(search_str_webpages)
    print('done')

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
    
    # replace unescaped ? with regex equivalent (any single character)
    search_term = search_term.replace('?', '.')

    # replace unescaped % with regex equivalent (any sequence of characters)
    search_term = search_term.replace('%', '\w+')

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
    search_term = search_term.replace(' ', r'(?:\s|\r\n|\r|\n)*')

    no_leading_boundary = search_term.startswith('.*')
    if not re.match(r'^[a-zA-Z0-9.]|\w+', search_term[0]):
        no_leading_boundary = True
    no_trailing_boundary = search_term.endswith('.*')
    if not re.match(r'^[a-zA-Z0-9.]|\w+', search_term[-1]):
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


def check_char(char):
    if not char.isprintable():
        return False
    # Define allowed characters: Alphanumeric, safe, reserved, and typically unsafe characters
    allowed_chars = re.compile(r'^[a-zA-Z0-9$-_.+!*\'\"(),;/?:@=&<>#%{}|\\^~\[\]` ]*$')
    return bool(allowed_chars.match(char))

def find_suffix(text, index, len_text):
    prev_end = index
    if text[index] == "\n":
        index += 1
    num_chars = 0
    char_limit = 100
    while index < len_text and check_char(text[index]) and num_chars < char_limit:
        if text[index] == ' ':
            prev_end = index
        num_chars += 1
        index += 1
    if index < len_text and not text[index].isprintable():
        prev_end = index
    return prev_end

def find_prefix(text, index):
    if index == 0:
        return index
    prev_start = index
    index -= 1
    if text[index] == '\n':
        index -= 1
    num_chars = 0
    char_limit = 100
    while index >= 0 and check_char(text[index]) and num_chars < char_limit:
        if text[index] == ' ':
            prev_start = index
        num_chars += 1
        index -= 1
    if index >=0 and not text[index].isprintable():
        prev_start = index
    return prev_start


def show_hidden_chars(text):
    # Replace hidden characters with visible symbols for easier debugging
    visible_text = (
        text.replace("\n", "\\n")
            .replace("\t", "\\t")
            .replace("\r", "\\r")
            .replace(" ", "[space]")  # Optional: make spaces visible too
    )
    return visible_text


def search(soup, pattern):
    # extract all text without HTML tags
    for element in soup(["style", "script", "title"]): # "meta" ,
        element.decompose()
    text = soup.get_text(separator="\n") 
    text = text.lower() 
    print(show_hidden_chars(text))
    regex = re.compile(pattern, re.IGNORECASE)
    match = re.search(regex, text)
    if not match:
        return False
    
    index = 0
    char_limit = 70
    fragments = []
    len_text = len(text)
    fragment_start = ":~:text="
    print('found a match')
    while match is not None:
        match_start = match.start() + index
        match_end = match.end() + index

        start = -1
        end = find_suffix(text, match_end, len_text)
        print("Found suffix!")
        if (end - match_end + 1) < char_limit:
            start = find_prefix(text, match_start)
            print("Found prefix!")
        
        if end != match_end:
            if text[match_end] == '\n':
                suffix = text[match_end + 1: end]
            else:
                suffix = text[match_end:end]
            suffix = suffix.strip()
            # print('suffix before ', suffix)
            suffix = urllib.parse.quote(suffix, safe="")
            suffix = re.sub(r'-', '%2D', suffix)
            suffix = re.sub(r'\.', '%2E', suffix)
            suffix = re.sub(r'_', '	%5F', suffix)
            suffix = re.sub(r'~', '%7E', suffix)
            print('suffix: ', suffix)
        else:
            suffix = ""

        if start != -1 and start != match_start:
            if text[match_start - 1] == '\n':
                prefix = text[start: match_start - 1]
            else:
                prefix = text[start:match_start]
            prefix = prefix.strip()
            prefix = urllib.parse.quote(prefix, safe="")
            prefix = re.sub(r'-', '%2D', prefix)
            prefix = re.sub(r'\.', '%2E', prefix)
            prefix = re.sub(r'_', '	%5F', prefix)
            prefix = re.sub(r'~', '%7E', prefix)
            print('prefix: ', prefix)
        else:
            prefix = ""
        
        term = match.group()
        term = urllib.parse.quote(term)
        term = re.sub(r'-', '%2D', term)
        term = re.sub(r'\s+', ' ', term) # Replace one or more whitespace characters with a single space
        term = term.strip()  # Remove leading/trailing spaces

        if prefix and suffix:
            fragment = fragment_start + prefix + '-,' + term + ",-" + suffix
        elif suffix:
            fragment = fragment_start + term + ",-" + suffix
        elif prefix:
            fragment = fragment_start + prefix + '-,' + term 
        else:
            fragment = fragment_start + term
        
        print("fragment: ", fragment)
        fragments.append(fragment)
        index = match_end
        match = re.search(pattern, text[match_end:], re.IGNORECASE)
 
    print(len(fragments))
    return fragments
