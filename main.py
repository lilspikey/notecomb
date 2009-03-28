import wx
import wx.stc
import sys

class MainFrame(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,title='Observertron')
        
        self.menubar=wx.MenuBar()
        
        self.text=wx.stc.StyledTextCtrl(self,style=wx.TE_MULTILINE|wx.NO_BORDER|wx.WANTS_CHARS)
        
        self.text.SetText('\n'.join(["one","two","three","four"]))
        #self.text.SetFoldFlags(64)
        #self.text.HideLines(0,1)
        
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.Modified)
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.text, 1, flag=wx.EXPAND)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Layout()
    
    def Modified(self,event):
        print "event.GetModificationType()", event.GetModificationType()
        print "event.GetLine()", event.GetLine()
        print "event.GetPosition()", event.GetPosition()
        print "event.GetLinesAdded()", event.GetLinesAdded()
        print "event.GetText()", event.GetText()

class App(wx.App):

    def OnInit(self):
        self.SetAppName('Observertron')
        frame=MainFrame(None)

        #frame.CenterOnScreen()
        #frame.SetSize(wx.DisplaySize())

        frame.Show()
        #frame.ShowFullScreen(True)
        #frame.SetPosition((0,0))

        #for name in sys.argv[1:]:
        #    frame.Load(name)

        return True

app=App(redirect=False)
app.MainLoop()