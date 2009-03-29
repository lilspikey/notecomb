from copy import copy
from difflib import SequenceMatcher

class Document(object):
    def __init__(self):
        self._text=''
        self.search('')
    
    def search(self,q):
        if q:
            self._visible=[]
            offset=0
            # TODO merge visible lines together
            for line in self._text.splitlines(True):
                if q in line:
                    length = len(line)
                    self._visible.append(self.Visible(offset,length))
                offset += len(line)
            if not self._visible:
                self._visible.append(self.Visible(0,0))
            else:
                # make the last visible section's line ending not visible
                # so we don't get an empty line showing int he search results
                last_visible=self._visible[-1]
                text=last_visible.text(self._text)
                if text.endswith("\n"):
                    last_visible.length -=1
        else:
            self._visible=[self.Visible(0,len(self._text))]
        self.current_search=q
    
    @property
    def visible_text(self):
        return ''.join(v.text(self._text) for v in self._visible)
    
    @property
    def text(self):
        return self._text
    
    def insert(self, offset, text):
        visible_offset, visible, other_visible = self._find_visible_from_offset(offset)
        actual_offset=visible.offset + (offset-visible_offset)
        self._insert_text(actual_offset, text)
        length=len(text)
        visible.length += length
        # shift other visible sections along by same amount
        self._move_visible(other_visible,length)
    
    def _find_visible_from_offset(self,offset):
        visible_offset=0
        for i, visible in enumerate(self._visible):
            if visible_offset <= offset <= visible_offset+visible.length:
                return visible_offset, visible, self._visible[i+1:]
            visible_offset += visible.length
        raise ValueError("invalid offset %d" % offset)
    
    def _move_visible(self,visible,length):
        for v in visible:
            v.offset += length
    
    def remove(self, offset, length):
        length_removed=0
        while length:
            visible_offset, visible, other_visible = self._find_visible_from_offset(offset+1)
            actual_offset=visible.offset + (offset-visible_offset)
        
            # how much we can remove from this visible section
            length_removed=min(length, visible.length-(offset-visible_offset))
            self._remove_text(actual_offset, length_removed)
            visible.length -= length_removed
        
            self._move_visible(other_visible,-length_removed)
            
            length -= length_removed
        self._merge_visible()
    
    def _remove_text(self, offset, length):
        '''remove text from the underlying text'''
        self._text=self._text[:offset]+self._text[offset+length:]
    
    def _insert_text(self, offset, text):
        '''insert text into underlying text'''
        self._text=self._text[:offset]+text+self._text[offset:]
    
    def _move_text(self,from_offset,to_offset,length):
        text=self._text[from_offset:from_offset+length]
        self._remove_text(from_offset, length)
        self._insert_text(to_offset, text)

    
    def _merge_visible(self):
        # any visible lines that are now joined together,
        # should be joined together in the real underlying text
        while True:
            merged=False
            for i, visible in enumerate(self._visible[:-1]):
                text=visible.text(self._text)
                if not text.endswith("\n"):
                    merged=True
                    other_visible=self._visible[i+1]
                    other_length=other_visible.length
                    self._move_text(other_visible.offset, visible.offset+visible.length, other_length)
                    
                    self._visible.remove(other_visible)
                    
                    visible.length += other_length
                    self._move_visible(self._visible[i+1:], other_length)
                    
                    break
            if not merged:
                # make sure there's a newline after the last visible section (if there's more text after it)
                last_visible=self._visible[-1]
                text=last_visible.text(self._text)
                if not text.endswith("\n"):
                    last_offset=last_visible.offset+last_visible.length
                    # check if more text after visible and not empty
                    if last_offset < len(self._text) and not last_visible.is_empty:
                        text_after=self._text[last_offset:]
                        if not text_after.startswith("\n"):
                            self._insert_text(last_offset, "\n")
                return
    
    
    class Visible(object):
        def __init__(self,offset,length):
            self.offset=offset
            self.length=length
        
        def text(self,text):
            return text[self.offset:self.offset+self.length]
        
        @property
        def is_empty(self):
            return self.length == 0

def undoable(fn):
    def _decorated(self,*args):
        self.current_undo=UndoAction(self)
        fn(self, *args)
        self.undos.append(self.current_undo)
        self.current_undo=None
    return _decorated


class UndoableDocument(Document):

    def __init__(self):
        super(UndoableDocument,self).__init__()
        self.undos=[]
        self.current_undo=None
    
    def can_undo(self):
        return len(self.undos) > 0
    
    def undo(self):
        if self.can_undo():
            last_undo,self.undos=self.undos[-1],self.undos[:-1]
            last_undo.undo(self)
    
    @undoable
    def insert(self, offset, text):
        super(UndoableDocument,self).insert(offset, text)
    
    @undoable
    def remove(self, offset, length):
        super(UndoableDocument,self).remove(offset,length)
    
    def _insert_text(self, offset, text):
        if self.current_undo:
            self.current_undo.append(UndoInsert(self, offset, text))
        super(UndoableDocument,self)._insert_text(offset, text)
    
    def _remove_text(self, offset, length):
        if self.current_undo:
            self.current_undo.append(UndoInsert(self, offset, length))
        super(UndoableDocument,self)._remove_text(offset, length)


class UndoAction(object):
    def __init__(self, doc):
        self.visible=[copy(v) for v in doc._visible]
        self.current_search=doc.current_search
        self.actions=[]
    
    def undo(self, doc):
        doc._visible=self.visible
        doc.current_search=self.current_search
        for action in reversed(self.actions):
            action.undo(doc)
    
    def append(self, action):
        self.actions.append(action)

class UndoInsert(object):
    
    def __init__(self, doc, offset, text):
        self.offset=offset
        self.text=text
    
    def undo(self, doc):
        doc._remove_text(self.offset,len(self.text))

class UndoRemove(object):

    def __init__(self, doc, offset, length):
        self.offset=offset
        self.text=doc.text[offset:offset+length]

    def undo(self, doc):
        doc._insert_text(self.offset,self.text)



            