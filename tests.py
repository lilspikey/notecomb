import unittest
import random

from model import Document, UndoableDocument

class DocumentTestCase(unittest.TestCase):

    def setUp(self):
        self.doc=Document()

    def test_insert(self):
        self.doc.insert(0,'here')
        self.assertEqual(self.doc.visible_text, 'here')
        
        self.doc.insert(0,'again ')
        self.assertEqual(self.doc.visible_text, 'again here')
        
        self.doc.insert(8,'1')
        self.assertEqual(self.doc.visible_text, 'again he1re')
        
        self.doc.insert(8,'23')
        self.assertEqual(self.doc.visible_text, 'again he231re')
        
        self.doc.insert(len(self.doc.visible_text),'ing')
        self.assertEqual(self.doc.visible_text, 'again he231reing')
    
    def test_remove(self):
        self.doc.insert(0,'here is some stuff\nover a few lines')
        self.assertEqual(self.doc.visible_text, 'here is some stuff\nover a few lines')
        
        self.doc.remove(0,5)
        self.assertEqual(self.doc.visible_text, 'is some stuff\nover a few lines')
        
        self.doc.remove(1,1)
        self.assertEqual(self.doc.visible_text, 'i some stuff\nover a few lines')
        
        self.doc.remove(len(self.doc.visible_text)-4,4)
        self.assertEqual(self.doc.visible_text, 'i some stuff\nover a few l')
    
    
    def test_search(self):
        self.doc.insert(0,'hello there\nthis is a test\nof search')
        self.doc.search('hello')
        self.assertEqual(self.doc.current_search, 'hello')
        
        self.assertEqual(self.doc.visible_text, 'hello there')
        self.doc.search('o')
        self.assertEqual(self.doc.visible_text, 'hello there\nof search')
        self.doc.search('th')
        self.assertEqual(self.doc.visible_text, 'hello there\nthis is a test')
        self.doc.search('')
        self.assertEqual(self.doc.visible_text, 'hello there\nthis is a test\nof search')
    
    def test_search_and_insert(self):
        self.doc.search('test')
        self.assertEqual(self.doc.visible_text, '')
        
        self.doc.search('')
        self.doc.insert(0,'hello there\nthis is a test\nof search')
        
        self.doc.search('test')
        self.assertEqual(self.doc.visible_text, 'this is a test')
        self.doc.insert(0, 'again ')
        self.assertEqual(self.doc.visible_text, 'again this is a test')
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
    
    def test_search_and_remove(self):
        self.doc.search('')
        self.doc.insert(0,'hello there\nthis is a test\nof search\nhello there')
        
        self.doc.search('hello')
        self.assertEqual(self.doc.visible_text, 'hello there\nhello there')
        
        self.doc.remove(0, 3)
        self.assertEqual(self.doc.visible_text, 'lo there\nhello there')
        
        self.doc.remove(len(self.doc.visible_text)-3, 3)
        self.assertEqual(self.doc.visible_text, 'lo there\nhello th')
        
        # now remove accross multiple visible regions
        self.doc.remove(7, 3)
        self.assertEqual(self.doc.visible_text, 'lo therello th')
        
        # finally check underlying text matches what we expect
        self.assertEqual(self.doc.text, 'lo therello th\nthis is a test\nof search\n')
    
    def test_insert_remove(self):
        # in the simple case (without search) inserting them remove should
        # have no effect
        self.doc.insert(0,'hello there this is a test\n of inserting and removing\nsome text')
        self._check_inserting_and_removing()
    
    def test_insert_remove_while_searching(self):
        # when inserting and removing (in that order) with search nothing should change either
        self.doc.insert(0,'hello there this is a test\n of inserting and removing\nsome text')
        
        self.doc.search('te')
        self._check_inserting_and_removing()
        
        self.doc.search('hello')
        self._check_inserting_and_removing()
        
        self.doc.search('inserting')
        self._check_inserting_and_removing()
        
        self.doc.search('some')
        self._check_inserting_and_removing()
        
        # now try a search with no visible lines
        self.doc.search('876fdjfdsf87')
        self._check_inserting_and_removing()
    
    def _check_inserting_and_removing(self):
        for i in range(0,200):
            text_length=len(self.doc.visible_text)
            offset=random.choice(range(text_length+1))
            length=random.choice(range(text_length+1)) + 1
            
            s=''.join(random.choice('gsgs8hkjefw98y') for i in range(length))
            
            visible_text_before=self.doc.visible_text
            text_before=self.doc.text
            
            self.doc.insert(offset, s)
            self.assert_( visible_text_before != self.doc.visible_text )
            self.assert_( text_before != self.doc.text )
            
            self.doc.remove(offset, length)
            self.assertEqual( self.doc.visible_text, visible_text_before )
            self.assertEqual( self.doc.text, text_before )

class UndoableDocumentTestCase(unittest.TestCase):
    
    def setUp(self):
        self.doc=UndoableDocument()
    
    def test_undo_insert(self):
        self.doc.insert(0,'here is some text')
        self.assertEqual( self.doc.text, 'here is some text' )
        
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assert_( not self.doc.can_undo() )
        self.assertEqual( self.doc.text, '' )
        
        self.doc.insert(0,'here is some text')
        self.doc.insert(2,'3')
        self.assertEqual( self.doc.text, 'he3re is some text' )
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assert_( self.doc.can_undo() )
        self.assertEqual( self.doc.text, 'here is some text' )
    
    def test_undo_remove(self):
        self.doc.insert(0,'here is some text')
        self.assertEqual( self.doc.text, 'here is some text' )
        
        self.doc.remove(1, 2)
        self.assertEqual( self.doc.text, 'he is some text' )
        
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assertEqual( self.doc.text, 'here is some text' )
    
    def test_undo_insert_search(self):
        self.doc.insert(0,'here is some text\nhello there')
        self.doc.search('hello')
        self.assertEqual( self.doc.visible_text, 'hello there' )
        
        self.doc.insert(0, '123 ')
        self.assertEqual( self.doc.visible_text, '123 hello there' )
        self.assertEqual( self.doc.text, 'here is some text\n123 hello there')
        
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        
        self.assertEqual( self.doc.visible_text, 'hello there' )
        self.assertEqual( self.doc.text, 'here is some text\nhello there')
        
        self.assertEqual( self.doc.current_search, 'hello')
        
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assert_( not self.doc.can_undo() )
        
        self.assertEqual( self.doc.current_search, '')
        self.assertEqual( self.doc.visible_text, '' )
        self.assertEqual( self.doc.text, '')
    
    def test_undo_remove_search(self):
        self.doc.insert(0,'here is some text\nhello there')
        self.doc.search('hello')
        self.assertEqual( self.doc.visible_text, 'hello there' )
        
        self.doc.remove(1, 2)
        self.assertEqual( self.doc.visible_text, 'hlo there' )

        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assertEqual( self.doc.current_search, 'hello')
        self.assertEqual( self.doc.visible_text, 'hello there' )
        self.assertEqual( self.doc.text, 'here is some text\nhello there' )
    
    def test_undo_remove_search_accross_visible(self):
        self.doc.insert(0,'hello today\nhere is some text\nhello there')
        self.doc.search('hello')
        self.assertEqual( self.doc.visible_text, 'hello today\nhello there' )
        
        self.doc.remove(10, 3)
        self.assertEqual( self.doc.visible_text, 'hello todaello there' )
        self.assertEqual( self.doc.text, 'hello todaello there\nhere is some text\n' )
        
        self.assert_( self.doc.can_undo() )
        self.doc.undo()
        self.assertEqual( self.doc.current_search, 'hello')
        self.assertEqual( self.doc.visible_text, 'hello today\nhello there' )
        self.assertEqual( self.doc.text, 'hello today\nhere is some text\nhello there' )
        
        self.doc.undo()
        self.assertEqual( self.doc.visible_text, self.doc.text )
        self.assertEqual( self.doc.text, '' )