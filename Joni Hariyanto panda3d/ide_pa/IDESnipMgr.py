import wx, pickle, IDE
from wx.py.editwindow import EditWindow

NEW_SNIP_NAME='NEW%s'
CARET_PERIOD=200


def restoreEW(e):
    e.EventObject.CaretPeriod=CARET_PERIOD
    e.EventObject.CaretLineVisible=True
    e.Skip()

def stealEWFocusLostEvent(e):
    e.EventObject.CaretPeriod=1
    e.EventObject.CaretLineVisible=False

def openSnippetsManager(newSnip=None):
    IDE.IDE_lastMode=IDE.IDE_getMode()
    IDE.IDE_setMode(IDE.MODE_noInput)
    saveNewSnip=newSnip is not None
    if saveNewSnip:
       i=1
       while NEW_SNIP_NAME%i in IDE.SNIPPETS:
         i+=1
       newSnipName=NEW_SNIP_NAME%i
       IDE.SNIPPETS[newSnipName]=[newSnip,(len(newSnip),)*2]
    frame = wx.Frame(None, -1, 'Code Snippets Manager'+(' - rename your new snippet'*saveNewSnip))
    panel = wx.Panel(frame)

    mgrSizer = wx.BoxSizer(wx.HORIZONTAL)
    namesSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Names : '),wx.VERTICAL)
    renameSizer = wx.BoxSizer(wx.HORIZONTAL)
    contentSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Snippet : '),wx.VERTICAL)

    snippetsNames=sorted(IDE.SNIPPETS.keys())
    snippetsList=wx.ListBox(panel, -1, wx.DefaultPosition, (120, 250), snippetsNames, wx.LB_SINGLE)
    contentText=EditWindow(panel,-1,size=(450,290))
    contentText.TabWidth=2
    contentText.CaretWidth=2
    contentText.CaretPeriod=CARET_PERIOD
    contentText.CaretLineVisible=True
    contentText.CaretLineBackground=((200,200,200))
    # steals edit window's kill focus event, to let the caret shown all the time,
    # not only when it has focus
    contentText.Bind(wx.EVT_KILL_FOCUS,stealEWFocusLostEvent)
    contentText.Bind(wx.EVT_SET_FOCUS,restoreEW)
    contentText.SetFocus()
    newNameText=wx.TextCtrl(panel)
    renameButton=wx.Button(panel,-1,'&Rename',style=wx.BU_EXACTFIT)
    renameButton.Bind(wx.EVT_BUTTON,Functor(renameSnippet,snippetsList,newNameText))
    copyButton=wx.Button(panel,-1,'Duplicate')
    delButton=wx.Button(panel,wx.ID_DELETE)
    copyButton.Bind(wx.EVT_BUTTON,Functor(copySnippet,snippetsList,newNameText))
    delButton.Bind(wx.EVT_BUTTON,Functor(delSnippet,[snippetsList,namesSizer,contentSizer]))
    saveButton=wx.Button(panel,wx.ID_SAVE)
    saveButton.Bind(wx.EVT_BUTTON,Functor(saveSnippetContent,snippetsList,contentText))

    renameSizer.Add(newNameText, 0, wx.ALIGN_CENTER_VERTICAL, 5)
    renameSizer.Add(renameButton, 0, wx.ALIGN_CENTER_VERTICAL, 5)

    namesSizer.Add(snippetsList, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND|wx.ALIGN_CENTER, 5)
    namesSizer.Add(renameSizer, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER, 5)
    namesSizer.Add(wx.StaticLine(panel,-1), 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
    namesSizer.Add(copyButton, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER, 5)
    namesSizer.Add(delButton, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER, 5)

    contentSizer.Add(contentText, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)
    contentSizer.Add(wx.StaticText(panel,-1,'selection and caret position are also saved'), 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER, 5)
    contentSizer.Add(saveButton, 0, wx.LEFT|wx.RIGHT|wx.EXPAND, 5)

    mgrSizer.Add(namesSizer, 0, wx.ALL|wx.EXPAND, 5)
    mgrSizer.Add(contentSizer, 0, wx.RIGHT|wx.TOP|wx.BOTTOM|wx.EXPAND, 5)

    frame.Bind(wx.EVT_CLOSE,Functor(closeSnippetsManager,snippetsList))
    snippetsList.Bind(wx.EVT_LISTBOX,Functor(snippetSelected,snippetsList,newNameText,contentText))
    if snippetsNames:
       if saveNewSnip:
          snippetsList.SetStringSelection(newSnipName)
       else:
          snippetsList.SetSelection(0)
       snippetsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
       if saveNewSnip:
          newNameText.SetFocus()
       else:
          snippetsList.SetFocus()
    else:
       for w in IDE.getWxSizerWidgets(namesSizer)+IDE.getWxSizerWidgets(contentSizer):
           w.Disable()

    panel.SetSizer(mgrSizer)
    mgrSizer.Fit(frame)
    mgrSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    # handles navigational wx events
    if IDE.WIN:
       widgets=IDE.getWxSizerWidgets(mgrSizer)
       widgets.remove(contentText) # let TAB be usable in the EditWindow
       for w in widgets:
           w.Bind(wx.EVT_KEY_DOWN,IDE.handleNavigationalWxEvents)

def closeSnippetsManager(snippetsList,e):
    IDE.IDE_saveSnippetsToDisk()
    # if it's left bound, it would crash on Linux
    snippetsList.Unbind(wx.EVT_LISTBOX)
    IDE.IDE_closeWxInterface(e)

def snippetSelected(snippetsList,newNameText,contentText,e):
    name=snippetsList.GetStringSelection()
    if name:
       snip=IDE.SNIPPETS[name]
       newNameText.SetValue(name)
       contentText.SetText(snip[0])
       contentText.SetSelection(*snip[1])
       contentText.ScrollToLine(0)
       contentText.EmptyUndoBuffer()

def renameSnippet(snippetsList,newNameText,e):
    origName=snippetsList.GetStringSelection()
    newName=newNameText.GetValue()
    if origName==newName: return
    nameValid=newName.strip()
    if not nameValid or newName in IDE.SNIPPETS:
       IDE.IDE_spawnWxErrorDialog('You need to fill its new name' if not nameValid else 'Snippet name already exists')
       newNameText.SetValue(origName)
       newNameText.SetFocus()
    else:
       IDE.SNIPPETS[newName]=IDE.SNIPPETS.pop(origName)
       snippetsList.SetItems(sorted(IDE.SNIPPETS.keys()))
       snippetsList.SetStringSelection(newName)
       snippetsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))

def delSnippet(args,e):
    IDE.IDE_spawnWxModal( IDE.IDE_spawnWxYesNoDialog,(
        'Are you sure to remove this snippet ?', doDelSnippet,args)
        )

def doDelSnippet(args):
    if not args or len(IDE.SNIPPETS)==0: return
    snippetsList,namesSizer,contentSizer=args
    idx=snippetsList.GetSelection()
    IDE.SNIPPETS.pop(snippetsList.GetStringSelection())
    if IDE.SNIPPETS:
       snippetsList.SetItems(sorted(IDE.SNIPPETS.keys()))
       snippetsList.SetSelection(min(len(IDE.SNIPPETS)-1,idx))
       snippetsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
       snippetsList.SetFocus()
    else:
       snippetsList.Clear()
       for w in IDE.getWxSizerWidgets(namesSizer)+IDE.getWxSizerWidgets(contentSizer):
           w.Disable()

def copySnippet(snippetsList,newNameText,e):
    origName=snippetsList.GetStringSelection()
    i=1
    while origName+str(i) in IDE.SNIPPETS:
      i+=1
    dupName=origName+str(i)
    IDE.SNIPPETS[dupName]=IDE.SNIPPETS[origName]
    snippetsList.SetItems(sorted(IDE.SNIPPETS.keys()))
    snippetsList.SetStringSelection(dupName)
    snippetsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    newNameText.SetFocus()
    newNameText.SetInsertionPointEnd()

def saveSnippetContent(snippetsList,contentText,e):
    IDE.SNIPPETS[snippetsList.GetStringSelection()]=[contentText.GetText(),contentText.GetSelection()]
