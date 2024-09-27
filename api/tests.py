from django.test import TestCase
from unittest.mock import Mock, patch
from utils.broken_links import crawl
from utils.string_match import scrape
from utils.robots import process_robots, check_link_ok
from utils.create_pattern import create_pattern, validate_brackets, replace
from utils.search import check_char, find_prefix, find_suffix, url_encode, search, search_without_highlighting
from bs4 import BeautifulSoup
import json
import requests
import re


class UnitTests(TestCase):
    @patch("requests.get")
    def test_link_extraction(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = """
        <html>
        <body>
            <a href="http://example.com/page1">Link 1</a>
            <a href="/page2">Link 2</a>
            <a href="https://othersite.com/page3">Link 3</a>
        </body>
        </html>
        """
        result = scrape(["http://example.com"], "search text", "brave")
        self.assertEqual(result[0], [])
        self.assertIn("http://example.com", result[-1])
        self.assertEqual(
            result[-1]["http://example.com"],
            [
                "http://example.com",
                "http://example.com/page1",
                "http://example.com/page2",
            ],
        )
        self.assertNotIn("https://othersite.com/page3", result[-1]["http://example.com"])

        result = crawl(["http://example.com"])
        self.assertEqual(result[0], [])
        self.assertIn("http://example.com", result[-1])
        self.assertEqual(
            result[-1]["http://example.com"],
            [
                "http://example.com",
                "http://example.com/page1",
                "http://example.com/page2",
            ],
        )
        self.assertNotIn("https://othersite.com/page3", result[-1]["http://example.com"])

    @patch("requests.get")
    def test_malformed_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        result = scrape(["invalid-url"], "search text", "brave")
        self.assertEqual(result[0], [])
        result = crawl(["invalid-url"])
        self.assertEqual(result[0], ["invalid-url"])

    def test_multiple_start_links(self):
        result = scrape(
            ["https://research.unimelb.edu.au", "https://www.unimelb.edu.au"],
            "search text",
            "brave"
        )
        self.assertIn("https://research.unimelb.edu.au", result[-1])
        self.assertIn("https://www.unimelb.edu.au", result[-1])
        self.assertEqual(result[0], [])

        result = crawl(
            ["https://research.unimelb.edu.au", "https://www.unimelb.edu.au"],
        )
        self.assertIn("https://research.unimelb.edu.au", result[-1])
        self.assertIn("https://www.unimelb.edu.au", result[-1])
        self.assertEqual(result[0], [])

    def test_no_start_links(self):
        result = scrape([], "search text", "brave")
        self.assertEqual(result[-1], {})
        self.assertEqual(result, [[], [], [], {}])

        result = crawl([])
        self.assertEqual(result[-1], {})
        self.assertEqual(result, [[], [], {}])

    def test_robots_txt(self):
        robot_rules = process_robots("User-agent: *\nDisallow: /private/\n")
        self.assertFalse(check_link_ok(robot_rules, "/private/"))
        self.assertTrue(check_link_ok(robot_rules, "/public/"))

    def test_search_without_highlighting(self):
        soup = BeautifulSoup(
            "<html><body>This is a test string</body></html>", "html.parser"
        )
        self.assertTrue(search_without_highlighting(soup, "This"))
        self.assertTrue(search_without_highlighting(soup, "test string"))
        self.assertFalse(search_without_highlighting(soup, "no string"))
        self.assertFalse(search_without_highlighting(BeautifulSoup("<html></html>", "html.parser"), "test"))

    @patch("requests.get")
    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout
        result = crawl(["https://example.com"])
        self.assertEqual(result[0], ["https://example.com"])
        result = scrape(["https://example.com"], "yeet", "brave")
        self.assertEqual(result[0], [])

    @patch("requests.get")
    def test_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError
        result = crawl(["https://example.com"])
        self.assertEqual(result[0], ["https://example.com"])
        result = scrape(["https://example.com"], "yeet", "brave")
        self.assertEqual(result[0], [])

    @patch("requests.get")
    def test_private_access_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff">Private Acess Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/staff":
                return Mock(status_code=401)
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result[:-1], [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )

        result = scrape(["https://handbook.unimelb.edu.au/"], "hey", "brave")
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result[:-1], [[], [], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )

    @patch("requests.get")
    def test_private_access_input(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=403,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/robots.txt":
                return Mock(
                    status_code=200, text="User-agent: *\nDisallow: /private/\n"
                )

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertEqual(result[1], ["https://handbook.unimelb.edu.au/"])
        result = scrape(["https://handbook.unimelb.edu.au/"], "hey", "brave")
        self.assertEqual(result[2], ["https://handbook.unimelb.edu.au/"])

    @patch("requests.get")
    def test_get_broken_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/arts-link":
                return Mock(status_code=410)
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result[:-1], [["https://handbook.unimelb.edu.au/2024/courses/arts-link"], []]
        )

        mock_get.side_effect = side_effect
        result = scrape(["https://handbook.unimelb.edu.au/"], "hey", "brave")
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(result[:-1], [[], ['https://handbook.unimelb.edu.au/2024/courses/arts-link'], []])

    # broken link as input
    @patch("requests.get")
    def test_broken_link_input(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au":
                return Mock(
                    status_code=400,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses">Courses Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au"])
        self.assertEqual(result[-1], {})
        self.assertNotIn("https://handbook.unimelb.edu.au", result[-1])
        self.assertEqual(result, [["https://handbook.unimelb.edu.au"], [], {}])

        result = scrape(["https://handbook.unimelb.edu.au"], "Arts", "brave")
        self.assertEqual(result[-1], {})
        self.assertNotIn("https://handbook.unimelb.edu.au", result[-1])
        self.assertEqual(result, [[], ["https://handbook.unimelb.edu.au"], [], {}])

    # test that links that have already been crawled are not crawled again
    @patch("requests.get")
    def test_crawled_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses">Courses Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )

        result = scrape(["https://handbook.unimelb.edu.au/"], "hey", "brave")
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )

    # assume safe page limit = 5!!!
    @patch("requests.get")
    def test_safe_page_limit(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses">Courses Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/history">History Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/philosophy">Philosophy Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/politics">Politics Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/international_relations">International Relations Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/history",
                "https://handbook.unimelb.edu.au/2024/courses/philosophy",
            ],
        )

        result = scrape(["https://handbook.unimelb.edu.au/"], "hey", "brave")
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/history",
                "https://handbook.unimelb.edu.au/2024/courses/philosophy",
            ],
        )

    def test_validate_brackets_balanced(self):
        # Valid cases
        self.assertTrue(validate_brackets("[abc]"))
        self.assertTrue(validate_brackets("term [abc] end"))
        self.assertTrue(validate_brackets("term end"))

    def test_validate_brackets_unbalanced(self):
        # Unbalanced cases
        with self.assertRaises(ValueError):
            validate_brackets("[abc")
        with self.assertRaises(ValueError):
            validate_brackets("abc]")
        with self.assertRaises(ValueError):
            validate_brackets("term [abc][def")
        with self.assertRaises(ValueError):
            validate_brackets("[]")

    def test_validate_brackets_nested(self):
        with self.assertRaises(ValueError):
            validate_brackets("[[abc]]")
    
    def test_replace_no_empty_options(self):
        self.assertEqual(replace(r'(||)'), r"(\b|\b|\b)")
        self.assertEqual(replace(r'(a|b|c)'), r"(a|b|c)")
        self.assertEqual(replace(r'(a)'), r"(a)")
    
    def test_create_pattern_for_word_search(self):
        self.assertEqual(create_pattern("beep"), r"\bbeep\b")
        self.assertEqual(create_pattern("hello world"), r"\bhello(?:\s|\r\n|\r|\n)*world\b")
    
    def test_create_pattern_for_percentage(self):
        self.assertEqual(create_pattern("%llo wor%"), r"\w*llo(?:\s|\r\n|\r|\n)*wor\w*")
        self.assertEqual(create_pattern("h%llo wor%d"), r"\bh\w*llo(?:\s|\r\n|\r|\n)*wor\w*d\b")
    
    def test_create_pattern_for_question_mark(self):
        self.assertEqual(create_pattern("?ello worl?"), r"\b.ello(?:\s|\r\n|\r|\n)*worl.\b")
        self.assertEqual(create_pattern("h?llo wor?d"), r"\bh.llo(?:\s|\r\n|\r|\n)*wor.d\b")
    
    def test_create_pattern_for_alternation_brackets(self):
        self.assertEqual(create_pattern("[H|b]ello worl[d|!]"), r"(H|b)ello(?:\s|\r\n|\r|\n)*worl(d|!)")
        self.assertEqual(create_pattern("Hello [w|m|r]orld"), r"\bHello(?:\s|\r\n|\r|\n)*(w|m|r)orld\b")
        with self.assertRaises(ValueError):
            create_pattern("[||||]")
    
    def test_create_pattern_for_actual_percentage_sign(self):
        self.assertEqual(create_pattern("\%"), r"%")
    
    def test_create_pattern_for_actual_question_mark(self):
        self.assertEqual(create_pattern("\?"), r"\?")
    
    def test_create_pattern_for_actual_square_brackets(self):
        self.assertEqual(create_pattern("\[\]"), r"\[\]")

    def test_create_pattern_for_percentage_in_brackets(self):
        self.assertEqual(create_pattern("h[%|e]yyy"), r"\bh(\w*|e)yyy\b")
        self.assertEqual(create_pattern("[%|y]ee[%|t]"), r"(\w*|y)ee(\w*|t)")
    
    def test_create_pattern_for_question_mark_in_brackets(self):
        self.assertEqual(create_pattern("h[?|eyyy]yyy"), r"\bh(.|eyyy)yyy\b")
        self.assertEqual(create_pattern("[?|y]ee[?|t!]"), r"(.|y)ee(.|t!)")
    
    def test_create_pattern_for_percentage_and_question_mark_in_brackets(self):
        self.assertEqual(create_pattern("h[?|%]yyy"), r"\bh(.|\w*)yyy\b")
        self.assertEqual(create_pattern("[?|%]ee[?|%|t!]"), r"(.|\w*)ee(.|\w*|t!)")
    
    def test_number_of_options(self):
        with self.assertRaises(ValueError):
            create_pattern("[|||||||||]")
        with self.assertRaises(ValueError):
            create_pattern("[?|%|][|s||a][||b|c|]")
            
    def test_url_encode(self):
        self.assertEqual(url_encode("(beep+boop)"), "%28beep%2Bboop%29")
        self.assertEqual(url_encode("-~._"), "%2D%7E%2E%5F")
    
    def test_find_prefix(self):
        text = "hey i am awesome\nyay!\n"
        self.assertEqual(find_prefix(text, 22), 16)
        text = "hey i am awesome\nyay!"
        self.assertEqual(find_prefix(text, 21), 16)
        text = "\n"
        self.assertEqual(find_prefix(text, 1), 1)
        # test char limit
        text = "Lorem ipsum dolor sit amet, consectetuer adipiscing elit.\n"
        self.assertEqual(find_prefix(text, len(text)-1), 11)

    def test_find_suffix(self):
        text = "\nhey i am awesome\nyay!"
        self.assertEqual(find_suffix(text, 0, len(text)), 17)
        text = "hey i am awesome\nyay!"
        self.assertEqual(find_suffix(text, 0, len(text)), 16)
        text = "\n"
        self.assertEqual(find_suffix(text, 0, len(text)), 0)
        # test char limit
        text = "\nLorem ipsum dolor sit amet, consectetuer adipiscing elit."
        self.assertEqual(find_suffix(text, 0, len(text)), 41)

    def test_check_char_alphanumeric(self):
        self.assertTrue(check_char("A"))
        self.assertTrue(check_char("z"))
        self.assertTrue(check_char("5"))
    
    def test_check_char_special_char(self):
        self.assertTrue(check_char("-"))
        self.assertTrue(check_char("_"))
        self.assertTrue(check_char("@"))
        self.assertTrue(check_char("!"))
    
    def test_check_char_disallowed(self):
        self.assertFalse(check_char("\t")) 
        self.assertFalse(check_char("\n"))  
        self.assertFalse(check_char("\r"))  

    def test_check_char_non_printable(self):
        self.assertFalse(check_char("\x00"))  # Null byte

    def test_check_char_space_character(self):
        self.assertTrue(check_char(" "))

    def test_check_char_invalid_characters(self):
        self.assertFalse(check_char("\u2603"))  # Unicode snowman (non-ASCII)
        self.assertFalse(check_char("😊")) # Emoji (non-ASCII)


# integration tests (internal)
class BrokenLinkTest(TestCase):
    # valid input, broken links, links that require access, links that have been crawled
    @patch("requests.get")
    def test_broken_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses">Courses Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff">Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/robots.txt":
                return Mock(
                    status_code=200, text="User-agent: *\nDisallow: /private/\n"
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/arts-link":
                return Mock(status_code=410)
            elif url == "https://handbook.unimelb.edu.au/2024/courses/staff":
                return Mock(status_code=401)
            elif url == "https://handbook.unimelb.edu.au/2024/courses":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"])
        self.assertIn("https://handbook.unimelb.edu.au/", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
            ],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            result[-1]["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result[:-1],
            [
                ["https://handbook.unimelb.edu.au/2024/courses/arts-link"],
                ["https://handbook.unimelb.edu.au/2024/courses/staff"],
            ],
        )

    # valid input, no broken links, private access link, links that have been crawled
    @patch("requests.get")
    def test_no_broken_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses">Courses Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/staff":
                return Mock(status_code=401)
            elif url == "https://handbook.unimelb.edu.au/2024/courses":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au"])
        self.assertIn("https://handbook.unimelb.edu.au", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au"],
            [
                "https://handbook.unimelb.edu.au",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            result[-1]["https://handbook.unimelb.edu.au"],
        )
        self.assertEqual(
            result[:-1], [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )


# integration tests (internal)
class StringMatchTest(TestCase):
    # valid input, have websites with the search term, private access link, repeated links
    @patch("requests.get")
    def test_contains_search_term(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/arts-link":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts in Melbourne</h1>
                <p>Another test page with Arts content.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/staff":
                return Mock(status_code=401)
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = scrape(
            ["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            "aRtS",
            "brave"
        )
        print("CONTAINS SEARCH TERM", result)
        self.assertIn("https://handbook.unimelb.edu.au/2024/courses/b-arts", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            [
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/b-arts",
            ],
        )
        self.assertCountEqual(
            result[0],
            [
                ("aRtS", "https://handbook.unimelb.edu.au/2024/courses/b-arts"),
                ("aRtS", "https://handbook.unimelb.edu.au/2024/courses/arts-link")
            ],
        )
        self.assertCountEqual(
            result[2], ["https://handbook.unimelb.edu.au/2024/courses/staff"]
        )

    # valid input, no websites with the search term, private access link, repeated links
    @patch("requests.get")
    def test_no_search_term(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/arts-link":
                return Mock(
                    status_code=200,
                    text="""
            <html>
            <body>
                <h1>Arts in Melbourne</h1>
                <p>Another test page with Arts content.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff">Private Access Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/staff":
                return Mock(status_code=401)
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = scrape(
            ["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            "Yeet",
            "brave"
        )
        self.assertIn("https://handbook.unimelb.edu.au/2024/courses/b-arts", result[-1])
        self.assertEqual(
            result[-1]["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            [
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/b-arts",
            ],
        )
        self.assertEqual(
            result[:-1], [[], [], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )

class SearchTest(TestCase):
    @patch("requests.get")
    def test_one_word_search(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'test'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\btest\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"])

    @patch("requests.get")
    def test_one_word_search(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'test page'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\btest(?:\s|\r\n|\r|\n)*page\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=this%20is%20a-,test%20page,-for%20the%20bachelor%20of%20arts%2E"])

    @patch("requests.get")
    def test_word_search_span_multiple_elements(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'degree this is'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bdegree(?:\s|\r\n|\r|\n)*this(?:\s|\r\n|\r|\n)*is\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=degree,this%20is"])

    @patch("requests.get")
    def test_percent_wildcard(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'te%'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bte\w*')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"])

        search_term = '%ts'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\w*ts\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=arts,-degree", 
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of-,arts,-%2E",
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of%20arts%2E-,arts,-link",
        ])

        search_term = 't%t'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bt\w*t\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"])
    
    @patch("requests.get")
    def test_question_mark_wildcard(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'te?t'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bte.t\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"])

        search_term = '?rt?'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\b.rt.\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=arts,-degree", 
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of-,arts,-%2E",
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of%20arts%2E-,arts,-link",
        ])

    @patch("requests.get")
    def test_alternation_brackets_wildcard(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>Some text.</p>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">BArts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">BArt Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'te[s|x|l]t'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bte(s|x|l)t\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=some-,text,-%2E",
            ":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"
        ])

        search_term = '[A|Ba]rt[s|]'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'(A|Ba)rt(s|\b)')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=arts,-degree", 
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of-,arts,-%2E",
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of%20arts%2E-,barts,-link",
            ":~:text=barts%20link-,bart,-link"
        ])

    @patch("requests.get")
    def test_other_wildcards_in_alternation_brackets(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == "https://handbook.unimelb.edu.au/2024/courses/b-arts":
                return Mock(
                    status_code=202,
                    text="""
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>Some teSOMERANDOMTEXTINTHEMIDDLEt.</p>
                <p>Some text.</p>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">BArts Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">BArt Link</a>
                <a href="https://handbook.unimelb.edu.au/2024/courses/staff"> Private Access Link</a>
            </body>
            </html>
            """,
                )
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")
        
        mock_get.side_effect = side_effect 
        search_term = 'te[s|x|%]t'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bte(s|x|\w*)t\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=some-,tesomerandomtextinthemiddlet,-%2E",
            ":~:text=some-,text,-%2E",
            ":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"
        ])

        search_term = 'te[?|%]t'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'\bte(.|\w*)t\b')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=some-,tesomerandomtextinthemiddlet,-%2E",
            ":~:text=some-,text,-%2E",
            ":~:text=this%20is%20a-,test,-page%20for%20the%20bachelor%20of%20arts%2E"
        ])

        search_term = '[?|B?]rt[?|]'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'(.|B.)rt(.|\b)')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=arts,-degree", 
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of-,arts,-%2E",
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of%20arts%2E-,barts,-link",
            ":~:text=barts%20link-,bart,-link"
        ])

        search_term = '[?|%]rt[?|%|]'
        pattern = create_pattern(search_term)
        self.assertEqual(pattern, r'(.|\w*)rt(.|\w*|\b)')
        fragments = search(pattern, "https://handbook.unimelb.edu.au/2024/courses/b-arts")
        self.assertEqual(fragments, [
            ":~:text=arts,-degree", 
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of-,arts,-%2E",
            ":~:text=this%20is%20a%20test%20page%20for%20the%20bachelor%20of%20arts%2E-,barts,-link",
            ":~:text=barts%20link-,bart,-link"
        ])






