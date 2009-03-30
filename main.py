import wx
import wx.stc
import sys

from model import UndoableDocument

APP_NAME='Observertron'

class DocumentFrame(wx.Frame):
    '''
    class to hook up standard menus etc
    '''
    
    __DOCUMENT_CLASS__=None
    
    def __init__(self,*args,**kw):
        super(DocumentFrame,self).__init__(*args,**kw)
        
        self.doc=self.__DOCUMENT_CLASS__()
        
        self.menubar=wx.MenuBar()
        
        # file menu
        self.file_menu=wx.Menu()
        self.menubar.Append(self.file_menu, "&File")
        
        self.AddMenuItem(self.file_menu, "New\tCtrl-N", self.OnNew, -1)
        self.AddMenuItem(self.file_menu, "Open...\tCtrl-O", self.OnOpen, -1)
        self.file_menu.AppendSeparator()
        
        self.file_save=self.AddMenuItem(self.file_menu, "Save\tCtrl-S", self.OnSave, -1)
        self.AddMenuItem(self.file_menu, "Save As...\tShift-Ctrl-S", self.OnSaveAs, -1)
        self.file_menu.AppendSeparator()
        
        self.AddMenuItem(self.file_menu, "Preferences...\tCtrl-K", self.OnPreferences, -1)
        self.file_menu.AppendSeparator()
        
        self.AddMenuItem(self.file_menu, "Quit %s\tCtrl-Q" % APP_NAME, self.OnQuit, -1)
        
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        self.edit_menu=wx.Menu()
        self.menubar.Append(self.edit_menu, "&Edit")
        
        self.edit_undo=self.AddMenuItem(self.edit_menu, "Undo\tCtrl-Z", self.OnUndo, wx.ID_UNDO)
        self.edit_redo=self.AddMenuItem(self.edit_menu, "Redo\tShift-Ctrl-Z", self.OnRedo, wx.ID_REDO)
        
        self.SetMenuBar(self.menubar)
        
        self.UpdateMenus()
    
    def AddMenuItem(self, menu, label, handler, id):
        menu_item=menu.Append(id,label)
        self.Bind(wx.EVT_MENU, handler, menu_item)
        return menu_item
    
    def UpdateFromDoc(self):
        self.UpdateMenus()
    
    def UpdateMenus(self):
        self.file_save.Enable(not self.doc.is_saved)
        self.edit_undo.Enable(self.doc.can_undo())
        self.edit_redo.Enable(self.doc.can_redo())
    
    def OnNew(self,event):
        # TODO check for modifications
        self.doc=self.__DOCUMENT_CLASS__()
        self.UpdateFromDoc()
    
    def OnOpen(self,event):
        # TODO check for modifications
        dialog=wx.FileDialog(self,"Open File",'','','Obs File (*.obs)|*.obs|All File|*.*', wx.FD_OPEN)
        dialog.Centre()
        filename=None
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
        dialog.Destroy()
        
        if filename:
            self.doc.open(filename)
            self.UpdateFromDoc()
    
    def OnSave(self,event):
        if self.doc.filename:
            self.doc.save()
            self.UpdateMenus()
        else:
            self.OnSaveAs(event)
    
    def OnSaveAs(self,event):
        dialog=wx.FileDialog(self,"Save File As...",'','','Obs File (*.obs)|*.obs|All File|*.*', wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        dialog.Centre()
        filename=None
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
        dialog.Destroy()
        
        if filename:
            self.doc.save_as(filename)
            self.UpdateMenus()
    
    def OnPreferences(self,event):
        pass
    
    def OnQuit(self,event):
        # TODO check whether modified
        self.Destroy()
    
    def OnUndo(self,event):
        if self.doc.can_undo():
            self.doc.undo()
            self.UpdateFromDoc()
    
    def OnRedo(self,event):
        if self.doc.can_redo():
            self.doc.redo()
            self.UpdateFromDoc()
    
    
    
class MainFrame(DocumentFrame):
    
    __DOCUMENT_CLASS__=UndoableDocument
    
    def __init__(self,parent):
        super(MainFrame,self).__init__(parent,title='Observertron')
        
        self.panel=wx.Panel(self)
        
        self.search=wx.SearchCtrl(self.panel)
        self.search.ShowCancelButton(True)
        
        self.text=wx.stc.StyledTextCtrl(self.panel,style=wx.TE_MULTILINE|wx.NO_BORDER|wx.WANTS_CHARS)
        self.text.SetCaretLineVisible(True)
        self.text.SetUseAntiAliasing(True)
        self.text.ConvertEOLs(wx.stc.STC_EOL_LF)
        self.text.SetEOLMode(wx.stc.STC_EOL_LF)
        self.text.SetUndoCollection(0)
        self.text.SetFocus()
        
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
        self.text.Bind(wx.EVT_SET_FOCUS, self.TextSetFocus)
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        sizer.Add(self.search, 0, flag=wx.EXPAND|wx.ALL, border=5)
        sizer.Add((5,5), 0)
        sizer.Add(self.text, 1, flag=wx.EXPAND|wx.GROW|wx.ALL)
        
        self.panel.SetSizer(sizer)
        self.Layout()
        
        self.UpdateFromDoc()
    
    def TextSetFocus(self,event):
        self.UpdateMenus()
        event.Skip()
    
    def UpdateFromDoc(self):
        super(MainFrame,self).UpdateFromDoc()
        self.search.ChangeValue(self.doc.current_search)
        self._update_colours()
        self._update_visible_text()
    
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
        self.SetAppName(APP_NAME)
        frame=MainFrame(None)
        
        frame.Show()
        
        #for name in sys.argv[1:]:
        #    frame.Load(name)

        return True

app=App(redirect=False)
app.MainLoop()