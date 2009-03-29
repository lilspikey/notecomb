import wx
import wx.stc
import sys

from model import UndoableDocument

class MainFrame(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,title='Observertron')
        
        
        self.doc=UndoableDocument()
        
        self.menubar=wx.MenuBar()
        
        edit_menu=wx.Menu()
        self.undo_menu_item=edit_menu.Append(-1,"Undo\tCtrl-Z")
        self.Bind(wx.EVT_MENU, self.OnUndo, self.undo_menu_item)
        self.redo_menu_item=edit_menu.Append(-1,"Redo\tShift-Ctrl-Z")
        self.Bind(wx.EVT_MENU, self.OnRedo, self.redo_menu_item)
        #edit_menu.AppendSeparator()
        
        self.menubar.Append(edit_menu, "&Edit")
        
        self.SetMenuBar(self.menubar)
        
        self.panel=wx.Panel(self)
        
        self.search=wx.SearchCtrl(self.panel)
        self.search.ShowCancelButton(True)
        
        self.text=wx.stc.StyledTextCtrl(self.panel,style=wx.TE_MULTILINE|wx.NO_BORDER|wx.WANTS_CHARS)
        self.text.SetCaretLineVisible(True)
        self.text.SetUseAntiAliasing(True)
        self.text.ConvertEOLs(wx.stc.STC_EOL_LF)
        self.text.SetEOLMode(wx.stc.STC_EOL_LF)
        self.text.SetUndoCollection(0)
        
        style=self.text.GetStyleAt(0)
        self.text.StyleSetEOLFilled(style,True)
        self.text.SetMarginType(0,wx.stc.STC_MARGIN_NUMBER)
        self.text.SetMarginWidth(0,16)
        self.text.SetMargins(0,0)
        self.text.SetMarginWidth(1,0)
        self.text.SetWrapMode(wx.stc.STC_WRAP_WORD)
        
        self.SetRegularColours()
        
        self.Bind(wx.stc.EVT_STC_MODIFIED, self.Modified)
        self.Bind(wx.EVT_TEXT, self.Search)
        self.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.SearchCancelled)
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.search, 0, flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add((5,5), 0)
        sizer.Add(self.text, 1, flag=wx.EXPAND|wx.GROW|wx.ALL)
        
        self.panel.SetSizer(sizer)
        self.Layout()
        
        self.UpdateFromDoc()
    
    def UpdateFromDoc(self):
        self.UpdateMenus()
        self.search.ChangeValue(self.doc.current_search)
        self._update_colours()
        self._update_visible_text()
    
    def UpdateMenus(self):
        self.undo_menu_item.Enable(self.doc.can_undo())
        self.redo_menu_item.Enable(self.doc.can_redo())
    
    def SetRegularColours(self):
        self.text.SetForegroundColour('#000000')
        self.text.SetBackgroundColour('#FFFFFF')
        self.text.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT,'#FFFFFF')
        style=self.text.GetStyleAt(0)
        self.text.StyleSetBackground(style,'#FFFFFF')
        self.text.SetCaretLineBackground('#EEEEEE')
    
    def SetSearchColours(self):
        self.text.SetForegroundColour('#000000')
        self.text.SetBackgroundColour('#FFFF99')
        self.text.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT,'#FFFF99')
        style=self.text.GetStyleAt(0)
        self.text.StyleSetBackground(style,'#FFFF99')
        self.text.SetCaretLineBackground('#EEEE99')
    
    def OnUndo(self,event):
        if self.doc.can_undo():
            self.doc.undo()
            self.UpdateFromDoc()
    
    def OnRedo(self,event):
        if self.doc.can_redo():
            self.doc.redo()
            self.UpdateFromDoc()
    
    def _update_colours(self):
        if self.doc.current_search:
            self.SetSearchColours()
        else:
            self.SetRegularColours()
    
    def SearchCancelled(self,event):
        self.search.SetValue('')
    
    def Search(self,event):
        q=self.search.GetValue()    
        self.doc.search(q)
        self._update_colours()
        self._update_visible_text()
    
    def _update_visible_text(self):
        # disable modification events while we
        # update the text in the text area
        mod_mask=self.text.GetModEventMask()
        self.text.SetModEventMask(0)
        self.text.SetText(self.doc.visible_text)
        self.text.GotoPos(self.doc.current_offset)
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
        
        self.UpdateMenus()
    
    def ModifiedInsertText(self, event):
        offset=event.GetPosition()
        text=self.text.GetTextRange(offset, offset+event.GetLength())
        self.doc.insert(offset, text)
    
    def ModifiedDeleteText(self, event):
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