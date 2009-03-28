
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
            self._visible=[self.Visible(0,len(self._text))]
    
    @property
    def visible_text(self):
        return ''.join(v.visible(self._text) for v in self._visible)
    
    @property
    def text(self):
        return self._text
    
    def insert(self, offset, text):
        current_offset=0
        for i, visible in enumerate(self._visible):
            if current_offset <= offset <= current_offset+visible.length:
                actual_offset=visible.offset + (offset-current_offset)
                self._text=self._text[:actual_offset]+text+self._text[actual_offset:]
                length=len(text)
                visible.length += length
                # shift other visible sections along by same amount
                self._move_visible(self._visible[i+1:],length)
                break
            current_offset += visible.length
    
    def _move_visible(self,visible,length):
        for v in visible:
            v.offset += length
    
    def remove(self, offset, length):
        pass
    
    class Visible(object):
        def __init__(self,offset,length):
            self.offset=offset
            self.length=length
        
        def visible(self,text):
            return text[self.offset:self.offset+self.length]
        