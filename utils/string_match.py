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
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# A limit on the number of links crawled for each starting link
SAFE_PAGE_LIMIT = 1
MAX_OPTIONS = 10
CHAR_LIMIT = 50

remove_mobile_elements_js = """
    var mobileSelectors = [
        '.mobile-nav',          // Mobile navigation bar
        '.mobile-header',       // Mobile header
        '.mobile-footer',       // Mobile footer
        '.menu-toggle',         // Menu toggle button (hamburger)
        '.hamburger-menu',      // Hamburger menu
        '.responsive-nav',      // Responsive navigation bar
        '.responsive-menu',     // Responsive menu
        '.mobile-menu',         // Mobile-specific menu
        '.hidden-xs',           // Bootstrap class to hide on mobile
        '.visible-xs',          // Bootstrap class to show on mobile
        '.visible-sm',          // Bootstrap class to show on small screens
        '.hidden-sm',           // Bootstrap class to hide on small screens
        '.mobile-specific',     // Any element with a 'mobile-specific' class
        '[data-mobile]',        // Elements with data-mobile attributes
        '[aria-hidden="true"]', // Often used to hide elements in mobile mode
        '.mobile-banner',       // Mobile banners or ad-specific elements
        '.mobile-popup',        // Mobile popups
        '.mobile-ad',           // Mobile ads
        '.offcanvas',           // Off-canvas menus (often used for mobile navigation)
        '.drawer',              // Drawer menu elements (common in mobile navigation)
        '.swipe',               // Swipeable elements (mobile interaction)
        '.touch',               // Elements with touch interactions (mobile)
        '[onclick*="mobile"]'   // Elements that have onClick behavior for mobile
    ];

    mobileSelectors.forEach(function(selector) {
        var elements = document.querySelectorAll(selector);
        elements.forEach(function(element) {
            element.remove();  // Remove the mobile-specific element
        });
    });
"""



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

        fragments = search(soup, pattern, start_link)
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

                fragments = search(soup, pattern, link)
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
    unique_webpages = set()
    count = 1
    for webpage in search_str_webpages:
        if webpage in unique_webpages:
            continue
        unique_webpages.add(webpage)
        print(count, ' ', webpage)
        count += 1
    print('done')

    return [search_str_webpages, requires_access]


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


def replace_empty_options(match):
    # This function will be used to replace empty options within parentheses
    content = match.group(0)
    # Replace empty options only inside the captured content
    replaced_content = re.sub(r'(?<=\|)(?=\|)|(?<=\()(?=\|)|(?<=\|)(?=\))', r'\\b', content)
    return replaced_content


def replace(search_term):
    # Replace within content enclosed by parentheses
    search_term = re.sub(r'\(.*?\)', replace_empty_options, search_term)
    return search_term


def create_pattern(search_term):
    if search_term == '%':
        return ValueError(f"Invalid wildcard.")
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
    len_options = len(options)
    if len_options > MAX_OPTIONS:
        raise ValueError(f"Too many options in alternation. Limit is {MAX_OPTIONS}.")
    if len_options > 0:
        if search_term[0] == '(' or search_term[-1] == ')':
            search_term = replace(search_term)
    
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
    # print(text[index])
    while re.match(r'\s+', text[index]):
        index += 1
    num_chars = 0
    while index < len_text and check_char(text[index]) and num_chars < CHAR_LIMIT:
        if text[index] == ' ':
            prev_end = index
        # print(text[index])
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
    # print(text[index])
    while re.match(r'\s+', text[index]):
        index -= 1
    num_chars = 0
    while index >= 0 and check_char(text[index]) and num_chars < CHAR_LIMIT:
        if text[index] == ' ':
            prev_start = index
        # print(text[index])
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

def search_without_highlighting(soup, pattern):
    # extract all text without HTML tags
    text = soup.get_text(separator=" ")  
    results = re.search(pattern, text, re.IGNORECASE)
    if results: 
        return True
    return False


def url_encode(string):
    string = string.strip()
    string = urllib.parse.quote(string, safe="")
    string = re.sub(r'-', '%2D', string)
    string = re.sub(r'\.', '%2E', string)
    string = re.sub(r'_', '	%5F', string)
    string = re.sub(r'~', '%7E', string)
    return string

def search(soup, pattern, url):
    print(soup.get_text(separator="\n"))
    # extract all text without HTML tags
    # user_agent = parse(user_agent_str)
    # browser = user_agent.browser.family 
    # if browser == 'Chrome':
    #     print('is chrome')
    # options = webdriver.ChromeOptions()
    # options.add_argument("--headless=new")
    # # options.add_argument(f'user-agent={user_agent_str}')
    # options.add_argument("window-size=2560,1600")
    # driver = webdriver.Chrome(options=options)
    # else:
    #     return search_without_highlighting(soup, pattern)

    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)

    driver.execute_script(remove_mobile_elements_js)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    # print(soup.prettify())
    for element in soup(["title"]): 
        element.decompose()
    text = soup.get_text(separator="\n") 
    text = text.lower() 
    print(show_hidden_chars(text))
    regex = re.compile(pattern, re.IGNORECASE)
    match = re.search(regex, text)
    if not match:
        return False
    
    index = 0
    fragments = []
    len_text = len(text)
    fragment_start = ":~:text="
    print('found a match')
    while match is not None:
        match_start = match.start() + index
        match_end = match.end() + index
        term = match.group(0)
        print('match string: ', show_hidden_chars(match.group(0)))
        if '\n' in term:
            elements = term.split('\n')
            frag_start = elements[0]
            frag_end = elements[-1]
            if frag_start and frag_end:
                frag_start = url_encode(frag_start)
                frag_end = url_encode(frag_end)
                fragment = fragment_start + frag_start + ',' + frag_end
                fragments.append(fragment)
                index = match_end
                match = re.search(pattern, text[match_end:], re.IGNORECASE)
                continue
        
        start = find_prefix(text, match_start)
        print("Found prefix!")
        end = find_suffix(text, match_end, len_text)
        print("Found suffix!")

        if end != match_end:
            if text[match_end] == '\n':
                suffix = text[match_end + 1: end]
            else:
                suffix = text[match_end:end]
            suffix = url_encode(suffix)
        else:
            suffix = ""

        if start != match_start:
            if text[match_start - 1] == '\n':
                prefix = text[start: match_start - 1]
            else:
                prefix = text[start:match_start]
            prefix = url_encode(prefix)
        else:
            prefix = ""
        
        term = urllib.parse.quote(term)
        term = re.sub(r'-', '%2D', term)
        term = re.sub(r'\s+', ' ', term) 
        term = term.strip() 

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
    driver.quit()
    return fragments

        
