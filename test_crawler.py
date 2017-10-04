import unittest
from crawler import crawler

class TestCrawlerMethods(unittest.TestCase):

    # run crawler on test urls
    _cr = crawler(None,'test_urls.txt') #change urls.txt to test_urls.txt
    _cr.crawl(depth=1)
    print '\n----------------------------------------------------------------------\n'

    # test resolve_word function
    def test_resolve_word(self):
        self.assertEqual('boy',self._cr.resolve_word(6))
        self.assertEqual('fat',self._cr.resolve_word(1))


    # test resolve_document function
    def test_resolve_document(self):
        self.assertEqual('http://localhost:8080/test/page3.html',self._cr.resolve_document(4))
        self.assertEqual('http://localhost:8080/test',self._cr.resolve_document(1))

    # test get_lexicon
    def test_get_lexicon(self):
        expected_dictionary={'boy':6, 'dog':5, 'egg':4, 'cat':3, 'ant':2, 'fat':1}
        self.assertDictEqual(expected_dictionary,self._cr.get_lexicon())

    # test get_document_index
    def test_get_document_index(self):
        expected_dictionary={
            'http://localhost:8080/test/page5.html':6,
            'http://localhost:8080/test/page4.html':5, 
            'http://localhost:8080/test/page3.html':4,
            'http://localhost:8080/test/page2.html':3,
            'http://localhost:8080/test/page1.html':2,
            'http://localhost:8080/test':1
        }
        self.assertDictEqual(expected_dictionary,self._cr.get_document_index())

    # test get_inverted_index
    def test_get_inverted_index(self):
        expected_dictionary={
            1: set([6]),
            2: set([5]),
            3: set([5, 4, 3, 2]),
            4: set([5]),
            5: set([4, 2]),
            6: set([3, 2])
        }
        self.assertDictEqual(expected_dictionary,self._cr.get_inverted_index())

    # test get_resolved_inverted_index
    def test_get_resolved_inverted_index(self):
        expected_dictionary={
            'fat': set(['http://localhost:8080/test/page5.html']),
            'ant': set(['http://localhost:8080/test/page4.html']),
            'cat': set(['http://localhost:8080/test/page4.html', 'http://localhost:8080/test/page3.html', 'http://localhost:8080/test/page2.html', 'http://localhost:8080/test/page1.html']),
            'egg': set(['http://localhost:8080/test/page4.html']),
            'dog': set(['http://localhost:8080/test/page3.html', 'http://localhost:8080/test/page1.html']),
            'boy': set(['http://localhost:8080/test/page2.html', 'http://localhost:8080/test/page1.html'])
        }
        self.assertDictEqual(expected_dictionary,self._cr.get_resolved_inverted_index())

suite = unittest.TestLoader().loadTestsFromTestCase(TestCrawlerMethods)
unittest.TextTestRunner(verbosity=2).run(suite)