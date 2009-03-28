import unittest

from model import Document

class DocumentTestCase(unittest.TestCase):

    def setUp(self):
        self.doc=Document()

    def test_insert(self):
        self.doc.insert(0,'here')
        self.assert_(self.doc.visible_text, 'here')
        self.doc.insert(0,'again ')
        self.assertEqual(self.doc.visible_text, 'again here')
        self.doc.insert(8,'1')
        self.assertEqual(self.doc.visible_text, 'again he1re')
        self.doc.insert(8,'23')
        self.assertEqual(self.doc.visible_text, 'again he231re')
        self.doc.insert(len(self.doc.visible_text),'ing')
        self.assertEqual(self.doc.visible_text, 'again he231reing')
    
    def test_search(self):
        self.doc.insert(0,'hello there\nthis is a test\nof search')
        self.doc.search('hello')
        self.assertEqual(self.doc.visible_text, 'hello there\n')
        self.doc.search('o')
        self.assertEqual(self.doc.visible_text, 'hello there\nof search')
        self.doc.search('th')
        self.assertEqual(self.doc.visible_text, 'hello there\nthis is a test\n')
        self.doc.search('')
        self.assertEqual(self.doc.visible_text, 'hello there\nthis is a test\nof search')
    
    def test_search_and_insert(self):
        self.doc.search('test')
        self.assertEqual(self.doc.visible_text, '')
        
        self.doc.search('')
        self.doc.insert(0,'hello there\nthis is a test\nof search')
        
        self.doc.search('test')
        self.assertEqual(self.doc.visible_text, 'this is a test\n')
        self.doc.insert(0, 'again ')
        self.assertEqual(self.doc.visible_text, 'again this is a test\n')
        self.assertEqual(self.doc.text,'hello there\nagain this is a test\nof search')
        
        self.doc.search('')
        self.assertEqual(self.doc.visible_text,'hello there\nagain this is a test\nof search')
        
        self.doc.search('search')
        self.assertEqual(self.doc.visible_text, 'of search')
        self.doc.insert(0,'hello ')
        self.assertEqual(self.doc.visible_text, 'hello of search')
        
        self.doc.search('hello')
        self.assertEqual(self.doc.visible_text,'hello there\nhello of search')
        self.doc.insert(11, 'go')
        self.assertEqual(self.doc.visible_text,'hello therego\nhello of search')
        self.assertEqual(self.doc.text,'hello therego\nagain this is a test\nhello of search')
        self.doc.insert(15, '23')
        self.assertEqual(self.doc.visible_text,'hello therego\nh23ello of search')
        self.assertEqual(self.doc.text,'hello therego\nagain this is a test\nh23ello of search')
        