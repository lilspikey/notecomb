import tempfile
import os, os.path
import time
import mmap
import sys
try:
    import cPickle as pickle
except ImportError:
    import pickle

'''
this is based on the code from pydocview, but packaged up into
a class that doesn't depend on wx
'''

def open_shared_mem(name):
    if sys.platform == 'win32':
        tfile = tempfile.TemporaryFile(prefix=name,suffix="tmp")
        fno = tfile.fileno()
        return mmap.mmap(fno, 1024, tagname='shared_memory')
    else:
        tfile = file(os.path.join(tempfile.gettempdir(), tempfile.gettempprefix() + name + "SharedMemory"), 'w+b')
        # ensure at least 1024 bytes in file
        tfile.write("*")
        tfile.seek(1024)
        tfile.write(" ")
        tfile.flush()
        fno = tfile.fileno()
        return mmap.mmap(fno, 1024)

class Pipe(object):
    def __init__(self, name):
        self._sharedMemory = open_shared_mem(name)
    
    def write(self, data):
        '''write into shared memory, once we are able to'''
        data = pickle.dumps(data)
        while True:
            self._sharedMemory.seek(0)
            marker = self._sharedMemory.read_byte()
            if marker == '\0' or marker == '*':
                self._sharedMemory.seek(0)
                self._sharedMemory.write('-')
                self._sharedMemory.write(data)
                self._sharedMemory.seek(0)
                self._sharedMemory.write('+')
                self._sharedMemory.flush()
                break
            else:
                time.sleep(1)
    
    def read(self):
        self._sharedMemory.seek(0)
        marker = self._sharedMemory.read_byte()
        if marker == '+':
            data = self._sharedMemory.read(1024-1)
            self._sharedMemory.seek(0)
            self._sharedMemory.write_byte("*")
            self._sharedMemory.flush()
            
            return pickle.loads(data)
        return None