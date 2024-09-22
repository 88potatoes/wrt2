from collections import defaultdict as dd
import re

MAX_OPTIONS = 10

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