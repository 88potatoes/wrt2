from django.test import TestCase

# Create your tests here.

class SampleTest(TestCase):
    def test_passing_sample1(self):
        self.assertTrue(True)

    def test_passing_sample2(self):
        self.assertTrue(2 == 1 + 1)