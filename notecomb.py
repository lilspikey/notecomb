import wx
import wx.stc

import sys

from model import UndoableDocument
from events import Event
from wxdoc import Preferences, DocumentFrame, check_for_modification

PREF_SHOW_LINENUMBERS='SHOW_LINENUMBERS'
PREF_AUTO_SAVE='AUTO_SAVE'
PREF_RECENT_FILES='recent_files'

class PrefDialog(wx.Dialog):
    def __init__(self,parent):
        wx.Dialog.__init__(self,parent,title='Preferences')
        
        sizer=wx.BoxSizer(wx.VERTICAL)
        
        spacer=(5,5)
        
        self.prefs=Preferences()
        
        self.show_line_numbers=self.CreatePrefsCheckBox("Show line numbers", PREF_SHOW_LINENUMBERS, True)
        self.auto_save=self.CreatePrefsCheckBox("Auto-save every five minutes", PREF_AUTO_SAVE, True)
        
        sizer.Add(self.show_line_numbers, 0, wx.ALL, 10)
        sizer.Add(self.auto_save, 0, wx.ALL, 10)
        
        button_sizer=wx.StdDialogButtonSizer()
        
        ok=wx.Button(self,wx.ID_OK,"Done")
        ok.SetDefault()
        
        button_sizer.AddButton(ok)
        
        button_sizer.SetAffirmativeButton(ok)
        
        button_sizer.Realize()
        
        sizer.Add(spacer)
        sizer.Add(spacer)
        sizer.Add(button_sizer, 0, wx.CENTER|wx.ALL, 10)
        sizer.Add(spacer)
        
        self.SetSizer(sizer)
        
        self.Fit()
    
    def CreatePrefsCheckBox(self, label, pref_key, default):
        checkbox=wx.CheckBox(self, -1, label)
        
        checkbox.SetValue(self.prefs.get(pref_key,default))
        
        def update_pref(event):
            self.prefs.set(pref_key, checkbox.GetValue())
            self.prefs.flush()
        
        checkbox.Bind(wx.EVT_CHECKBOX, update_pref)
        return checkbox
#    def UpdatePref(self):
#        self.prefs.set(PREF_SHOW_LINENUMBERS, self.show_line_numbers.GetValue())
#        self.prefs.set(PREF_AUTO_SAVE, self.auto_save.GetValue())    
    
class NoteCombFrame(DocumentFrame):
    __APP_VERSION__='0.2.1 alpha'
    __APP_WEBSITE__='http://www.psychicorigami.com/notecomb/'
    __DOCUMENT_CLASS__=UndoableDocument
    __PREFS_DIALOG__=PrefDialog
    
    _show_line_numbers=False
    
    def __init__(self,parent):
        super(NoteCombFrame,self).__init__(parent,title='NoteComb')
        
        self.panel=wx.Panel(self)
        
        self.search=wx.SearchCtrl(self.panel)
        
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
            num_lines=self.text.GetLineCount()
            width=self.text.TextWidth(wx.stc.STC_STYLE_DEFAULT,'%03d'%num_lines)
            self.text.SetMarginWidth(0,width+5)
        else:
            self.text.SetMarginWidth(0,0)
        self._show_line_numbers=value
    
    @check_for_modification
    def OnClose(self,event):
        self.SaveDefaultSizeAndPosition()
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
    
    def UpdateMenus(self):
        super(NoteCombFrame,self).UpdateMenus()
        
        # check we've initialised fully
        if not getattr(self, 'text', None):
            return
        self.set_show_linenumbers(self._show_line_numbers)
    
    def UpdateFromDoc(self):
        super(NoteCombFrame,self).UpdateFromDoc()
        self.search.ChangeValue(self.doc.current_search)
        self._update_colours()
        self._update_visible_text()
        self.UpdateMenus()
    
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
        self.search.ShowCancelButton(q != '') 
        self.doc.search(q)
        self._update_colours()
        self._update_visible_text()
    
    def OnCopy(self, event):
        if self.text.GetSelectedText():
            self.text.Copy()
    
    def OnPaste(self, event):
        if self.text.CanPaste():
            self.text.Paste()
    
    def OnCut(self, event):
        if self.text.GetSelectedText():
            self.text.Cut()
    
    def OnSelectAll(self, event):
        self.text.SelectAll()
    
    def OnFind(self, event):
        self.search.SetFocus()
        self.search.SelectAll()
    
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
    
    def OnAbout(self,event):
        info=wx.AboutDialogInfo()
        info.SetName(wx.GetApp().GetAppName())
        info.SetVersion(self.__APP_VERSION__)
        info.SetDescription('A program for combing through notes')
        info.AddDeveloper('John Montgomery')
        info.SetCopyright('(C) John Montgomery 2009')
        wx.AboutBox(info)
