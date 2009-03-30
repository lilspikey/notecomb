import wx
import wx.stc

import sys
try:
    import cPickle as pickle
except ImportError:
    import pickle

from model import UndoableDocument
from events import Event

APP_NAME='Observertron'

class Singleton(object):

    _instances = {}

    def __new__(cls, *args, **kw):
        try:
            instance = Singleton._instances[cls]
        except KeyError:
            instance = super(Singleton, cls).__new__(cls, *args, **kw)
            Singleton._instances[cls] = instance
        return instance

class Preferences(Singleton):
    
    def __init__(self):
        if 'cfg' not in vars(self):
            self.cfg=wx.ConfigBase.Get()
            self.changed=Event()
    
    def get(self, key, defaultValue):
        value=self.cfg.Read(key, '')
        try:
            return pickle.loads(str(value))
        except:
            return defaultValue
    
    def set(self, key, value):
        result=self.cfg.Write(key, pickle.dumps(value))
        self.changed(key, value)
        return result
    
    def flush(self):
        self.cfg.Flush()

PREF_SHOW_LINENUMBERS='SHOW_LINENUMBERS'
PREF_AUTO_SAVE='AUTO_SAVE'
PREF_RECENT_FILES='recent_files'

class PrefDialog(wx.Dialog):
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,title='Preferences')
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        spacer=(5,5)
        
        self.prefs=Preferences()
        
        self.show_line_numbers=wx.CheckBox(self, -1, "Show line numbers")
        self.auto_save=wx.CheckBox(self, -1, "Auto-save every five minutes")
        
        self.show_line_numbers.SetValue(self.prefs.get(PREF_SHOW_LINENUMBERS,True))
        self.auto_save.SetValue(self.prefs.get(PREF_AUTO_SAVE,True))
        
        sizer.Add(self.show_line_numbers, 0, wx.ALL, 10)
        sizer.Add(self.auto_save, 0, wx.ALL, 10)
        
        button_sizer=wx.StdDialogButtonSizer()
        
        cancel=wx.Button(self,wx.ID_CANCEL,"Cancel")
        ok=wx.Button(self,wx.ID_OK,"Ok")
        ok.SetDefault()
        
        button_sizer.AddButton(cancel)
        button_sizer.AddButton(ok)
        
        button_sizer.SetAffirmativeButton(ok)
        button_sizer.SetCancelButton(cancel)
        
        button_sizer.Realize()
        
        sizer.Add(spacer)
        sizer.Add(spacer)
        sizer.Add(button_sizer, 0, wx.CENTER|wx.ALL, 10)
        sizer.Add(spacer)
        
        self.SetSizer(sizer)
        
        self.Fit()
    
    def UpdatePrefs(self):
        self.prefs.set(PREF_SHOW_LINENUMBERS, self.show_line_numbers.GetValue())
        self.prefs.set(PREF_AUTO_SAVE, self.auto_save.GetValue())

def check_for_modification(fn):
    def _decorated(self,event):
        if self.doc.is_modified:
            dialog=wx.MessageDialog(self,"Your changes will be lost if you don't save them.","Do you want to save your changes?",wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            dialog.Center()
            result=dialog.ShowModal()
            dialog.Destroy()
            if result != wx.ID_CANCEL:
                if result == wx.ID_YES:
                    # save changes
                    self.OnSave(event)
                    # cancelled save, so don't allow the event
                    if self.doc.is_modified:
                        return
            else:
                return
        return fn(self,event)
    return _decorated

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
        
        self.file_open_recent=wx.Menu()
        self.file_menu.AppendSubMenu(self.file_open_recent,"Open Recent")
        self.file_clear_menu=self.AddMenuItem(self.file_open_recent, "Clear Menu", self.OnClearMenu, -1)
        
        self.file_menu.AppendSeparator()
        
        self.file_save=self.AddMenuItem(self.file_menu, "Save\tCtrl-S", self.OnSave, -1)
        self.AddMenuItem(self.file_menu, "Save As...\tShift-Ctrl-S", self.OnSaveAs, -1)
        self.file_menu.AppendSeparator()
        
        self.AddMenuItem(self.file_menu, "Preferences...\tCtrl-K", self.OnPreferences, wx.ID_PREFERENCES)
        self.file_menu.AppendSeparator()
        
        self.AddMenuItem(self.file_menu, "Quit %s\tCtrl-Q" % APP_NAME, self.OnQuit, wx.ID_EXIT)
        
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        self.edit_menu=wx.Menu()
        self.menubar.Append(self.edit_menu, "&Edit")
        
        self.edit_undo=self.AddMenuItem(self.edit_menu, "Undo\tCtrl-Z", self.OnUndo, wx.ID_UNDO)
        self.edit_redo=self.AddMenuItem(self.edit_menu, "Redo\tShift-Ctrl-Z", self.OnRedo, wx.ID_REDO)
        
        self.SetMenuBar(self.menubar)
        
        self.prefs=Preferences()
        
        self.UpdateMenus()
        self.update_recent_files_menu()
    
    def AddMenuItem(self, menu, label, handler, id):
        menu_item=menu.Append(id,label)
        self.Bind(wx.EVT_MENU, handler, menu_item)
        return menu_item
    
    def UpdateFromDoc(self):
        self.UpdateMenus()
    
    def UpdateMenus(self):
        title=self.doc.filename or '<untitled>'
        if self.doc.is_modified:
            title += '*'
        self.SetTitle(title)
        self.file_save.Enable(not self.doc.is_saved)
        self.edit_undo.Enable(self.doc.can_undo())
        self.edit_redo.Enable(self.doc.can_redo())
    
    @check_for_modification
    def OnNew(self,event):
        self.doc=self.__DOCUMENT_CLASS__()
        self.UpdateFromDoc()
    
    @check_for_modification
    def OnOpen(self,event):
        dialog=wx.FileDialog(self,"Open File",'','','Obs File (*.obs)|*.obs|All File|*.*', wx.FD_OPEN)
        dialog.Centre()
        filename=None
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
        dialog.Destroy()
        
        if filename:
            self.Load(filename)
    
    def Load(self,filename):
        self.doc.open(filename)
        self._update_recent_files(filename)
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
            self._update_recent_files(filename)
            self.UpdateMenus()
    
    def OnPreferences(self,event):
        dialog=PrefDialog(self)
        dialog.Center()
        if dialog.ShowModal() == wx.ID_OK:
            dialog.UpdatePrefs()
        dialog.Destroy()
    
    def update_recent_files_menu(self):
        recent_files=self.prefs.get('recent_files',[])
        self.file_clear_menu.Enable(len(recent_files)>0)
        
        # remove all, but last item
        while self.file_open_recent.GetMenuItemCount() > 1:
            menu_items=self.file_open_recent.GetMenuItems()
            self.file_open_recent.RemoveItem(menu_items[0])
        
        if len(recent_files) > 0:
            self.file_open_recent.PrependSeparator()
            for file in reversed(recent_files):
                menu_item=self.file_open_recent.Prepend(-1,file)
                self.BindRecentFile(menu_item, file)
    
    def BindRecentFile(self, menu_item, file):
        self.Bind(wx.EVT_MENU, lambda event: self.OpenRecentFile(file), menu_item)
    
    @check_for_modification
    def OpenRecentFile(self, file):
        self.Load(file)
    
    def _update_recent_files(self, file_name):
        recent_files=self.prefs.get('recent_files',[])
        if file_name in recent_files:
            recent_files.remove(file_name)
        recent_files.insert(0, file_name)
        if len(recent_files) > 8:
            recent_files=recent_files[:8]
        self.prefs.set('recent_files', recent_files)

    def OnClearMenu(self,event):
        self.prefs.set('recent_files', [])
    
    @check_for_modification
    def OnQuit(self,event):
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
        
        self.prefs.changed += self.prefs_changed
        self.set_show_linenumbers(self.prefs.get(PREF_SHOW_LINENUMBERS,True))
        
        self.timer=wx.Timer(self,-1)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(5*60*1000)
    
    def prefs_changed(self, key, value):
        if key == PREF_SHOW_LINENUMBERS:
            self.set_show_linenumbers(value)
        elif key == PREF_RECENT_FILES:
            self.update_recent_files_menu()
    
    def set_show_linenumbers(self, value):
        if value:
            self.text.SetMarginWidth(0,32)
        else:
            self.text.SetMarginWidth(0,0)
    
    @check_for_modification
    def OnQuit(self,event):
        self.timer.Stop()
        self.Destroy()
    
    def OnTimer(self, event):
        if self.prefs.get(PREF_AUTO_SAVE,True):
            if self.doc.is_modified:
                self.doc.save()
                self.UpdateMenus()
    
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
        
        files=sys.argv[1:]
        if not files:
            files=[None]
        
        for file in files:
            frame=MainFrame(None)
            frame.Show()
            if file:
                frame.Load(file)
        
        return True

app=App(redirect=False)
app.MainLoop()