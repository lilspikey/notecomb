# based on http://www.valuedlessons.com/2008/04/events-in-python.html

class Event(object):
    def __init__(self):
        self.listeners=set()
    
    def register(self, listener):
        self.listeners.add(listener)
        return self
    
    def unregister(self, listener):
        self.listeners.remove(listener)
        return self
    
    def notify(self, *args, **kw):
        for listener in self.listeners:
            listener(*args, **kw)
    
    __call__ = notify
    __iadd__ = register
    __isub__ = unregister