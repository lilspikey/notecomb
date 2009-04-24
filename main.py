import wx
import wx.stc

import sys

from notecomb import NoteCombFrame
from wxdoc import DocApp

if __name__ == '__main__':
    class App(DocApp):
        __APP_NAME__='NoteComb'
        __DOC_FRAME__=NoteCombFrame
        
    app=App(redirect=False)
    app.MainLoop()