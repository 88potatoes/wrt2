import re
from typing import List, Pattern, Tuple


def process_robots(robots_txt: str, agent_name: str = "*", handled_fields: List[str] = ["disallow", "allow"]) -> List[Tuple[str, int, str]]:
    """
    Reads a robots.txt text and derives all rules for the agent, for simplicity this agent is assumed to
    be the default user agent *, the interaction between a named agent and the wildcard agent name is not 
    supported and records containing multiple agents are ignored.

    The return value is a list of rules.

    Each rule is a tuple which has a string (either Allow or Disallow), a length and a string which is 
    the partial text which the rule covers.
    """
    # Pre-flight sanity checks
    for field in handled_fields:
        # All handled directives are assumed to be lower-case.
        assert field == field.lower()
    # agent_name is assumed to be "*"
    assert agent_name == "*"
    robots_lines: List[str] = robots_txt.split("\n")
    # Parse from where agent starts to where a different agent begins or the lines end.
    in_agent: bool = False
    # Directive line from http://www.robotstxt.org/orig.html - no need to worry about exactly how this works until 
    #  Regular Expressions are covered, consider it as splitting up the text into the pattern {field}: {value} skipping
    #  any comments and allowing us to easily ignore lines which don't fit this pattern. {field} is .group(1) and {value}
    #  is .group(2).
    directive_line: Pattern[bytes] = re.compile(r"([A-Za-z\-]+):\s*([^\s#]+)")
    directives: List[Tuple[str, List[Pattern[bytes]]]] = []
    for line in robots_lines:
        # See if this is a directive line.
        contents = re.match(directive_line, line)
        if not contents:
            continue
        # Field - can only handle "user-agent" and those in handled_directives
        field = contents.group(1).lower()
        # Value - note this is case insensitive.
        value = contents.group(2).lower()

        if field == "user-agent":
            if in_agent:
                # New agent, done dealing with all directives for the current agent.
                break
            else:
                # If the agent is not the default user agent, continue to the next line.
                if not value == agent_name:
                    continue
                else:
                    in_agent = True
                    continue
        else:
            # Only process directives for our agent.
            if not in_agent:
                continue
        if field not in handled_fields:
            # Ignore fields we don't support.
            continue
        new_directive = (field, len(value), value)
        directives.append(new_directive)
    return directives


def check_link_ok(rules: List[Tuple[str, int, str]], link_to_check: str) -> bool:
    """
    Takes a list of rules and a link to check against them. Returns True if the link is visitable and 
        False if the link should not be visited by the crawling.

    Processing Rules:
    Rules should be processed in order. If the link is shorter than the pattern, the rule should be ignored.
    If the slice of the link matching the length in the rule matches the string associated with the rule,
    the directive associated with the rule is returned.
    """
    # Patterns are case insensitive.
    ltc = link_to_check.lower()
    for rule in rules:
        directive, length, string = rule
        if length > len(ltc):
            continue
        elif ltc[:length] == string:
            # Matches rule so we don't have to look through any more rules.
            if directive == "disallow":
                return False
            else:
                assert directive == "allow"
                return True
        else:
            # Move to next rule.
            continue
    # Default behaviour is that the link is OK to visit.
    return True
