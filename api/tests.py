from django.test import TestCase
from unittest.mock import Mock, patch
from utils.broken_links import crawl
from utils.string_match import scrape, search
from utils.robots import process_robots, check_link_ok
from bs4 import BeautifulSoup
import requests
import json

# Create your tests here.

class SampleTest(TestCase):
    @patch('requests.get')
    def test_link_extraction(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = '''
        <html>
        <body>
            <a href="http://example.com/page1">Link 1</a>
            <a href="/page2">Link 2</a>
            <a href="https://othersite.com/page3">Link 3</a>
        </body>
        </html>
        '''
        result = scrape(['http://example.com'], 'output.json', 'search text')
        self.assertEqual(result, [])

        with open('output.json', 'r') as json_file:
            json_data = json.load(json_file)
        self.assertIn('http://example.com', json_data)
        self.assertEqual(json_data['http://example.com'], ['http://example.com','http://example.com/page1', 'http://example.com/page2'])
        self.assertNotIn('https://othersite.com/page3', json_data['http://example.com'])

        result = crawl(['http://example.com'], 'output.json')
        self.assertEqual(result, [])

        with open('output.json', 'r') as json_file:
            json_data = json.load(json_file)
        self.assertIn('http://example.com', json_data)
        self.assertEqual(json_data['http://example.com'], ['http://example.com','http://example.com/page1', 'http://example.com/page2'])
        self.assertNotIn('https://othersite.com/page3', json_data['http://example.com'])

    @patch('requests.get')
    def test_malformed_url(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 404
        result = scrape(['invalid-url'], 'output.json', 'search text')
        self.assertEqual(result,[])
        result = crawl(['invalid-url'], 'output.json')
        self.assertEqual(result,['invalid-url'])

    def test_multiple_start_links(self):
        result = scrape(['https://research.unimelb.edu.au', 'https://www.unimelb.edu.au'], 'output.json', 'search text')
        with open('output.json', 'r') as json_file:
            json_data = json.load(json_file)
        self.assertIn('https://research.unimelb.edu.au', json_data)
        self.assertIn('https://www.unimelb.edu.au', json_data)
        self.assertEqual(result,[])

        result = crawl(['https://research.unimelb.edu.au', 'https://www.unimelb.edu.au'], 'output.json')
        with open('output.json', 'r') as json_file:
            json_data = json.load(json_file)
        self.assertIn('https://research.unimelb.edu.au', json_data)
        self.assertIn('https://www.unimelb.edu.au', json_data)
        self.assertEqual(result,[])
    
    def test_robots_txt(self):
        robot_rules = process_robots("User-agent: *\nDisallow: /private/\n")
        self.assertFalse(check_link_ok(robot_rules, '/private/'))
        self.assertTrue(check_link_ok(robot_rules, '/public/'))
    
    def test_search(self):
        soup = BeautifulSoup('<html><body>This is a test string</body></html>', 'html.parser')
        self.assertTrue(search(soup, 'This'))
        self.assertTrue(search(soup, 'test string'))
        self.assertFalse(search(soup, 'no string'))
        self.assertFalse(search(BeautifulSoup('<html></html>', 'html.parser'), 'test'))

    # broken links
    # valid input, no broken links
    @patch('requests.get')
    def test_no_broken_links(self, mock_get):
        mock_get.side_effect = [
            Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n"),
            Mock(status_code=200, text='''
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            '''),
            Mock(status_code=200)
        ]
        result = crawl(['https://handbook.unimelb.edu.au'], 'output.json')
        self.assertEqual(result, [])

    # valid input, broken links
    @patch('requests.get')
    def test_are_broken_links(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == 'https://handbook.unimelb.edu.au/':
                return Mock(status_code=200, text='''
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            ''')
            elif url == 'https://handbook.unimelb.edu.au/robots.txt':
                return Mock(status_code=200, text="User-agent: *\nDisallow: /private/\n")  
            elif url == 'https://handbook.unimelb.edu.au/2024/courses/arts-link':
                return Mock(status_code=404)

        mock_get.side_effect = side_effect
        result = crawl(['https://handbook.unimelb.edu.au/'], 'output.json')
        print(result)
        self.assertEqual(len(result), 1)
    
    # broken link as input
    @patch('requests.get')
    def test_broken_links_input(self, mock_get):
        def side_effect(url, *args, **kwargs):
            if url == 'https://indigenousknowledge.unimelb.edu.au/resources/indigenous-research2/research-ethics':
                return Mock(status_code=404, text='''
            <html>
            <body>
                <h1>Arts Degree</h1>
                <p>This is a test page for the Bachelor of Arts.</p>
                <a href="https://handbook.unimelb.edu.au/2024/courses/arts-link">Arts Link</a>
            </body>
            </html>
            ''')
            elif url == 'https://handbook.unimelb.edu.au/2024/courses/arts-link':
                return Mock(status_code=404)
        mock_get.side_effect = side_effect
        result = crawl(['https://indigenousknowledge.unimelb.edu.au/resources/indigenous-research2/research-ethics'], 'output.json')
        self.assertEqual(result, ['https://indigenousknowledge.unimelb.edu.au/resources/indigenous-research2/research-ethics'])



    # integration tests
    # test empty start link
    # def test_empty_start_links(self):
    #     result = scrape([], 'output.json', 'search text')
    #     self.assertEqual(result, [])
    #     result = crawl([], 'output.json')
    #     self.assertEqual(result, [])

    
    



    


