from django.test import TestCase
from unittest.mock import Mock, patch
from utils.broken_links import crawl
from utils.string_match import scrape, search
from utils.robots import process_robots, check_link_ok
from bs4 import BeautifulSoup
import json
import requests


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
        result = scrape(["http://example.com"], "output.json", "search text")
        self.assertEqual(result[0], [])

        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("http://example.com", json_data)
        self.assertEqual(
            json_data["http://example.com"],
            [
                "http://example.com",
                "http://example.com/page1",
                "http://example.com/page2",
            ],
        )
        self.assertNotIn("https://othersite.com/page3", json_data["http://example.com"])

        result = crawl(["http://example.com"], "output2.json")
        self.assertEqual(result[0], [])

        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("http://example.com", json_data)
        self.assertEqual(
            json_data["http://example.com"],
            [
                "http://example.com",
                "http://example.com/page1",
                "http://example.com/page2",
            ],
        )
        self.assertNotIn("https://othersite.com/page3", json_data["http://example.com"])

    @patch("requests.get")
    def test_malformed_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        result = scrape(["invalid-url"], "output.json", "search text")
        self.assertEqual(result[0], [])
        result = crawl(["invalid-url"], "output2.json")
        self.assertEqual(result[0], ["invalid-url"])

    def test_multiple_start_links(self):
        result = scrape(
            ["https://research.unimelb.edu.au", "https://www.unimelb.edu.au"],
            "output.json",
            "search text",
        )
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://research.unimelb.edu.au", json_data)
        self.assertIn("https://www.unimelb.edu.au", json_data)
        self.assertEqual(result[0], [])

        result = crawl(
            ["https://research.unimelb.edu.au", "https://www.unimelb.edu.au"],
            "output2.json",
        )
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://research.unimelb.edu.au", json_data)
        self.assertIn("https://www.unimelb.edu.au", json_data)
        self.assertEqual(result[0], [])

    def test_no_start_links(self):
        result = scrape([], "output.json", "search text")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertEqual(json_data, {})
        self.assertEqual(result, [[], []])

        result = crawl([], "output2.json")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertEqual(json_data, {})
        self.assertEqual(result, [[], []])

    def test_robots_txt(self):
        robot_rules = process_robots("User-agent: *\nDisallow: /private/\n")
        self.assertFalse(check_link_ok(robot_rules, "/private/"))
        self.assertTrue(check_link_ok(robot_rules, "/public/"))

    def test_search(self):
        soup = BeautifulSoup(
            "<html><body>This is a test string</body></html>", "html.parser"
        )
        self.assertTrue(search(soup, "This"))
        self.assertTrue(search(soup, "test string"))
        self.assertFalse(search(soup, "no string"))
        self.assertFalse(search(BeautifulSoup("<html></html>", "html.parser"), "test"))

    @patch("requests.get")
    def test_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout
        result = crawl(["https://example.com"], "output.json")
        self.assertEqual(result[0], ["https://example.com"])
        result = scrape(["https://example.com"], "output2.json", "yeet")
        self.assertEqual(result[0], [])

    @patch("requests.get")
    def test_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError
        result = crawl(["https://example.com"], "output.json")
        self.assertEqual(result[0], ["https://example.com"])
        result = scrape(["https://example.com"], "output2.json", "yeet")
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
        result = crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result, [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )

        result = scrape(["https://handbook.unimelb.edu.au/"], "output2.json", "hey")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result, [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
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
        result = crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        self.assertEqual(result[1], ["https://handbook.unimelb.edu.au/"])
        result = scrape(["https://handbook.unimelb.edu.au/"], "output2.json", "hey")
        self.assertEqual(result[1], ["https://handbook.unimelb.edu.au/"])

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
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            """,
                )
            elif url == "https://handbook.unimelb.edu.au/2024/courses/arts-link":
                return Mock(status_code=410)
            return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")

        mock_get.side_effect = side_effect
        result = crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result, [["https://handbook.unimelb.edu.au/2024/courses/arts-link"], []]
        )

        mock_get.side_effect = side_effect
        result = scrape(["https://handbook.unimelb.edu.au/"], "output2.json", "hey")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            ["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(result, [[], []])

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
        result = crawl(["https://handbook.unimelb.edu.au"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertEqual(json_data, {})
        self.assertNotIn("https://handbook.unimelb.edu.au", json_data)
        self.assertEqual(result, [["https://handbook.unimelb.edu.au"], []])

        result = scrape(["https://handbook.unimelb.edu.au"], "output2.json", "Arts")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertEqual(json_data, {})
        self.assertNotIn("https://handbook.unimelb.edu.au", json_data)
        self.assertEqual(result, [[], []])

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
        crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )

        scrape(["https://handbook.unimelb.edu.au/"], "output2.json", "hey")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
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
        crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/history",
                "https://handbook.unimelb.edu.au/2024/courses/philosophy",
            ],
        )

        scrape(["https://handbook.unimelb.edu.au/"], "output2.json", "hey")
        with open("output2.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/history",
                "https://handbook.unimelb.edu.au/2024/courses/philosophy",
            ],
        )


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
        result = crawl(["https://handbook.unimelb.edu.au/"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/"],
            [
                "https://handbook.unimelb.edu.au/",
                "https://handbook.unimelb.edu.au/2024/courses",
            ],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            json_data["https://handbook.unimelb.edu.au/"],
        )
        self.assertEqual(
            result,
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
        result = crawl(["https://handbook.unimelb.edu.au"], "output.json")
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au"],
            [
                "https://handbook.unimelb.edu.au",
                "https://handbook.unimelb.edu.au/2024/courses",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )
        self.assertNotIn(
            "https://handbook.unimelb.edu.au/2024/courses/staff",
            json_data["https://handbook.unimelb.edu.au"],
        )
        self.assertEqual(
            result, [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
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
            "output.json",
            "aRtS",
        )
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/2024/courses/b-arts", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            [
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/b-arts",
            ],
        )
        self.assertCountEqual(
            result[0],
            [
                "https://handbook.unimelb.edu.au/2024/courses/b-arts",
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
            ],
        )
        self.assertCountEqual(
            result[1], ["https://handbook.unimelb.edu.au/2024/courses/staff"]
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
            "output.json",
            "Yeet",
        )
        with open("output.json", "r") as json_file:
            json_data = json.load(json_file)
        self.assertIn("https://handbook.unimelb.edu.au/2024/courses/b-arts", json_data)
        self.assertEqual(
            json_data["https://handbook.unimelb.edu.au/2024/courses/b-arts"],
            [
                "https://handbook.unimelb.edu.au/2024/courses/arts-link",
                "https://handbook.unimelb.edu.au/2024/courses/b-arts",
            ],
        )
        self.assertEqual(
            result, [[], ["https://handbook.unimelb.edu.au/2024/courses/staff"]]
        )
