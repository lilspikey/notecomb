import wx

import sys
import tempfile
import webbrowser
try:
    import cPickle as pickle
except ImportError:
    import pickle

from events import Event
from pipe import Pipe

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

def check_for_modification(fn):
    def _decorated(self,event):
        if self.doc.is_modified:
            self.Raise()
            dialog=wx.MessageDialog(self,"Your changes will be lost if you don't save them.","Do you want to save your changes?",wx.YES_NO | wx.CANCEL | wx.ICON_QUESTION)
            dialog.CenterOnParent()
            result=dialog.ShowModal()
            dialog.Destroy()
            if result != wx.ID_CANCEL:
                if result == wx.ID_YES:
                    # save changes
                    self.OnSave(event)
                    # cancelled save, so don't allow the event
                    if self.doc.is_modified:
                        return wx.ID_CANCEL
            else:
                return wx.ID_CANCEL
        return fn(self,event)
    return _decorated

class DocumentFrame(wx.Frame):
    '''
    class to hook up standard menus etc
    '''

    __DOCUMENT_CLASS__=None
    __PREFS_DIALOG__=None

    def __init__(self,*args,**kw):
        super(DocumentFrame,self).__init__(*args,**kw)
        
        self.is_closing=False
        
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
        self.AddMenuItem(self.file_menu, "Close Window\tCtrl-W", self.OnClose, -1)

        self.file_save=self.AddMenuItem(self.file_menu, "Save\tCtrl-S", self.OnSave, -1)
        self.AddMenuItem(self.file_menu, "Save As...\tShift-Ctrl-S", self.OnSaveAs, -1)
        self.file_menu.AppendSeparator()

        self.AddMenuItem(self.file_menu, "Preferences...\tCtrl-K", self.OnPreferences, wx.ID_PREFERENCES)
        self.file_menu.AppendSeparator()

        self.AddMenuItem(self.file_menu, "Quit %s\tCtrl-Q" % wx.GetApp().GetAppName(), self.OnQuit, wx.ID_EXIT)

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnDestroyed)
        self.Bind(wx.EVT_ACTIVATE, self.OnActivate)

        self.edit_menu=wx.Menu()
        self.menubar.Append(self.edit_menu, "&Edit")

        self.edit_undo=self.AddMenuItem(self.edit_menu, "Undo\tCtrl-Z", self.OnUndo, wx.ID_UNDO)
        self.edit_redo=self.AddMenuItem(self.edit_menu, "Redo\tShift-Ctrl-Z", self.OnRedo, wx.ID_REDO)
        self.edit_menu.AppendSeparator()
        self.edit_cut=self.AddMenuItem(self.edit_menu, "Cut\tCtrl-X", self.OnCut, wx.ID_CUT)
        self.edit_copy=self.AddMenuItem(self.edit_menu, "Copy\tCtrl-C", self.OnCopy, wx.ID_COPY)
        self.edit_paste=self.AddMenuItem(self.edit_menu, "Paste\tCtrl-V", self.OnPaste, wx.ID_PASTE)
        self.edit_menu.AppendSeparator()
        self.edit_select_all=self.AddMenuItem(self.edit_menu, "Select All\tCtrl-A", self.OnSelectAll, -1)
        self.edit_menu.AppendSeparator()
        self.edit_find=self.AddMenuItem(self.edit_menu, "Find\tCtrl-F", self.OnFind, -1)

        self.help_menu=wx.Menu()
        self.menubar.Append(self.help_menu, "&Help")

        self.AddMenuItem(self.help_menu, "About %s" % wx.GetApp().GetAppName(), self.OnAbout, wx.ID_ABOUT)
        self.edit_menu.AppendSeparator()
        self.AddMenuItem(self.help_menu, "Visit %s" % self.__APP_WEBSITE__, self.OnWebsite, -1)

        self.SetMenuBar(self.menubar)

        self.prefs=Preferences()

        self.UpdateMenus()
        self.update_recent_files_menu()
        
        self.SetWindowsIcon()
    
    def SetWindowsIcon(self):
        if sys.platform == 'win32':
            exeName = sys.executable
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ICO)
            self.SetIcon(icon)

    def GetDocFilename(self):
        return self.doc.filename
    
    def IsEmpty(self):
        return self.doc.is_empty
    
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

    def OnNew(self,event):
        wx.GetApp().OpenFile(None)

    def OnOpen(self,event):
        dialog=wx.FileDialog(self,"Open File",'','','Obs File (*.obs)|*.obs|All File|*.*', wx.FD_OPEN)
        dialog.Centre()
        filename=None
        if dialog.ShowModal() == wx.ID_OK:
            filename = dialog.GetPath()
        dialog.Destroy()

        if filename:
            wx.GetApp().OpenFile(filename)

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
        wx.GetApp().ShowPreferences()
    
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

    def OpenRecentFile(self, file):
        wx.GetApp().OpenFile(file)

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

    def OnQuit(self,event):
        wx.GetApp().Quit()

    @check_for_modification
    def OnClose(self, event):
        self.Destroy()

    def OnDestroyed(self, event):
        wx.GetApp().FrameClosed(self)
    
    def OnActivate(self, event):
        if event.GetActive():
            wx.GetApp().FrameRaised(self)
        event.Skip() # for mac bug

    def OnUndo(self,event):
        if self.doc.can_undo():
            self.doc.undo()
            self.UpdateFromDoc()

    def OnRedo(self,event):
        if self.doc.can_redo():
            self.doc.redo()
            self.UpdateFromDoc()
    
    def OnWebsite(self,event):
        webbrowser.open(self.__APP_WEBSITE__)

class DocApp(wx.App):

    __APP_NAME__='wxdocapp'
    __DOC_FRAME__=DocumentFrame
    
    def OnInit(self):
        self.SetAppName(self.__APP_NAME__)
        
        self._pipe=Pipe(self.GetAppName() + '-' + wx.GetUserId())
        
        self._frames=[]

        files=sys.argv[1:]
        self.OpenFiles(files)
        
        self.prefs_dialog=self.__DOC_FRAME__.__PREFS_DIALOG__(None)
        self.prefs_dialog.Center()
        
        return True
    
    def OnExit(self):
        del self._singleInstanceChecker
    
    def ShowPreferences(self):
        if not self.prefs_dialog.IsShown():
            self.prefs_dialog.Show()
    
    def OpenFiles(self, files):
        self._singleInstanceChecker = wx.SingleInstanceChecker(self.GetAppName() + '-' + wx.GetUserId(), tempfile.gettempdir())
        if self._singleInstanceChecker.IsAnotherRunning():
            self._pipe.write(files)
        else:
            if not files:
                files=[None]

            for filename in files:
                self.OpenFile(filename)
            
            self.timer=wx.Timer(self,-1)
            self.Bind(wx.EVT_TIMER, self.CheckForOpenFiles, self.timer)
            self.timer.Start(1000)
    
    def CheckForOpenFiles(self, event):
        files=self._pipe.read()
        if files:
            for filename in files:
                self.OpenFile(filename)
    
    def OpenFile(self, filename):
        # see if we already have a window
        # open for the filename passed in
        empty_frame=None
        if filename:
            for frame in self._frames:
                if frame.GetDocFilename() == filename:
                    frame.Raise()
                    return
        
        # otherwise see if there's an empty frame we can use
        empty_frames=[frame for frame in self._frames if frame.IsEmpty()]
        if empty_frames:
            empty_frame=empty_frames[0]
    
        if not empty_frame:
            frame=self.__DOC_FRAME__(None)
            self._frames.append(frame)
        else:
            frame=empty_frame
        frame.Show()

        if filename:
            frame.Load(filename)
        
        frame.Raise()

    def MacOpenFile(self, filename):
        self.OpenFile(filename)
    
    def FrameClosed(self, frame):
        if frame in self._frames:
            self._frames.remove(frame)
            # see if this is the last
            # frame being closed and if so
            # destroy the prefs dialog
            if not self._frames:
                self.prefs_dialog.Destroy()
    
    def FrameRaised(self, frame):
        # add frame to front of list
        if frame in self._frames:
            self._frames.remove(frame)
            self._frames.insert(0, frame)
    
    def Quit(self):
        # try to close all windows
        
        # copy list of frames, so as to avoid
        # problems as windows get raised etc
        frames=list(self._frames)
        
        for frame in frames:
            res=frame.OnClose(None)
            if res == wx.ID_CANCEL:
                break # cancel pressed
        