from collections import defaultdict as dd
import re

# max number of options in alternation brackets
MAX_OPTIONS = 10

# validate if brackets in the search term are balanced
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


# replace empty options within alternation brackets with word boundaries
def replace_empty_options(match):
    content = match.group(0)
    # Replace empty options only inside the captured content
    replaced_content = re.sub(r'(?<=\|)(?=\|)|(?<=\()(?=\|)|(?<=\|)(?=\))', r'\\b', content)
    return replaced_content


# if the alternation brackets are at the start or end of the search term,
# replace empty options with word boundaries 
def replace(search_term):
    search_term = re.sub(r'\(.*?\)', replace_empty_options, search_term)
    return search_term

# Create the regex pattern based on the search term
def create_pattern(search_term):
    """
    Wildcards are defined as below:
    1. ?: Represents a wildcard for a single character. For example, 'student' matches 'st?de?t'.
    2. %: Acts as a wildcard for 0 or more characters until it reaches the end of the word. 
        For example, 'student' matches '%tu%en%'.
    3. Alternation Brackets [a|b|c]: Represents a wildcard to match multiple options. 
        % and ? can be used within these brackets. 
        For example, ‘ab’,’ cd’,’ de’ all match [ab|c?|d%]. Number of options is currently limited to 10.
        Please note that only links with the same subdomain as the input links will be crawled. 
    """

    # '%' alone will return a extremely large number matches as it matches every word 
    if search_term == '%':
        return ValueError(f"Invalid wildcard.")
    if not validate_brackets(search_term):
        raise ValueError(f"Invalid bracket syntax.")

    # Replace escape characters that overlap with the wildcard syntax with placeholders
    search_term = search_term.replace(r'\%', '<PERCENT>')
    search_term = search_term.replace(r'\?', '<QUESTION_MARK>')
    search_term = search_term.replace(r'\[', '<LITERAL_OPEN_BRACKET>')
    search_term = search_term.replace(r'\]', '<LITERAL_CLOSE_BRACKET>')
    search_term = search_term.replace(r'\|', '<LITERAL_PIPE>')

    # determine if a word boundary should be placed in front or at the end of the search term
    no_leading_boundary = search_term.startswith('%')
    if not no_leading_boundary:
        no_leading_boundary = search_term.startswith('(')
    no_trailing_boundary = search_term.endswith('%')
    if not no_trailing_boundary:
        no_trailing_boundary = search_term.endswith(')')
    
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

    # if search term does not start / end with a word character, do not put a word boundary at the front / end
    if not re.match(r'^[a-zA-Z0-9?]', search_term[0]):
        no_leading_boundary = True
    if not re.match(r'^[a-zA-Z0-9?]', search_term[-1]):
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
