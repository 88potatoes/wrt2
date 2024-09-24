import urllib.parse
import re
import urllib
from bs4 import BeautifulSoup
from selenium import webdriver

# character limit for URL fragments
CHAR_LIMIT = 50

# JavaScript code to remove mobile-specific elements from the web page
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


# FOR DEBUGGING, DELETE BEFORE PRODUCTION!
def show_hidden_chars(text):
    # Replace hidden characters with visible symbols for easier debugging
    visible_text = (
        text.replace("\n", "\\n")
        .replace("\t", "\\t")
        .replace("\r", "\\r")
        .replace(" ", "[space]")  # Optional: make spaces visible too
    )
    return visible_text


# check if the character is allowed in the text fragment
def check_char(char):
    if not char.isprintable():
        return False
    # allowed characters: alphanumeric, safe, reserved, and typically unsafe characters
    allowed_chars = re.compile(r"^[a-zA-Z0-9$-_.+!*\'\"(),;/?:@=&<>#%{}|\\^~\[\]` ]*$")
    return bool(allowed_chars.match(char))


# find suffix for matching string
def find_suffix(text, index, len_text):
    prev_end = index
    while index < len_text and re.match(r"\s+", text[index]):
        index += 1
    num_chars = 0
    while index < len_text and check_char(text[index]) and num_chars < CHAR_LIMIT:
        if text[index] == " ":
            prev_end = index
        num_chars += 1
        index += 1
    if index < len_text and not text[index].isprintable():
        prev_end = index
    return prev_end


# find prefix for matching string
def find_prefix(text, index):
    if index == 0:
        return index
    prev_start = index
    index -= 1
    # print(text[index])
    while index >= 0 and re.match(r"\s+", text[index]):
        index -= 1
    num_chars = 0
    while index >= 0 and check_char(text[index]) and num_chars < CHAR_LIMIT:
        if text[index] == " ":
            prev_start = index
        # print(text[index])
        num_chars += 1
        index -= 1
    if index >= 0 and not text[index].isprintable():
        prev_start = index
    return prev_start


# Search text without text highlighting
# for browsers other than chrome
def search_without_highlighting(soup, pattern):
    # extract all text without HTML tags
    text = soup.get_text(separator=" ")
    results = re.search(pattern, text, re.IGNORECASE)
    if results:
        return True
    return False


# apply url encoding to the string
def url_encode(string):
    string = string.strip()
    string = urllib.parse.quote(string, safe="")
    string = re.sub(r"-", "%2D", string)
    string = re.sub(r"\.", "%2E", string)
    string = re.sub(r"_", "	%5F", string)
    string = re.sub(r"~", "%7E", string)
    return string


# search function with text highlighting
def search(pattern, url):
    # open the webpage to get both Javascript and HTML content
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    driver.get(url)
    driver.execute_script(remove_mobile_elements_js)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")

    # print(soup.prettify())
    # remove elements that are not on the page
    for element in soup(["title"]):
        element.decompose()

    # separate each html element by the newline char
    text = soup.get_text(separator="\n")
    # change to lowercase to make it case insensitive
    text = text.lower()
    # print(show_hidden_chars(text))

    regex = re.compile(pattern, re.IGNORECASE)
    match = re.search(regex, text)
    if not match:
        return []

    index = 0
    fragments = []
    len_text = len(text)
    fragment_start = ":~:text="
    # print('found a match')

    # loop through the entire HTML to find all matching strings
    while match is not None:
        # add index of previous match to make current index relative to the entire HTML
        match_start = match.start() + index
        match_end = match.end() + index
        term = match.group(0)
        # print('match string: ', show_hidden_chars(match.group(0)))

        # use 'start' and 'end' syntax if the term spans multiple consecutive elements
        if "\n" in term:
            elements = term.split("\n")
            frag_start = elements[0]
            frag_end = elements[-1]
            if frag_start and frag_end:
                frag_start = url_encode(frag_start)
                frag_end = url_encode(frag_end)
                fragment = fragment_start + frag_start + "," + frag_end
                fragments.append(fragment)
                # adjust index to ending index of the current match
                index = match_end
                match = re.search(pattern, text[match_end:], re.IGNORECASE)
                continue

        # find index of first character in prefix
        start = find_prefix(text, match_start)
        # find index of last character in suffix
        end = find_suffix(text, match_end, len_text)

        # check if a suffix has been found
        if end != match_end:
            # check if the suffix is in the next element of the matching string
            if text[match_end] == "\n":
                suffix = text[match_end + 1 : end]
            else:
                suffix = text[match_end:end]
            suffix = url_encode(suffix)
        else:
            suffix = ""

        # check if a prefix has been found
        if start != match_start:
            # check if the prefix is in the previous element of the matching string
            if text[match_start - 1] == "\n":
                prefix = text[start : match_start - 1]
            else:
                prefix = text[start:match_start]
            prefix = url_encode(prefix)
        else:
            prefix = ""

        # encode the matching string
        term = urllib.parse.quote(term)
        term = re.sub(r"-", "%2D", term)
        term = re.sub(r"\s+", " ", term)
        term = term.strip()

        # build the fragment
        if prefix and suffix:
            fragment = fragment_start + prefix + "-," + term + ",-" + suffix
        elif suffix:
            fragment = fragment_start + term + ",-" + suffix
        elif prefix:
            fragment = fragment_start + prefix + "-," + term
        else:
            fragment = fragment_start + term

        print("fragment: ", fragment)
        fragments.append(fragment)
        # adjust index to ending index of the current match
        index = match_end
        match = re.search(pattern, text[match_end:], re.IGNORECASE)

    # print(len(fragments))
    driver.quit()
    return fragments
