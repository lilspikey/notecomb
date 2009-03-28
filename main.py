import wx
import wx.stc
import sys

from model import Document

class MainFrame(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,title='Observertron')
        
        
        self.doc=Document()
        
        self.menubar=wx.MenuBar()
        
        self.search=wx.SearchCtrl(self)
        self.search.ShowCancelButton(True)
        
        self.text=wx.stc.StyledTextCtrl(self,style=wx.TE_MULTILINE|wx.NO_BORDER|wx.WANTS_CHARS)
        
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.Modified)
        self.Bind(wx.EVT_TEXT, self.Search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.SearchCancelled)
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.search, 0, flag=wx.EXPAND)
        sizer.AddSpacer((5,5))
        sizer.Add(self.text, 1, flag=wx.EXPAND|wx.GROW|wx.ALL)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer)
        self.Layout()
    
    def SearchCancelled(self,event):
        self.search.SetValue('')
    
    def Search(self,event):
        q=self.search.GetValue()
        self.doc.search(q)
        self._update_visible_text()
    
    def _update_visible_text(self):
        mod_mask=self.text.GetModEventMask()
        self.text.SetModEventMask(0)
        self.text.SetText(self.doc.visible_text)
        self.text.SetModEventMask(mod_mask)
    
    def Modified(self,event):
        mod_type=event.GetModificationType()
        action=None
        
        if mod_type & wx.stc.STC_MOD_INSERTTEXT:
            action=self.ModifiedInsertText
        elif mod_type & wx.stc.STC_MOD_DELETETEXT:
            action=self.ModifiedDeleteText
        
        if action:
            action(event)
        
        print mod_type, wx.stc.STC_MOD_INSERTTEXT
        print repr(self.doc.visible_text)
        print repr(self.text.GetText())
    
    def ModifiedInsertText(self, event):
        if self.doc.visible_text != self.text.GetText():
            offset=event.GetPosition()
            text=event.GetText()
        
            self.doc.insert(offset, text)
    
    def ModifiedDeleteText(self, event):
        if self.doc.visible_text != self.text.GetText():
            offset=event.GetPosition()
            length=event.GetLength()
        
            self.doc.remove(offset, length)

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