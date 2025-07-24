import sys, wx
if not 'IDEmini' in sys.modules:
   wxApp = wx.App(redirect=False)
   wx.MessageDialog(None,
      message='You should not run this module directly.\nPlease run "IDE_STARTER.pyw" instead.',
      caption='USER ERROR', style=wx.ICON_ERROR).ShowModal()
   sys.exit()

import IDEmini
from IDEmini import *
from IDESceneGraphBrowser import *
from IDENodeProps import *
import IDEPolyButton
import IDEPreferences
import IDESnipMgr
import builtins
M = sys.modules[__name__]


def startPStatsServer():
    if WIN:
       PStatsPath = glob(joinPaths(directModulesDir,os.pardir,'bin','pstats.exe'))
    else:
       PStatsPath = glob(joinPaths(os.path.dirname(sys.executable),'pstats'))
    M.PStatsEnabled = PStatsPath and os.path.exists(PStatsPath[0])
    if PStatsEnabled:
       M.PStatsPID = subprocess.Popen(PStatsPath[0]).pid

def connectToPStatsServer():
    msg = createMsg('Connecting to PStats server.....',bg=(0,1,0,.85))
    putMsg(msg,'',.5)
    renderFrame(2)
    PStatClient.connect()
    if PStatClient.isConnected():
       IDE_setMessage('Connected to PStats server.')

def killPStatsServer():
    if PStatsEnabled:
       if WIN:
          try:
             subprocess.Popen('taskkill /f /IM pstats.exe')
          except:
             pass
       elif hasattr(os,'kill'):
          try:
              os.kill(PStatsPID,1)
          except:
              pass

def IDE_enablePStats():
    if PStatClient.isConnected():
       msg = createMsg('Already connected to PStats server.',bg=(0,1,0,.85))
       putMsg(msg,'',1)
       return
    connectToPStatsServer()
    if not PStatClient.isConnected():
#        killPStatsServer()
       startPStatsServer()
       taskMgr.doMethodLater(1,connectToPStatsServer,IDE_tasksName+'connectToPStatsServer',extraArgs=[])

def IDE_gotoDir(loc):
    if WIN:
       os.startfile(loc)
    elif MAC:
       subprocess.Popen('open "%s"'%loc, shell=True)
    elif LIN:
       subprocess.Popen('xdg-open "%s"'%loc, shell=True)
    else:
       msg=createMsg(NOT_YET,bg=(1,0,0,.85))
       putMsg(msg,NOT_YET,2)

def createTooltip(text,align=TextProperties.ACenter,alpha=None):
    tt = createMsg(text, pad=(.3,.3,.3,.1), bg=(1,1,1,1), align=align)
    tt.setName('tool tip')
    if alpha is not None:
       tt.setTexture(IDE_gradingAlphaTexV1 if alpha else IDE_gradingAlphaTexV0)
    tt.node().clearFrame()
    return tt

def createMsg(errText,bg=(1, 0, 0, .85),fg=(0, 0, 0, 1),pad=(1,1,1,1),align=TextProperties.ACenter,alpha=1):
    text = TextNode('message text')
    text.setText(errText)
    text.setAlign(align)
    #~ text.setFont(IDE_FONT_transmetals)
    text.setFont(IDE_FONT_monospace)
    text.setGlyphScale(.85)
    text.setTextColor(*fg)
#     text.setShadowColor(*fg)
    text.setFrameColor(1, 1, 1, 1)
    text.setFrameAsMargin(*pad)
    bg=bg[:3]+(1,)
    text.setCardColor(*bg)
    text.setCardAsMargin(*pad)
    textNP = NodePath(text)
    textNP.setTransparency(TransparencyAttrib.MAlpha)
    if alpha:
       textNP.setTexture(IDE_gradingAlphaTexV1_2)
    return textNP

def putMsg(msg,ivalname,wait=1.5,stat=False):
    for c in asList(IDE_root.findAllMatches('**/message text')):
        c.removeNode()
    msg.reparentTo(IDE_overlayParent)
    msg.setScale(IDE_msgScale)
    msg.setBin('gaugeBin',1)
    if stat:
       IDE_setMessage(msg.node().getText())
    if wait>0:
       Sequence(
          Wait(wait),
          Func(msg.removeNode),
       name=IDE_ivalsName+ivalname).start()

def IDE_selectFiles2Save(args,ce):
    filesList,save=args
    for i in range(filesList.Count):
        filesList.Check(i,save)

def IDE_file2saveSelected(docs,ce):
    idx=ce.GetEventObject().GetSelection()
    if idx>-1:
       docs[idx].setDocActive()

def IDE_saveFilesProcessWxChar(ce):
    #~ ce.Skip()
    KC=ce.GetKeyCode()
    EO=ce.GetEventObject()
    if KC==wx.WXK_ESCAPE:
       IDE_closeWxInterface(EO.GetGrandParent())
    # serves the navigational key events, which relies on wx eventloop,
    # which is not enabled on Windows, since it steals Panda's keystrokes
    # (IT'S WORSE THAN LOSING WX NAVIGATIONAL EVENTS)
    else:#elif WIN
       if KC==wx.WXK_TAB:
          NKE=wx.NavigationKeyEvent
          EO.Navigate(NKE.IsBackward if ce.m_shiftDown else NKE.IsForward)
       elif type(EO)==wx.Button and KC in (wx.WXK_NUMPAD_ENTER,wx.WXK_RETURN,wx.WXK_SPACE):
          EO.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED))

def IDE_saveNextNewFile():
    IDE_newWorthyFiles.pop(0)
    if IDE_newWorthyFiles:
       IDE_newWorthyFiles[0].setDocActive()
       if not WIN:
          renderFrame(2)
       IDE_DO.acceptOnce(IDE_EVT_fileSaved,IDE_saveNextNewFile)
       IDE_doc.saveFile()
    else: # all new files have been saved, it's time to exit
       IDE_cleanupAndExit(exit=True)

def IDE_exit():
    if IDE_doc:
       if not IDE_doc.callTipParent.isHidden():
          IDE_doc.hideCallTip()
          return
    if IDE_isInMode(MODE_exiting): return
    IDE_removeAnyMenuNcallTip()
    IDE_CC_cancel()
    IDE_hideSGB()
    IDE_cancelResolutionChange()
    M.IDE_lastMode = IDE_getMode()
    IDE_setMode(MODE_exiting)
    M.IDE_exitStatus = 0
    notSavedFiles = []
    newFiles = []
    for d in IDE_documents:
        if d.isChanged:
           if d.FullPath:
              notSavedFiles.append(d)
           else:
              newFiles.append(d)
    if notSavedFiles or newFiles:
       IDE_warnUnsavedFiles(notSavedFiles,newFiles)
    else:
       IDE_openYesNoDialog('Are you sure to E.X.I.T  ?', IDE_cleanupAndExit)

def IDE_warnUnsavedFiles(notSavedFiles,newFiles):
    notSavedFilesPath=[d.FullPath for d in notSavedFiles]+[d.FileName for d in newFiles]
    
    saveFilesWindow = wx.Frame(None,-1,'There are unsaved changes in file(s)')
    saveFilesScreen = wx.Panel(saveFilesWindow)

    text = wx.StaticText(saveFilesScreen,-1,'Some files have been changed and not yet saved :')
    editedFilesList = wx.CheckListBox(saveFilesScreen, size=(415,200), choices=notSavedFilesPath)
    editedFilesList.Bind(wx.EVT_LISTBOX,Functor(IDE_file2saveSelected,notSavedFiles+newFiles))
    editedFilesList.SetToolTipString('check the files you want to save')
    IDE_selectFiles2Save([editedFilesList,1],0)

    selAllFilesBtn = wx.Button(saveFilesScreen, -1, 'Check All')
    selAllFilesBtn.Bind(wx.EVT_BUTTON,Functor(IDE_selectFiles2Save,[editedFilesList,1]))
    deselAllFilesBtn = wx.Button(saveFilesScreen, -1, 'Uncheck All')
    deselAllFilesBtn.Bind(wx.EVT_BUTTON,Functor(IDE_selectFiles2Save,[editedFilesList,0]))

    SFsizer = wx.BoxSizer(wx.HORIZONTAL)
    SFsizer.Add(selAllFilesBtn, 0, wx.RIGHT|wx.ALIGN_CENTER, 5)
    SFsizer.Add(deselAllFilesBtn, 0, wx.LEFT|wx.ALIGN_CENTER, 5)

    def cancelExit(e):
        IDE_closeWxInterface(saveFilesWindow)

    def dontSaveAndExit(e):
        numNotSaved=len(notSavedFiles+newFiles)
        IDE_closeWxInterface(saveFilesWindow,restoreMode=False)
        IDE_openYesNoDialog('Changes in %s file%s will NOT be saved.\nAre you sure to E.X.I.T  ?'%(numNotSaved,'s'*(numNotSaved>1)), IDE_cleanupAndExit)

    def saveAndExit(e):
        numNotSavedFiles=len(notSavedFiles)
        for i in range(numNotSavedFiles):
            if editedFilesList.IsChecked(i):
               if notSavedFiles[i].saveFile():# unable to be saved
                  IDE_closeWxInterface(saveFilesWindow,restoreMode=False)
                  return
               renderFrame(2)
        M.IDE_newWorthyFiles=[]
        for i in range(numNotSavedFiles,numNotSavedFiles+len(newFiles)):
            if editedFilesList.IsChecked(i):
               IDE_newWorthyFiles.append(newFiles[i-numNotSavedFiles])
        IDE_closeWxInterface(saveFilesWindow,restoreMode=False)
        if IDE_newWorthyFiles:
           IDE_newWorthyFiles[0].setDocActive()
           if LIN:
              if not IDE_isScenePaused:
                 IDE_toggleSceneActive()
              renderFrame(2)
           if len(IDE_newWorthyFiles)>1:
              IDE_DO.acceptOnce(IDE_EVT_fileSaved,IDE_saveNextNewFile)
           IDE_doc.saveFile()
        else:
           IDE_cleanupAndExit(exit=True)

    saveNotEditedFilesBtn = wx.Button(saveFilesScreen, -1, 'Save and Exit')
    saveNotEditedFilesBtn.Bind(wx.EVT_BUTTON, saveAndExit)
    saveNotEditedFilesBtn.SetFont(wxBigFont)
    saveNotEditedFilesBtn.SetFocus()

    dontSaveBtn = wx.Button(saveFilesScreen, -1, "Don't Save and Exit")
    dontSaveBtn.Bind(wx.EVT_BUTTON, dontSaveAndExit)

    cancelBtn = wx.Button(saveFilesScreen, wx.ID_CANCEL)
    cancelBtn.Bind(wx.EVT_BUTTON, cancelExit)

    Vsizer = wx.BoxSizer(wx.VERTICAL)
    Vsizer.Add(text, 0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT, 5)
    Vsizer.Add(editedFilesList, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)
    Vsizer.Add(SFsizer, 0, wx.ALIGN_CENTER_HORIZONTAL, 5)
    Vsizer.Add(wx.StaticLine(saveFilesScreen), 0, wx.ALL|wx.EXPAND, 5)
    Vsizer.Add(saveNotEditedFilesBtn, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5)
    Vsizer.Add(dontSaveBtn, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5)
    Vsizer.Add(cancelBtn, 0, wx.BOTTOM|wx.ALIGN_CENTER_HORIZONTAL, 5)

    saveFilesWindow.Bind(wx.EVT_CLOSE,cancelExit)
    saveFilesScreen.SetSizer(Vsizer)
    Vsizer.Fit(saveFilesWindow)
    Vsizer.SetSizeHints(saveFilesWindow)
    saveFilesWindow.Center()
    saveFilesWindow.Show()
    # let all panel's children receive ESCAPE to cancel
    for c in saveFilesScreen.GetChildren():
        c.Bind(wx.EVT_CHAR,IDE_saveFilesProcessWxChar)

def IDE_openOkDialog(msg,confirmFunc,args=None,darken=True,
                     colorScale=Vec4(1),msgColor=Vec4(0,0,0,1)):
    IDE_openYesNoCancelDialog(msg,confirmFunc,args,dialogType=2,darken=darken,
      colorScale=colorScale,msgColor=msgColor)

def IDE_openYesNoDialog(msg,confirmFunc,args=None,darken=True,
                        colorScale=Vec4(1),msgColor=Vec4(0,0,0,1)):
    IDE_openYesNoCancelDialog(msg,confirmFunc,args,dialogType=1,darken=darken,
      colorScale=colorScale,msgColor=msgColor)

def adjustUV(card,text,inc):
    scale=inc+card.getTexScale(TextureStage.getDefault())[1]/(text.getBounds().getCenter()[2])
    card.setTexScale(TextureStage.getDefault(),1,text.getBounds().getCenter()[2]*scale)
    print('V scale :',scale, file=IDE_DEV)

def IDE_openYesNoCancelDialog(msg,confirmFunc,args=None,dialogType=0,darken=True,
                              colorScale=Vec4(1), msgColor=Vec4(0,0,0,1)):
    global IDE_dialog
    ync = loader.loadModel('models/yncDialog/ync')
    headlight = ync.find('**/rigHeadlightOn')
    Sequence( headlight.colorScaleInterval(.25,Vec4(1,1,1,0)),
              Wait(.2),
              headlight.colorScaleInterval(.2,Vec4(1,1,1,1)),
              name=IDE_ivalsName+'dialog headlight blink'
            ).loop()
    b3 = ync.getTightBounds()
    text = OnscreenText(parent=ync,text=msg,font=IDE_FONT_monospace,scale=IDE_dialogMsgScale,fg=msgColor)
    textB3 = text.getTightBounds()
    textDim = (textB3[1]-textB3[0])
    text.setZ(textDim[2]+IDE_dialogMsgPad*IDE_FONT_monospace.getLineHeight()*IDE_dialogMsgScale)
    bx = max((b3[1]-b3[0])[0]*.485,textDim[0]*.5+.05)/ync.getSx()
    CM = CardMaker('')
    CM.setFrame(-bx,bx,0,2*text.getBounds().getCenter()[2])
    dialogBG=loader.loadTexture('models/yncDialog/dialogBG.png')
    cardParent=ync.attachNewNode('textBG',sort=-1)
    card = cardParent.attachNewNode(CM.generate())
    card.setTexScale(TextureStage.getDefault(),1,text.getBounds().getCenter()[2]*IDE_dialogUVscale)
    card.setTexture(dialogBG)
    card.setTexture(TextureStage('alpha'),IDE_gradingAlphaTexV0_1)
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setColorScale(colorScale)
    text.wrtReparentTo(cardParent)
    cardParent.setP(-90)

    args=[] if args is None else [args]
    if dialogType==2: # ok
       buttons = [ IDEPolyButton.myButton(ync, 'n', ('hover','pressed'),
          hitKey=('o','escape'), command=Functor(IDE_closeConfDialog,confirmFunc,args),
          enable=0, stayAlive=0, text='Ok',font=IDE_FONT_transmetals,
          textScale=.07,textPos=(0,-.15)) ]
       ync.find('**/y').hide()
       ync.find('**/c').hide()
    else:
       buttons = [ IDEPolyButton.myButton(ync, 'y', ('hover','pressed'), hitKey='y',
          command=Functor(IDE_closeConfDialog,confirmFunc,args+[True]),
          enable=0, stayAlive=0, text='Yes',font=IDE_FONT_transmetals) ]
       if dialogType==0: # yes no cancel
          buttons += [
             IDEPolyButton.myButton(ync, 'n', ('hover','pressed'), hitKey='n',
                command=Functor(IDE_closeConfDialog,confirmFunc,args+[False]),
                enable=0, stayAlive=0, text='No',font=IDE_FONT_transmetals,
                textScale=.07,textPos=(0,-.15)),
             # sets the CANCEL button as default one, so pack it in a sequence
             [IDEPolyButton.myButton(ync, 'c', ('hover','pressed'), hitKey=('c','escape'),
                command=Functor(IDE_closeConfDialog,confirmFunc,args+[None]),
                enable=0, stayAlive=0, text='Cancel',font=IDE_FONT_transmetals)
                ],
          ]
          buttons[2][0].text.setSx(-1)
       elif dialogType==1: # yes no
          buttons += [
             # sets the NO button as default one, so pack it in a sequence
             [IDEPolyButton.myButton(ync, 'c', ('hover','pressed'), hitKey=('n','escape'),
                command=Functor(IDE_closeConfDialog,confirmFunc,args+[False]),
                enable=0, stayAlive=0, text='No',font=IDE_FONT_transmetals)
                ],
          ]
          buttons[1][0].text.setSx(-1)
          ync.find('**/n').removeNode()


    IDE_dialog = IDEPolyButton.myDialog(
        root = ync,
        pos = (0,0,-1), scale=IDE_dialogScale,
        buttons=buttons,
        )

    light = ync.find('**/rigLightOn')
    light.hide()
    leftBut = ync.find('**/y')
    leftBut.setR(leftBut,-90)
    rightBut = ync.find('**/c')
    rightBut.setR(rightBut,-90)

    veilFS = base.getAspectRatio()*3
    veilCard = DirectFrame(parent=ync, state=DGG.NORMAL, sortOrder=-10,
      frameSize=(-veilFS,veilFS)*2, frameColor=Vec4(1), suppressMouse=0)
    veilCard.setName('veil')
    veilCard.setPythonTag('destroy',veilCard.destroy)
    veilCard.setTransparency(TransparencyAttrib.MAlpha)
    if not darken:
       veilCard.hide()
    ync.prepareScene(base.win.getGsg())
    ync.node().setBounds(OmniBoundingVolume())
    ync.node().setFinal(1)
    renderFrame()
    ync.node().setFinal(0)
    ync.node().clearBounds()
    ync.reparentTo(IDE_overlayParent)
    ync.setZ(IDE_2Droot,-1.2)
    ync.setBin('gaugeBin',1)

    minb,maxb=IDE_dialog.root.getTightBounds()
    dim=maxb-minb
    IDE_dialog.height=IDE_root.getRelativeVector(IDE_dialog.root.getParent(),Vec3(0,0,dim[2]))[2]
    IDE_dialog.uvFlow = LerpFunc(
       lambda v:card.setTexOffset(TextureStage.getDefault(),0,v), duration=.4)
    IDE_dialog.uvFlow.loop()

    openDialogIval = Sequence(
        Parallel(
           veilCard.colorScaleInterval(.4,Vec4(0,0,0,.65),Vec4(0)),
           # slides it on screen
           Sequence(
              ync.posInterval(.2,Point3(0),blendType='easeOut'),
              Wait(.05),
              Parallel(
                 cardParent.hprInterval(.15,Vec3(0),blendType='easeIn'),
                 leftBut.hprInterval(.15,Vec3(0),blendType='easeInOut'),
                 rightBut.hprInterval(.15,Vec3(0,0,-180),blendType='easeInOut'),
                 ),
              ),
           ),
        # enables dialog buttons' events and shortcut keys
        Func(IDE_dialog.enableDialogButtons),
        Func(IDE_dialog.setDialogKeysActive),
        # starts collision task
        Func(IDEPolyButton.start),
        Wait(.15),
        Func(light.hide if dialogType==2 else light.show),
        name=IDE_ivalsName+'open dialog'
    )
    openDialogIval.start()
    IDE_dialog.ival=openDialogIval
    IDE_textCursorIval.pause()

#     IDE_DO.accept(IDE_getMode()+MODE_SUFFIX+'wheel_up',adjustUV,[card,text,1])
#     IDE_DO.accept(IDE_getMode()+MODE_SUFFIX+'wheel_down',adjustUV,[card,text,-1])

def IDE_closeConfDialog(confFunc,argsNresult):
    IDE_textCursorIval.resume()
    IDE_dialog.ival.pause()
    IDE_dialog.root.find('**/rigLightOn').hide()
    Sequence(
        # stops collision task
        Func(IDEPolyButton.stop),
        Func(IDE_dialog.disableDialogButtons),
        Func(IDE_dialog.uvFlow.pause),
        Parallel(
           IDE_dialog.root.find('**/textBG').hprInterval(.15,Vec3(0,-90,0),blendType='easeOut'),
           IDE_dialog.root.find('**/y').hprInterval(.15,Vec3(0,0,-90),blendType='easeOut'),
           IDE_dialog.root.find('**/c').hprInterval(.15,Vec3(0,0,-90),blendType='easeOut'),
           ),
        Wait(.05),
        Parallel(
           IDE_dialog.root.posInterval(.2,Point3(0,0,-1.2),other=IDE_2Droot,blendType='easeIn'),
           IDE_dialog.root.find('**/veil').colorScaleInterval(.2,Vec4(0))
           ),
        # destroys it
        Func(IDE_dialog.root.find('**/veil').getPythonTag('destroy')),
        Func(IDE_dialog.root.find('**/veil').clearPythonTag,'destroy'),
        Func(IDE_dialog.cleanup),
        Func(globals().__setitem__,'IDE_dialog',None),
        # runs command
        Func(confFunc,*argsNresult),
        name=IDE_ivalsName+'close dialog'
    ).start()

def IDE_raisePreferenceWindow():
    IDE_setMode(IDE_lastMode)
    if IDEPreferences.PREF_OPEN:
       IDEPreferences.openPreferences()

def IDE_openPreferenceByButton():
    if IDE_isInMode(MODE_preferenceAvail):
       IDEPreferences.openPreferences()

def IDE_cleanupAndExit(exit=False):
    global IDE_lastMode
    IDE_setMode(IDE_lastMode)
    if not exit:
       return
    if IDEPreferences.PREF_OPEN:
       IDE_lastMode=IDE_getMode()
       IDE_setMode(MODE_noInput)
       IDE_openOkDialog('Preferences window is still active.\nPlease finalize tuning before exit.',IDE_raisePreferenceWindow)
       return
    IDE_saveFilesList()
    IDE_saveCFGtoFile()
    print('\nIDE shutdown on '+time.strftime('%A, %b %d %Y, %H:%M', time.gmtime(time.time()-time.timezone)))
    print('GOOD BYE')
    LOG.writeToDisk()
    M.IDE_exitStatus=1
    IDE_DO.ignoreAll()
    renderFrame(2)
    killPStatsServer()
    taskMgr.doMethodLater(.1,IDE_reallyExit,'IDE_reallyExit',extraArgs=[])

def IDE_saveFilesList():
    lastEditedFiles=[d.FullPath for d in IDE_documents if d.FullPath]
    # puts the main file back in, if it's closed
    if APP_mainFile not in lastEditedFiles:
       lastEditedFiles.insert(0,APP_mainFile)
    currFile=IDE_doc.FullPath if IDE_doc is not None and IDE_doc!=IDE_log else APP_mainFile
    # respects user's prefered CWD, use it at next runtime by default
    lastEditedFiles.append([APP_mainFile,currFile,APP_CWD])
    # saves the opened files list to a file
    dumpToFile(lastEditedFiles, joinPaths(IDE_path,'%s.%s'%(LAST_FILES,PLATFORM)))
    # saves the recently opened files list to a file
    dumpToFile(IDE_recentFiles, recentFilesListName)
    # saves the files records to a file
    for d in IDE_documents:
        # updates only existing files
        if not d.isChanged and d.FullPath:
           if os.path.exists(d.FullPath):
              IDE_filesProps[d.FullPath]=[ os.path.getsize(d.FullPath),
                                           os.stat(d.FullPath)[stat.ST_MTIME],
                                           d.line,
                                           d.column,
                                           list(d.markedColumns.items()),
                                           d.canvasXpos,
                                           d.canvasZpos/IDE_lineScale[2],
                                           d.preferedCWD,
                                           d.preferedArgs,
                                         ]
           else:
              del IDE_filesProps[d.FullPath]
    dumpToFile(IDE_filesProps, filesPropsName)

def loadSound(name):
    s=loader.loadSfx(name)
    s.setVolume(.2)
    s.setInvulnerable(1)
    return s

def disableMouse2Cam():
    base.mouseInterface.stash()

def enableMouse2Cam():
    base.mouseInterface.unstash()

def mustBeHalted():
    return IDE_isInMode(MODE_forcingRender)

def IDE_forceRender(forced=False):
    if not forced and (UNDO or REDO): return
    M.IDE_lastModeB4ForcedRender = IDE_getMode()
    # I need to render a frame and also updating key up/down status,
    # so temporarily redirect all events, then do a whole framework step
    IDE_setMode(MODE_forcingRender)
    IDE_step()
    IDE_setMode(IDE_lastModeB4ForcedRender)

def relocateFRMeter(IDE=True):
    if base.frameRateMeter:
       frm=NodePath(base.frameRateMeter)
       frm.clearTransform()
       minb,maxb=frm.getTightBounds()
       dim=maxb-minb
       frm.setScale(IDE_scale)
       tmpParent=frm.getParent().attachNewNode('')
       if IDE:
          frm.setPos(SliderBG,-IDE_winORatio,0,-1-IDE_frameHeight+dim[2])
          tmpParent.setPos(frm.getTightBounds()[1][0],0,frm.getTightBounds()[0][2])
       else:
          frm.setPos(SliderBG,-IDE_winORatio+IDE_canvasThumbWidth,0,-1+IDE_tabsHeight)
          tmpParent.setPos(frm.getTightBounds()[1])
       frm.wrtReparentTo(tmpParent)
       frmScale=IDE_tabsHeight*.75
       tmpParent.setScale(frmScale/dim[2])
       frm.wrtReparentTo(tmpParent.getParent())
       tmpParent.removeNode()

def warnReadonlyDoc():
    IDE_SOUND_blockedKeyb.play()
    putMsg(createMsg('NOTE: File %s is read only'%IDE_doc.FileName,fg=(0,0,0,1),bg=(.9,.8,.4,.85)),'readonly doc')

def IDE_alertUserNcontinue(keepRunning=1):
    if IDEmini.IDE_activated and IDE_root.isHidden(): # restores IDE if it's not active
       IDE_goBackToIDE()
    IDE_processException( traceback.format_exc() )
    # continue running
    if keepRunning:
       IDE_safeRun()

def IDE_safeRun():
    try:
        taskMgr._origRun()
    except SystemExit:
        if IDE_exitStatus==1:
           IDE_shutdown()
        else:
           print("user's APP just tried to force exit", file=IDE_DEV)
           IDE_alertUserNcontinue()
    except:
        print(IDE_errShoutout)
        traceback.print_exc()
        IDE_alertUserNcontinue()

def IDE_safeStep():
    try:
        dataStepFunc(base)
        ivalStepFunc(base)
        igStepFunc(base)
    except:
        print(IDE_errShoutout)
        traceback.print_exc()
        IDE_alertUserNcontinue(keepRunning=0)

################################################################################
def IDE_isAnyModifierDown():
    for b in IDE_modifiers:
        if base.mouseWatcherNode.isButtonDown(b):
           return True
    return False

def IDE_isShiftOnlyDown():
    shift = False
    for b in IDE_modifiers:
        if base.mouseWatcherNode.isButtonDown(b):
           if b==MODIF_shift:
              shift = True
           else:
              return False
    return shift

def IDE_getMode():
    return IDE_BTnode.getPrefix().replace(MODE_SUFFIX,'')

def IDE_setMode(mode):
    IDE_BTnode.setPrefix(mode+MODE_SUFFIX)

def IDE_isInMode(mode):
    currMode = IDE_getMode()
    if type(mode) in myFinder.PythonSequence:
       for m in mode:
           if currMode==m:
              return True
       return False
    else:
       return currMode==mode

def IDE_acceptKeyMap(km,method,extraArgs=[],repeat=False):
    IDE_acceptKeys(km,method,extraArgs,repeat)

def IDE_acceptKeys(events,method,extraArgs=[],repeat=False):
    if type(events) in STRINGTYPE:
       events=[events]
    repeatEvts=[e+'-repeat' for e in events] if repeat else []
    for event in events+repeatEvts:
        for mode in IDE_MODES:
            IDE_DO.accept(mode+MODE_SUFFIX+event,method,extraArgs)

def IDE_disableDefaultUserBT():
    base.buttonThrowers[0].stash() # disables the default button thrower
    base.timeButtonThrower.stash() # disables the default time button thrower
    IDE_getAPPButtonThrowers().stash() # disables user-created button throwers

def IDE_toggleIDEorScene():
    if IDE_root.isHidden():
       IDE_goBackToIDE()
    else:
       IDE_jumpToScene()

def IDE_jumpToScene():
    global IDE_lastMode,IDE_lastDocB4Jump2Scene
    currMode=IDE_getMode()
    if currMode in [MODE_active,MODE_noFile,MODE_completing]:
       if currMode==MODE_completing:
          IDE_CC_cancel()
          currMode=IDE_getMode()
       IDE_lastMode=currMode
       IDE_root.hide()
       if SGB_overScene:
          M.SGBframeOverScene = SGBframe.instanceUnderNode(IDE_2Droot,'')
       base.buttonThrowers[0].unstash()
       base.timeButtonThrower.unstash() # enables the default time button thrower
       IDE_getAPPButtonThrowers(stashed=True).unstash() # enables user-created button throwers
       IDE_setMode(MODE_noInput)
       if IDE_isScenePaused and not PR.resumeLocked:
          IDE_toggleSceneActive(1) # activates scene
       IDE_lastDocB4Jump2Scene=None
       if IDE_log:
          if IDE_doc!=IDE_log:
             IDE_lastDocB4Jump2Scene=IDE_doc
             IDE_log.setDocActive(tempSwitch=1)
          IDE_textCursor.stash()
          # these must be done after the log is set as active doc
          logOverScene=IDE_new_canvas.instanceUnderNode(IDE_logOverSceneParent,IDE_logOverSceneNodeName)
          logOverScene.setTransform(IDE_new_canvas.getParent().getTransform(IDE_2Droot))
          logOverScene.setTexture(IDE_logOverSceneTex,1)
          logOverScene.setColorScale(IDE_COLOR_logOverScene,2)
          slider=SliderBG.instanceUnderNode(IDE_logOverSceneParent,'slider instance')
          slider.setTransform(SliderBG.getParent().getTransform(IDE_2Droot))
#           IDE_logOverSceneParent.setZ(IDE_tabsHeight)
          IDE_logOverSceneParent.find('**/block_display*').hide()
       enableMouse2Cam()
       relocateFRMeter(IDE=False)
       if APP_cursorHidden:
          IDE_hideCursor()
       if APP_pointerNrestPos:
          base.win.movePointer(*APP_pointerNrestPos)
          # without this, there will be still some offset. The movement must be done at once.
          IDE_safeStep()
          IDE_safeStep()
#           renderFrame(2)
       if APP_mouseRelative: # must be done after moving the pointer
          IDE_setMouseRelative()
       taskMgr.doMethodLater(.01,IDE_setMode,IDE_tasksName+'jumpToScene',extraArgs=[MODE_jump2scene])

def IDE_goBackToIDE():
    global IDE_lastMode,IDE_isScenePaused,IDE_isCtrlDown,IDE_lastDocB4Jump2Scene,\
           APP_cursorHidden,APP_mouseRelative,APP_pointerNrestPos
    __stopdragSliderBar()
    IDE_root.show()
    if SGB_overScene:
       SGBframeOverScene.removeNode()
       M.SGBframeOverScene=None
    IDE_disableDefaultUserBT()
    IDE_setMode(IDE_lastMode)
    IDE_isCtrlDown=False
    IDE_isScenePaused=PR.isPaused # this must be updated to the actual state,
                                  # because the scene can pause/resume itself
    if IDE_log:
       IDE_logOverSceneParent.find('**/block_display*').show()
       IDE_logOverSceneParent.removeChildren()
    IDE_textCursor.unstash()
    if IDE_lastDocB4Jump2Scene:
       IDE_lastDocB4Jump2Scene.setDocActive(tempSwitch=1)
    disableMouse2Cam()
    relocateFRMeter()
    renderFrame(2) # to get the actual properties
    APP_cursorHidden=base.win.getProperties().getCursorHidden()
    APP_mouseRelative=base.win.getProperties().getMouseMode()==WindowProperties.MRelative
    APP_pointerNrestPos=None
    IDE_showCursor()
    IDE_setMouseAbsolute()

def IDE_toggleLogOverScene():
    if IDE_BTnode.getPrefix()!=sliderBarDragPrefix:
       stashed=IDE_logOverSceneParent.isStashed()
       getattr(IDE_logOverSceneParent,'unstash' if stashed else 'stash')()

def IDE_analyzeButtonDown(button):
#     print>>IDE_DEV, button
    if base.mouseWatcherNode.isButtonDown(MODIF_alt):
       if base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey('m')):
          print('MODE :',IDE_getMode(), file=IDE_DEV)
       elif base.mouseWatcherNode.isButtonDown(MODIF_shift) and \
            base.mouseWatcherNode.isButtonDown(KeyboardButton.asciiKey('r')):
          if IDE_isInMode(MODE_forcingRender):
             IDE_setMode(IDE_lastModeB4ForcedRender)
          else:
             IDE_setMode(MODE_active if IDE_documents else MODE_noFile)
          print('MODE RESTORED TO :',IDE_getMode(), file=IDE_DEV)

def IDE_analyzeButtonStroke(button):
#     print>>IDE_DEV, 'STROKE:',button#,ord(button)
    if mustBeHalted(): return
    if not IDE_getMode() in MODE_activeOrCompleting:
       if not IDE_root.isHidden() and not IDE_isInMode(MODE_replacing):
          IDE_SOUND_blockedKeyb.play()
       return
    if not (IDE_isCtrlDown or base.mouseWatcherNode.isButtonDown(MODIF_alt)) and \
         button in myPrintableChars:
       IDE_finishIndentCloseUpViewIval()
       IDE_injectChar(button)
       if button in myPunctuationNoDotWhitespace:
          IDE_CC_cancel()

def IDE_setControlDown():
    M.IDE_isCtrlDown=True

def IDE_setControlUp():
    M.IDE_isCtrlDown=False

################################################################################
def IDE_toggleSceneActive(status=None):
    if status==None:
       if IDE_isScenePaused:
          IDE_resumeScene()
       else:
          IDE_pauseScene()
    elif status:
       IDE_resumeScene()
    else:
       IDE_pauseScene()

def shootScene():
    global IDE_sceneCapture
    IDE_2Droot.hide()
    base.setFrameRateMeter(0)
    BVenabled=base.bufferViewer.isEnabled()
    if BVenabled:
       for c in base.bufferViewer.cards:
           c.stash()
    allRegions=[base.win.getDisplayRegion(r) for r in range(base.win.getNumDisplayRegions())]
    dr=[d for d in allRegions if not d.getCamera().isEmpty() and d.getCamera().getName()=='closeup vpcam']
    if dr: dr[0].setActive(0)
    # render to texture initialization
    buffer=base.win.addRenderTexture(Texture(),mode=GraphicsOutput.RTMCopyTexture)
    # render the next frame
    renderFrame()
    # get the card covering the whole screen
    IDE_sceneCapture=base.win.getTextureCard()
    IDE_sceneCapture.setName('sceneCapture')
    IDE_sceneCapture.reparentTo(render2dp)
    if base.win.getGsg().getCopyTextureInverted():
       IDE_sceneCapture.setSz(-1)
    # stop render-to-texture
    base.win.clearRenderTextures()

    #~ NO LONGER NEEDED to work around RTT problem
    #~ cardTex=IDE_sceneCapture.getTexture()
    #~ if cardTex and cardTex.hasRamImage():
       #~ ox,oy=cardTex.getXSize(),cardTex.getYSize()
       #~ p2x,p2y=math.log(ox,2),math.log(oy,2)
       #~ notP2X,notP2Y=math.modf(p2x)[0]!=.0, math.modf(p2y)[0]!=.0
   #~ #     print 'ox,oy:',ox,oy,
       #~ x,y=2**int(notP2X+p2x), 2**int(notP2Y+p2y)
   #~ #     print 'x,y:',x,y
       #~ oimg=PNMImage()
       #~ cardTex.store(oimg)
       #~ newImg=PNMImage(x,y)
       #~ newImg.copySubImage(oimg,0,y-oy,0,0)
       #~ newTex=Texture()
       #~ newTex.load(newImg)
       #~ IDE_sceneCapture.setTexture(newTex)
    #~ else:
       #~ IDE_sceneCapture.removeNode()

    IDE_2Droot.show()
    base.setFrameRateMeter(1)
    base.frameRateMeter.getDisplayRegion().setSort(MAXINT)
    relocateFRMeter()
    if BVenabled:
       for c in base.bufferViewer.cards:
           c.unstash()
    if dr: dr[0].setActive(1)

def IDE_pauseScene():
    global IDE_2Dscene,IDE_3Dscene,IDE_isScenePaused
    shootScene()
    IDE_2Dscene=render2d.getChildren()
    IDE_2Dscene.stash()
    IDE_3Dscene=render.getChildren()
    IDE_3Dscene.stash()
    IDE_isScenePaused = PR.pause(
       allAnims=1,
       allAudios=1,
       allMovies=1,
       collision=1,
#        excludedTaskNamePrefix=unstoppable_namePrefix,
       excludedIvalNamePrefix=IDE_ivalsName,
#        frameworkStep=IDE_safeStep,
       lowerLevelOperation=0
       )
    IDE_updatePauseStatusText()

def IDE_resumeScene(forced=0):
    global IDE_2Dscene,IDE_3Dscene,IDE_isScenePaused
    try:
       IDE_2Dscene.unstash()
    except:
       pass
    try:
       IDE_3Dscene.unstash()
    except:
       pass
    IDE_2Dscene.clear()
    IDE_3Dscene.clear()
    for c in asList(render2dp.findAllMatches('**/sceneCapture')):
        c.removeNode()
    IDE_isScenePaused = PR.resume(lowerLevelOperation=forced)
    if IDE_isScenePaused==2: # resume is locked
       msg=createMsg('NOTE : the scene was paused from its level.\nYou should not resume it from IDE level.')
       putMsg(msg,'resumeLockedNotify',4,stat=True)
    else:
       IDE_updatePauseStatusText()

def IDE_getAPPButtonThrowers(stashed=False):
    if stashed:
       stashedBTs=base.dataRoot.findAllMatches('**/@@+ButtonThrower')
       stashedBTs.removePath(base.buttonThrowers[0])
       stashedBTs.unstash()
    BTNC = NodePathCollection()
    BTNC.addPath(IDE_BTnodePath)
    BTNC.addPath(base.timeButtonThrower)
    btnThrowers = asList(base.dataRoot.findAllMatches('**/+ButtonThrower'))
    for i in range(base.win.getNumInputDevices()):
        name = base.win.getInputDeviceName(i)
        for bt in btnThrowers:
            if bt.getName()==name:
               BTNC.addPath(bt)
               break
    APPBT = base.dataRoot.findAllMatches('**/+ButtonThrower')
    APPBT.removePathsFrom(BTNC)
    BTNC.clear()
#     print>>IDE_DEV, 'APPBT:',APPBT
    return APPBT


IDE_winX,IDE_winY = base.win.getXSize(),base.win.getYSize()
IDE_winOX,IDE_winOY = IDE_winX,IDE_winY
IDE_winORatio = float(IDE_winX)/IDE_winY

renderFrame() # must be done to get the correct properties
APP_cursorHidden = base.win.getProperties().getCursorHidden()
APP_mouseRelative = base.win.getProperties().getMouseMode()==WindowProperties.MRelative
# mouse cursor might be hidden already by user's app
if APP_cursorHidden:
   IDE_showCursor()
if APP_mouseRelative:
   IDE_setMouseAbsolute()
APP_pointerNrestPos=None
disableMouse2Cam()

IDE_MB = ModifierButtons()
IDE_MB.addButton(KeyboardButton.shift())
IDE_MB.addButton(KeyboardButton.control())
IDE_MB.addButton(KeyboardButton.alt())
IDE_MB.addButton(KeyboardButton.meta())
IDE_BTnode = ButtonThrower('IDE button thrower')
IDE_BTnode.setButtonDownEvent('IDE_buttonDown')
IDE_BTnode.setKeystrokeEvent('IDE_btnStroke')
IDE_BTnode.setModifierButtons(IDE_MB)
IDE_BTnodePath = base.buttonThrowers[0].getParent().attachNewNode(IDE_BTnode)

base.buttonThrowers[0].stash() # disables the default button thrower
base.timeButtonThrower.stash() # disables the default time button thrower
IDE_getAPPButtonThrowers().stash() # disables user-created button throwers

dataStepFunc = taskFunc(taskMgr.getTasksNamed('dataLoop')[0])
ivalStepFunc = taskFunc(taskMgr.getTasksNamed('ivalLoop')[0])
igStepFunc = taskFunc(taskMgr.getTasksNamed('igLoop')[0])

# activates notify output redirection
LOG.startMonitorNotify()


###############################################################################
###############################################################################
class CC_TEMP:
   def __init__(I,fullpath,globalDict):
       I.__dict__=globalDict
       I.fullpath=fullpath
       I.core=[] # includes core itself to the core attributes list
       I.core=list(I.__dict__.keys())

   def cleanup(me):
       # get the keys as list, not iterator, to prevent dict changed during iteration error
       for a in list(me.__dict__.keys()):
           if a not in me.core: # clears everything except the core attributes
              del me.__dict__[a]

   def doImport(me,importWhat):
       exec((importWhat), me.__dict__)

   def doExec(this,evalWhat):
       print('EXECUTING :',evalWhat, file=IDE_DEV)
       attr=evalWhat[:evalWhat.find('=')]
       exec(evalWhat, IDE_CC_TEMP_GLOBAL, this.__dict__)
       return getattr(this,attr)

# THIS ONE IS FOR CODE COMPLETION ISOLATED NAMESPACE
IDE_CC_TEMP_GLOBAL = {}
IDE_CC_TEMP = CC_TEMP(None,IDE_CC_TEMP_GLOBAL)
# object to hold temporary import
importLine_GLOBAL = {}
importLine_CC_TEMP = CC_TEMP(None,importLine_GLOBAL)

CC_TW = TextWrapper()
CC_TW.width=70

################################################################################
IDE_lastMode = MODE_starting
IDE_setMode(MODE_starting)

IDE_FONT_monospace=loader.loadFont('Monospace.ttf')
IDE_FONT_monospaceBold=loader.loadFont('Monospace Bold.ttf')
IDE_FONT_transmetals=loader.loadFont('Transmetals.ttf')
IDE_FONT_transmetals.setLineHeight(.9)
IDE_FONT_digitalStrip=loader.loadFont('DigitalStrip.ttf')
IDE_FONT_digitalStripBold=loader.loadFont('DigitalStrip Bold.ttf')
IDE_FONT_usuzi=loader.loadFont('Usuzi.ttf')
IDE_FONT_medrano=loader.loadFont('Medrano.ttf')


## wxPython stuff ##############################################################
wxBigFont = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD)
LCimageList=wx.ImageList(16,16)
LCimageList.Add(wx.Bitmap(joinPaths(IDE_imagesPath,'listUpArrow.png')))
LCimageList.Add(wx.Bitmap(joinPaths(IDE_imagesPath,'listDownArrow.png')))

def startWxLoop():
    taskMgr.add(handleNewWx, IDE_tasksName+'handleWx')

def stopWxLoop():
    taskMgr.remove(IDE_tasksName+'handleWx')

def WxStep():
    while newWxEVTloop.Pending():
        newWxEVTloop.Dispatch()
    wxApp.ProcessIdle()

def WxStepAndStop():
    while newWxEVTloop.Pending():
        newWxEVTloop.Dispatch()
    wxApp.ProcessIdle()
    stopWxLoop()

def handleNewWx(task):
    while newWxEVTloop.Pending():
        newWxEVTloop.Dispatch()
#     time.sleep(.001)
    # very important for UI updates
    wxApp.ProcessIdle()
    #print>>IDE_DEV, '.',
    return Task.cont

def handleNavigationalWxEvents(ce):
    def getBookParent(o):
        if type(o)!=wx.Notebook:
           topLevel=o.GetTopLevelParent()
           parent=o.GetParent()
           while parent!=topLevel:
                 if type(parent)==wx.Notebook:
                    return parent
                 parent=parent.GetParent()
        return o
    KC=ce.GetKeyCode()
    EO=ce.GetEventObject()
    # serves the navigational key events, which relies on wx eventloop,
    # which is not enabled on Windows, since it steals Panda's keystrokes
    # (IT'S WORSE THAN LOSING WX NAVIGATIONAL EVENTS)
    if type(EO) in (wx.Button,wx.BitmapButton) and KC in (wx.WXK_NUMPAD_ENTER,wx.WXK_RETURN):
       waitForKeyUp(EO)
       e=wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED)
       e.EventObject=EO
       EO.ProcessEvent(e)
    elif KC==wx.WXK_PAGEUP and ce.ControlDown() and not EO.IsTopLevel():
       b=getBookParent(EO)
       if type(b)==wx.Notebook:
          b.AdvanceSelection(False)
    elif KC==wx.WXK_PAGEDOWN and ce.ControlDown() and not EO.IsTopLevel():
       b=getBookParent(EO)
       if type(b)==wx.Notebook:
          b.AdvanceSelection()
    elif KC==wx.WXK_DOWN and type(EO)==wx.Notebook:
       EO.GetPage(EO.Selection).SetFocus()
    elif KC==wx.WXK_TAB:
       NKE=wx.NavigationKeyEvent
       EO.Navigate(NKE.IsBackward if ce.ShiftDown() else NKE.IsForward)
    elif ce.AltDown() and not ce.ControlDown() and not ce.MetaDown() and \
         KC!=wx.WXK_ALT: # look for shortcut keys
       # ARRRRGH !
       # For wx.Button, simply using wx step causes hard crash,
       # if when pressing the shortcut key, the widget in focus is other than
       # the one after the interface were created, so I have to do it the complicated way
#        WxStep()
#        return
       widgets=[]
       parent=EO.GetParent()
       while type(parent)!=wx.Panel:
             parent=parent.GetParent()
       for w in getWxSizerWidgets(parent.GetSizer()):
           label=w.GetLabel()
           if label.find('&')>-1 and ord(label[label.index('&')+1].upper())==KC:
              widgets.append(w)
       if widgets:
          if len(widgets)==1:
             inFocus=widgets[0]
          else: # shortcut key is used by multiple widgets
             if ce.ShiftDown():
                func=lambda w: w.GetId()>EO.GetId()
             else:
                func=lambda w: w.GetId()<EO.GetId()
             nextWidgets=list(filter(func,widgets))
             inFocus=(nextWidgets if nextWidgets else widgets)[-1*ce.ShiftDown()]
          if not inFocus.AcceptsFocus(): # can't accept focus, try next widgets
             id=inFocus.GetId()-1
             w=parent.FindWindowById(id)
             while w and not w.AcceptsFocus():
                   id=w.GetId()-1
                   w=parent.FindWindowById(id)
             if w:
                inFocus=w
          if inFocus.AcceptsFocus():
             inFocus.SetFocusFromKbd()
             # The whole point of this complicated way is to block any button
             # from generating event upon shortcut-key down. Setting it to focus is enough.
             if type(inFocus)!=wx.Button:
                WxStep()
             # simply crashes, delayed or not, using doMethodLater or stdpy.threading2.Timer
#              else:
#                 inFocus.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED))
    else:
       ce.Skip()

def waitForKeyUp(EO):
    keyUpCatcher=wx.Button(EO.GetParent(),-1)
    keyUpCatcher.__isUp=False
    # it's OK to let __isUp filled with the event itself, it's True anyway
    keyUpCatcher.Bind(wx.EVT_KEY_UP,Functor(setattr,keyUpCatcher,'__isUp'))
    keyUpCatcher.Hide()
    keyUpCatcher.SetFocus()
    while not keyUpCatcher.__isUp:
          keyUpCatcher.SetFocus()
          WxStep()
          if EO.GetParent().FindFocus()!=keyUpCatcher:
             keyUpCatcher.__isUp=False
          print('WX: release the button please.....')
    keyUpCatcher.Destroy()
    EO.SetFocus()

def getWxSizerWidgets(sizers):
    if type(sizers) not in (tuple,list):
       sizers=(sizers,)
    widgets=[]
    for s in sizers:
        for c in s.GetChildren():
            w=c.GetWindow()
            if w is None:
               sizerChild=c.GetSizer()
               if sizerChild is not None:
                  widgets+=getWxSizerWidgets(sizerChild)
            else:
               widgets.append(w)
    return widgets

# enabling wx event loop on Windows steals Panda's keystrokes
NO_WX_LOOP = WIN
if not WIN:
   startWxLoop()


################################################################################
def __startdragSliderBar(m=None):
    global IDE_oldPrefix
    IDE_removeAnyMenuNcallTip()
    mpos=base.mouseWatcherNode.getMouse()
    parentZ=vertSliderBar.getParent().getZ(render2dp)
    sliderDragTask=taskMgr.add(__dragSliderBar,dragSliderBarTaskName)
    sliderDragTask.ZposNoffset=mpos[1]-vertSliderBar.getZ(render2dp)+parentZ
    sliderDragTask._lastMpos=Point2(mpos)
    IDE_oldPrefix=IDE_BTnode.getPrefix()
    IDE_BTnode.setPrefix(sliderBarDragPrefix)
    IDE_DO.acceptOnce(sliderBarDragPrefix+'mouse1-up',__stopdragSliderBar)
    IDE_DO.acceptOnce(cancelSliderBarDragEvent,__stopdragSliderBar,[None,IDE_canvas.getZ()])

def __dragSliderBar(t):
    if not base.mouseWatcherNode.hasMouse():
       return Task.cont
    mpos=base.mouseWatcherNode.getMouse()
    if t._lastMpos==mpos:
       parentZ=vertSliderBar.getParent().getZ(render2dp)
       Zoffset=mpos[1]-vertSliderBar.getZ(render2dp)+parentZ
       if Zoffset!=t.ZposNoffset:
          t.ZposNoffset=Zoffset
       return Task.cont
    if -1<=mpos<=1:
       t._lastMpos=Point2(mpos)
    __updateCanvasZpos((t.ZposNoffset-mpos[1])/(IDE_canvasRatio*IDE_scale[2]))
    return Task.cont

def __stopdragSliderBar(m=None,lastZ=None):
    taskMgr.remove(dragSliderBarTaskName)
    IDE_DO.ignore(sliderBarDragPrefix+'mouse1-up')
    IDE_DO.ignore(cancelSliderBarDragEvent)
    __stopScrollPage()
    if lastZ is not None:
       __updateCanvasZpos(lastZ)
    IDE_BTnode.setPrefix(IDE_oldPrefix)

def __startScrollPage(dir,m):
    if not (IDE_isInMode(MODE_active) or IDE_root.isHidden()):
       return
    global IDE_oldPrefix, pageUpDnSuspended
    IDE_oldPrefix=IDE_BTnode.getPrefix()
    IDE_BTnode.setPrefix(sliderBarDragPrefix)
    IDE_DO.acceptOnce(sliderBarDragPrefix+'mouse1-up',__stopdragSliderBar)
    t=taskMgr.add(__scrollPage,IDE_tasksName+'scrollPage',extraArgs=[int((dir+1)*.5),dir*IDE_frameHeight])
    pageUpDnSuspended=[0,0]

def __scrollPage(dir,scroll):
    if not pageUpDnSuspended[dir]:
       __scrollCanvas(scroll)
    return Task.cont

def __stopScrollPage(m=None):
    taskMgr.remove(IDE_tasksName+'scrollPage')

def __suspendScrollUp(m=None):
    pageUpSkin.setColorScale(pageArrowInactiveColor)
    pageUpDnSuspended[0]=1
def __continueScrollUp(m=None):
    if taskMgr.hasTaskNamed(dragSliderBarTaskName) or (not IDE_isInMode(MODE_active) and IDE_BTnode.getPrefix()!=sliderBarDragPrefix):
       return
    pageUpSkin.setColorScale(1,1,1,1)
    pageUpDnSuspended[0]=0

def __suspendScrollDn(m=None):
    pageDnSkin.setColorScale(pageArrowInactiveColor)
    pageUpDnSuspended[1]=1
def __continueScrollDn(m=None):
    if taskMgr.hasTaskNamed(dragSliderBarTaskName) or (not IDE_isInMode(MODE_active) and IDE_BTnode.getPrefix()!=sliderBarDragPrefix):
       return
    pageDnSkin.setColorScale(1,1,1,1)
    pageUpDnSuspended[1]=0

def __suspendScrollPage(m=None):
    __suspendScrollUp()
    __suspendScrollDn()

def __enteringThumb(m=None):
    if IDE_isInMode(MODE_active) or IDE_root.isHidden():
       __suspendScrollPage()

def __exitingThumb(m=None):
    if IDE_isInMode(MODE_active) or IDE_root.isHidden():
       pass

def __scrollCanvas(scroll,adjCursor=False,forced=False):
    if vertSliderBar.isHidden() and not IDE_root.isHidden():
       return
    __updateCanvasZpos(IDE_canvas.getZ()+scroll,forced)
    if adjCursor and not -1+IDE_statusBarHeight+IDE_lineScale[2]<IDE_textCursor.getZ(render2dp)<1-IDE_tabsHeight:
       canvasZ=IDE_canvas.getZ()
       minZ=int(canvasZ/IDE_lineScale[2])
       if minZ*IDE_lineScale[2]<canvasZ/IDE_lineScale[2]:
          minZ+=1
       maxZ=int((canvasZ+IDE_frameHeight)/IDE_lineScale[2]-1.5)
       IDE_doc.line=clampScalar(minZ,maxZ,IDE_doc.line)
       IDE_doc.column=min(IDE_doc.lastMaxColumn,len(IDE_doc.File[IDE_doc.line].rstrip('\n')))
       IDE_updateCurPos()
       # adjust canvas' X if current column is outside the frame
       __exposeColumn()

def __updateCanvasZpos(Zpos,forced=False):
    # Let's handle this here instead of spreading it everywhere.
    # Negative Z is not supposed to happen, so use this mean to indicate that
    # I want to slide it to the doc end.
    if Zpos==-1:
       Zpos=IDE_canvasLen-IDE_frameHeight+.015
    oldZ=IDE_canvas.getZ()
    newZ=clampScalar(Zpos, .0, IDE_canvasLen-IDE_frameHeight+.015)
    thumbZ=-newZ*IDE_canvasRatio
    vertSliderBar.setZ(thumbZ)
    if IDE_doc is None or (abs(oldZ-newZ)<1e-3 and not forced):
       return False
    pageUpRegion['frameSize']=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,
                               thumbZ-IDE_canvasThumbBorder,-IDE_canvasThumbBorder)
    pageUpSkin.setTexScale(pageArrowAlphaTS,-IDE_frameHeight/min(thumbZ,-.001),1)
    PDmin=-IDE_frameHeight+IDE_canvasThumbBorder
    PDmax=thumbZ+vertSliderBar['frameSize'][2]
    pageDnRegion['frameSize']=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,
                               PDmin,PDmax)
    pageDnSkin.setTexScale(pageArrowAlphaTS,IDE_frameHeight/max(PDmax-PDmin,.001),1)
    IDE_doc.canvasZpos=newZ
    IDE_doc.lineMarkParent.setZ(IDE_new_canvas,newZ)
    IDE_canvas.setZ(newZ)
    populatePage()
    return True

def populatePage(startLine=-100,forced=False):
    isLoadedFile=type(IDE_doc)!=types.FunctionType and IDE_doc is not None
    if not isLoadedFile or REPLACING or JUMP_TO_SAVED: return #or UNDO or REDO
#     startT=globalClock.getRealTime()
    canvasZ=IDE_canvas.getZ()
    renderStartLine=int(canvasZ/IDE_lineScale[2])
    # exclusive range end, don't subtract numLines by 1
    renderEndLine=clampScalar(0, max(0,IDE_doc.numLines), int((canvasZ+IDE_frameHeight)/IDE_lineScale[2])+1 )
#     print>>IDE_DEV, renderStartLine,renderEndLine
    neededStuff=NodePathCollection()
    newDisplay=list(range(renderStartLine,renderEndLine))
    if forced:
       reused=[]
       IDE_doc.displayed.clear()
    else:
       lastDisplayed=list(IDE_doc.displayed.keys())
       reused=intersection(lastDisplayed,newDisplay)
       if renderStartLine-2<startLine<=renderEndLine:
          removed=[l for l in IDE_doc.displayed if l>=startLine]
          for r in removed:
              if r in reused:
                 reused.remove(r)
       removed=difference(lastDisplayed,reused)
       newDisplay=difference(newDisplay,reused)
       for r in removed:
           IDE_doc.displayed[r].removeNode()
           del IDE_doc.displayed[r]
    if newDisplay:
       renderStartLine=min(min(newDisplay),IDE_doc.numLines-1)
       # exclusive range end, don't subtract numLines by 1
       renderEndLine=min(max(newDisplay)+1,IDE_doc.numLines)
    else: # NO NEW LINE NEED TO BE RENDERED
       return
    for keptLine in reused:
        neededStuff.addPath(IDE_doc.displayed[keptLine])
    neededStuff.addPath(IDE_textCursor) # keeps the cursor
    neededStuff.addPath(IDE_doc.helperLine) # keeps the indentation helper line
    # keeps the moved lines visual effect
#     neededStuff.addPathsFrom(IDE_doc.textParent.findAllMatches('**/movedLineDuplicate'))
    neededStuff.detach()
    bmh=IDE_doc.textParent.find('**/bracketMatchHilight')
    if not bmh.isEmpty():
       bmh.detachNode()
    IDE_doc.textParent.node().removeAllChildren()
    neededStuff.reparentTo(IDE_doc.textParent)
    neededStuff.clear()
    if not bmh.isEmpty():
       bmh.reparentTo(IDE_doc.textParent)
    isQuoted,color=IDE_doc.getLineQuotedNColor(renderStartLine)
#     print>>IDE_DEV, 'DRAWN: %s-%s'%(renderStartLine,renderEndLine)
    for z in range(renderStartLine,renderEndLine):
        textLine=IDE_doc.textParent.attachNewNode(str(z))
        IDE_doc.displayed[z]=textLine
        # DO NOT use this
#         color,isQuoted=IDE_doc.drawTextLine(z,textLine,color,isQuoted)
        # To maintain correctness, always get the quoted status
        # from the database, instead of from the result of drawTextLine, so it's easier
        # to debug if I made mistakes in updating the quoted status database
        isQuoted,color=IDE_doc.getLineQuotedNColor(z)
        IDE_doc.drawTextLine(z,textLine,color,isQuoted)
        textLine.setZ(-z*IDE_lineheight)
    #~ print>>IDE_DEV, 'POPULATED in %s sec'%(globalClock.getRealTime()-startT)

def adjustCanvasLength(numItem,forced=0):
    global IDE_canvasLen, IDE_canvasRatio
    if not UPDATE_DISPLAY or MOVING_LINES: return
    IDE_canvasLen=float(numItem)*IDE_lineScale[2]
    canvasRatio=(IDE_frameHeight-.015)/(IDE_canvasLen+IDE_canvasThumbBorder)
    scaledFrameHeight=IDE_frameHeight*canvasRatio
    thumbSizeDiff=max(scaledFrameHeight,IDE_canvasThumbMinZSize)-scaledFrameHeight
    IDE_canvasRatio=canvasRatio-thumbSizeDiff/(IDE_canvasLen+IDE_canvasThumbBorder)
    if IDE_canvasLen<IDE_frameHeight-.015:
       canvasZ=.0
       vertSliderBar.hide()
       pageUpRegion.hide()
       pageDnRegion.hide()
       pageUpSkin.hide()
       pageDnSkin.hide()
       IDE_canvasLen=IDE_frameHeight-.015
    else:
       canvasZ=IDE_canvas.getZ()
       vertSliderBar.show()
       pageUpRegion.show()
       pageDnRegion.show()
       pageUpSkin.show()
       pageDnSkin.show()
    vsliderBottomZ=-max(scaledFrameHeight,IDE_canvasThumbMinZSize)
    vertSliderBar['frameSize']=(IDE_canvasThumbBorder,
                                IDE_canvasThumbWidth+IDE_canvasThumbBorder,
                                vsliderBottomZ, -IDE_canvasThumbBorder)
    vsliderBarSkin.setZ(vsliderBottomZ)
    vsliderBarSkin.setSz(-1-(IDE_canvasThumbBorder+vsliderBottomZ)/IDE_canvasThumbWidth)
    vsliderBarSkin.setTexScale(TextureStage.getDefault(),vsliderBarSkin.getSz(),1)
    __updateCanvasZpos(canvasZ,forced)

def __exposeCurrentLine(line=None,center=False,col=None,moveDir=0):
    currLine=IDE_doc.line if line is None else line
    # adjust canvas' Z if current line is outside the frame
    canvasZ=IDE_canvas.getZ()
    if center is None:
       offBottom=canvasZ-(currLine+1.4)*IDE_lineScale[2]<-IDE_frameHeight
       offTop=canvasZ-(currLine)*IDE_lineScale[2]>0
       if offBottom or offTop:
          center=True
          IDE_doc.displayed.clear()
    if center:
       newZ=currLine*IDE_lineScale[2]-.5*IDE_frameHeight
    else:
       newZ=canvasZ
       visLines=IDE_CFG[CFG_visLinesOfCaret]
       bottomSpace=IDE_lineScale[2]*(visLines if moveDir<0 else 0)
       topSpace=IDE_lineScale[2]*(visLines if moveDir>0 else 0)
       if canvasZ-(currLine+1.4)*IDE_lineScale[2]<-IDE_frameHeight+bottomSpace: # off bottom
          newZ=(currLine+1.4)*IDE_lineScale[2]-IDE_frameHeight+bottomSpace
       elif canvasZ-(currLine)*IDE_lineScale[2]>-topSpace: # off top
          newZ=(currLine)*IDE_lineScale[2]-topSpace
    # update
    if abs(canvasZ-newZ)>1e-3:
       ret=__updateCanvasZpos(newZ)
    else:
       ret=False
    # adjust canvas' X if current column is outside the frame
    __exposeColumn(col)
    return ret

def __exposeColumn(col=None):
    if col:
       curX=IDE_frame.getRelativePoint(IDE_textCursor.getParent(),Point3(col*IDE_all_chars_maxWidth,0,0))[0]
    else:
       curX=IDE_textCursor.getX(IDE_frame)
    LedgeSpace=IDE_CFG[CFG_visColumnsOfCaret]*IDE_all_chars_maxWidth*IDE_textScale[0]
    RedgeSpace=IDE_frameWidth-LedgeSpace
    if not (LedgeSpace<curX<RedgeSpace):
       if curX>IDE_frameWidth*.5:
          x=min(IDE_frameBorderWidth*1.2,IDE_canvas.getX(IDE_frame)+RedgeSpace-curX)
       else:
          x=min(IDE_frameBorderWidth*1.2,IDE_canvas.getX(IDE_frame)+LedgeSpace-curX)
       IDE_canvas.setX(IDE_frame,x)
       IDE_doc.canvasXpos=IDE_canvas.getX()


def IDE_SB_createLCpos():
    global SB_LC_parent,SB_LC_BGparent,IDE_curPosText
    SB_LC_parent = statusBar.attachNewNode('line col parent')
    SB_LC_BGparent = IDE_SB_BGcards.copyTo(SB_LC_parent)
    z=.5*(IDE_statusBarHeight-SB_LC_parent.getTightBounds()[1][2])
    SB_LC_parent.setPos(IDE_SB_itemsGap,0,z)
    IDE_curPosText = OnscreenText(parent=SB_LC_parent, fg=IDE_COLOR_statusText,
       pos=(IDE_statusBarHeight*.3,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ALeft,mayChange=1)

def IDE_SB_createBookMarks():
    global SB_Marks_parent,SB_Marks_BGparent,IDE_marksStatusText
    SB_Marks_parent = statusBar.attachNewNode('linemarks parent')
    SB_Marks_BGparent = IDE_SB_BGcards.copyTo(SB_Marks_parent)
    IDE_marksStatusText=OnscreenText(parent=SB_Marks_parent, fg=IDE_COLOR_statusText,
       pos=(IDE_statusBarHeight*.3,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ALeft,mayChange=1)

def IDE_SB_createMacroNotif():
    global SB_Macro_parent,SB_Macro_BGparent,IDE_macroNotif
    SB_Macro_parent = statusBar.attachNewNode('macro notification parent')
    SB_Macro_BGparent = IDE_SB_BGcards.copyTo(SB_Macro_parent)
    spot = PNMImage(16,16)
    spot.addAlpha()
    spot.renderSpot(Vec4D(1,0,0,1),Vec4D(.3,0,0,0),.15,.85)
    spotTex=Texture()
    spotTex.load(spot)
    CM = CardMaker('recordSymbol')
    CM.setFrame(IDE_SB_bgSize*.2,IDE_SB_bgSize*.2+IDE_SB_bgSize,0,IDE_SB_bgSize)
    card = SB_Macro_parent.attachNewNode(CM.generate())
    card.setTransparency(TransparencyAttrib.MAlpha)
    card.setTexture(spotTex)
    card.stash()
    Sequence(
       card.colorScaleInterval(.35,Vec4(1,1,1,.1)),
       card.colorScaleInterval(.35,Vec4(1,1,1,1)),
       name=IDE_ivalsName+'macro recording blink'
       ).loop()
    IDE_macroNotif = OnscreenText(parent=SB_Macro_parent, fg=IDE_COLOR_statusText,
       pos=(IDE_statusBarHeight*.2+IDE_SB_bgSize,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ALeft,mayChange=1)

def IDE_SB_createErrorsNotif():
    global SB_Err_parent,SB_Err_BGparent,IDE_errNotif
    SB_Err_parent = statusBar.attachNewNode('error notification parent')
    SB_Err_BGparent = IDE_SB_BGcards.copyTo(SB_Err_parent)
    IDE_errNotif = OnscreenText(parent=SB_Err_parent, fg=IDE_COLOR_statusText,
       pos=(IDE_statusBarHeight*.3,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ALeft,mayChange=1)

def IDE_SB_createPreferencesButton():
    global SB_Pref_parent,SB_Pref_button
    SB_Pref_parent = statusBar.attachNewNode('preferences parent')
    SB_Pref_parent.setX(render2dp,1-IDE_SB_itemsGap*statusBar.getSx(render2dp))
    SB_Pref_parent.setZ(SB_LC_parent.getZ())
    SB_Pref_button = DirectButton(parent=SB_Pref_parent, image='IDE_pref.png', relief=None,
       scale=IDE_SB_bgSize*.5, command=IDE_openPreferenceByButton,
       clickSound=0, rolloverSound=0, pressEffect=0)
    SB_Pref_button.alignTo(SB_Pref_parent, DGG.LR,DGG.O)
    SB_Pref_button.setTransparency(1)
    prefButtonTT = createTooltip('Preferences',align=TextProperties.ARight, alpha=0)
    prefButtonTT.reparentTo(SB_Pref_button.stateNodePath[2])
    prefButtonTT.setScale(1.55)
    prefButtonTT.setBin('dialogsBin',0)
    Aligner.alignTo(prefButtonTT,SB_Pref_button.stateNodePath[0], DGG.CR, DGG.CL, gap=IDE_SB_itemsAlignGap)

def IDE_SB_createPause():
    global SB_Pause_parent,SB_Pause_BGparent,IDE_pauseStatusText
    SB_Pause_parent = statusBar.attachNewNode('pause parent')
    SB_Pause_BGparent = IDE_SB_BGcards.copyTo(SB_Pause_parent)
    SB_Pause_parent.setX(SB_Pause_parent,-IDE_SB_bgSize)
    SB_Pause_parent.flattenLight()
    IDE_pauseStatusText = OnscreenText(parent=SB_Pause_parent, fg=IDE_COLOR_statusText,
       pos=(-IDE_statusBarHeight*.4,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ARight,mayChange=1)

def IDE_SB_createMessageBar():
    global SB_Msg_parent,SB_Msg_BGparent,IDE_messageLine
    SB_Msg_parent = statusBar.attachNewNode('message bar parent')
    SB_Msg_BGparent = IDE_SB_BGcards.copyTo(SB_Msg_parent)
    SB_Msg_parent.setPos(SB_Err_parent.getTightBounds()[1][0]+IDE_SB_itemsGap,0,SB_LC_parent.getZ())
    IDE_messageLine = OnscreenText(parent=SB_Msg_parent, fg=IDE_COLOR_statusText,
       pos=(IDE_statusBarHeight*.25,IDE_SB_textZ),scale=IDE_SB_textScale,
       align=TextNode.ALeft,mayChange=1)
    msgPlaneNode = PlaneNode('cut msg')
    msgPlaneNode.setPlane( Plane(Vec3(-1,0,0), Point3(0)) )
    IDE_messageLine.setClipPlane(SB_Pause_parent.attachNewNode(msgPlaneNode))

def IDE_arrangeStatusBar():
    Aligner.alignTo(SB_Marks_parent,SB_LC_parent,DGG.UL,DGG.UR, gap=IDE_SB_itemsAlignGap)
    Aligner.alignTo(SB_Macro_parent,SB_Marks_parent,DGG.UL,DGG.UR, gap=IDE_SB_itemsAlignGap)
    Aligner.alignTo(SB_Err_parent,SB_Macro_parent,DGG.UL,DGG.UR, gap=IDE_SB_itemsAlignGap)
    Aligner.alignTo(SB_Pause_parent, SB_Pref_button, DGG.LR,DGG.LL, gap=IDE_SB_itemsAlignGap)
    Aligner.alignTo(SB_Msg_parent,SB_Err_parent,DGG.UL,DGG.UR, gap=IDE_SB_itemsAlignGap)
    s = SB_Msg_parent.getRelativePoint(render2dp,
       Point3(1-IDE_SB_itemsGap*statusBar.getSx(render2dp),0,0))[0]/IDE_SB_bgSize
    s = (-IDE_SB_itemsGap+SB_Msg_parent.getRelativePoint(statusBar,Point3(SB_Pause_parent.getTightBounds()[0][0],0,0))[0])/IDE_SB_bgSize
    SB_Msg_BGparent.setSx(s)
    SB_Msg_BGparent.setTexScale(TextureStage.getDefault(),s,1)

def IDE_findBracketFWD(brCol,b=None):
    brCol+=1
    openBr=(b,) if b else IDE_openBrackets
    closeBr=brMatch=(IDE_bracketsPairs[b],) if b else IDE_closeBrackets
    numOpenBr=numCloseBr=0
    for z in range(IDE_doc.line,IDE_doc.numLines):
        s=IDE_doc.File[z].rstrip()
        sLen=len(s)
        if sLen:
           if IDE_doc.hilight:
              isQuoted,color=IDE_doc.getLineQuotedNColor(z)
              charsColor=IDE_doc.hilightLine(s,color,isQuoted)[2]
           for x in range(brCol,len(s)):
               if IDE_doc.hilight and charsColor[x] in COLORIDX_notCode:
                  continue
               if s[x] in closeBr:
                  if numOpenBr==numCloseBr:
                     return True,s[x],x,z
                  else:
                     numCloseBr+=1
               elif s[x] in openBr:
                  numOpenBr+=1
        brCol=0
    return False,'',0,0

def IDE_findBracketBWD(brCol,b=None):
    closeBr=(b,) if b else IDE_closeBrackets
    openBr=brMatch=(IDE_bracketsInvPairs[b],) if b else IDE_openBrackets
    numOpenBr=numCloseBr=0
    for z in range(IDE_doc.line,-1,-1):
        s=IDE_doc.File[z].rstrip()
        sLen=len(s)
        if not sLen: continue
        if IDE_doc.hilight:
           isQuoted,color=IDE_doc.getLineQuotedNColor(z)
           charsColor=IDE_doc.hilightLine(s,color,isQuoted)[2]
        rightMost=clampScalar(0,sLen,brCol) if z==IDE_doc.line else sLen
        for x in range(rightMost-1,-1,-1):
            if IDE_doc.hilight and charsColor[x] in COLORIDX_notCode:
               continue
            if s[x] in openBr:
               if numOpenBr==numCloseBr:
                  return True,s[x],x,z
               else:
                  numOpenBr+=1
            elif s[x] in closeBr:
               numCloseBr+=1
    return False,'',0,0

def IDE_selectInsideBrackets(cursorAtEnd):
    if IDE_isInMode(MODE_completing):
       IDE_CC_cancel()
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_selectInsideBrackets,cursorAtEnd],False)
    brCol = IDE_doc.column
    s = IDE_doc.File[IDE_doc.line]
    sLen=len(s)
    if not sLen: return
    if brCol>=sLen and IDE_doc.column:
       brCol-=1
    searchDir = 0
    b = s[brCol]
    if b in IDE_openBrackets:
       searchDir=1
    elif b in IDE_closeBrackets:
       searchDir=-1
    elif IDE_doc.column:
       brCol=IDE_doc.column-1
       b = s[brCol]
       if b in IDE_openBrackets:
          searchDir=1
       elif b in IDE_closeBrackets:
          searchDir=-1
    # starts search
    if searchDir==0:
       found,brMatch,x,z = IDE_findBracketFWD(IDE_doc.column)
       if found:
          lastLine=IDE_doc.line
          IDE_doc.line = z
          found,brMatch,sx,sz = IDE_findBracketBWD(x,brMatch)
          IDE_doc.line = lastLine
    elif searchDir==1:
       sz,sx=IDE_doc.line,brCol
       found,brMatch,x,z = IDE_findBracketFWD(brCol,b)
    else:
       z,x=IDE_doc.line,brCol
       found,brMatch,sx,sz = IDE_findBracketBWD(brCol,b)
    if found:
       if cursorAtEnd:
          IDE_doc.blockStartLine,IDE_doc.blockStartCol=sz,sx+1
          IDE_doc.line,IDE_doc.column = z,x
       else:
          IDE_doc.blockStartLine,IDE_doc.blockStartCol=z,x
          IDE_doc.line,IDE_doc.column = sz,sx+1
       IDE_doc.isSelecting = True
       IDE_updateBlock()
       IDE_updateCurPos()
       __exposeCurrentLine()

def IDE_updateCurPos():
    IDE_updateLineMarksStatus()
    if IDE_doc:
       IDE_textCursor.setPos( IDE_doc.column*IDE_all_chars_maxWidth, 0,
                              -IDE_doc.line*IDE_lineheight+IDE_chars_maxBaseline2top)
       IDE_textCursorIval.setT(0)
       IDE_textCursor.setColorScale(IDE_COLOR_caret)
       IDE_curPosText['text']='%s : %s'%(IDE_doc.line+1,IDE_doc.column+1)
    b3=IDE_curPosText.getTightBounds()
    s=((b3[1]-b3[0])[0]+IDE_SB_textEdge)/IDE_SB_bgSize
    sD=s-SB_LC_BGparent.getSx()
    if not IDE_SB_BGupdateThreshold<sD<0:
       SB_LC_BGparent.setSx(s)
       SB_LC_BGparent.setTexScale(TextureStage.getDefault(),s,1)
       IDE_arrangeStatusBar()
    IDE_updateCallTipAlpha()
    if IDE_doc and IDE_doc.displayed:
       bmh = IDE_doc.textParent.find('**/bracketMatchHilight')
       if not bmh.isEmpty():
          bmh.removeNode()
       if IDE_doc.numLines<IDE_CFG[CFG_brMatchMaxLines]:
          brCol=IDE_doc.column
          s=IDE_doc.File[IDE_doc.line]
          sLen=len(s)
          if not sLen: return
          if brCol>=sLen and IDE_doc.column:
             brCol-=1
          searchDir=0
          b=s[brCol]
          if b in IDE_openBrackets:
             searchDir=1
          elif b in IDE_closeBrackets:
             searchDir=-1
          elif IDE_doc.column:
             brCol=IDE_doc.column-1
             b=s[brCol]
             if b in IDE_openBrackets:
                searchDir=1
             elif b in IDE_closeBrackets:
                searchDir=-1
          if searchDir==0:
             return
          if IDE_doc.hilight:
             isQuoted,color=IDE_doc.getLineQuotedNColor()
             charsColor=IDE_doc.hilightLine(s,color,isQuoted)[2]
             if charsColor[brCol] in COLORIDX_notCode:
                return
          tex=IDE_normal_chars_tex if IDEPreferences.PREF_OPEN else IDE_logOverSceneTex
   #        print 'B:',b
          origBrCol=brCol
          found,brMatch,x,z=(IDE_findBracketFWD if searchDir==1 else IDE_findBracketBWD)(brCol,b)
          bh=IDE_REALbrHL.copyTo(IDE_doc.textParent)
          bh.setPos(origBrCol*IDE_all_chars_maxWidth,0,-IDE_doc.line*IDE_lineheight+IDE_chars_maxBaseline2top)
          if not found:
             bh.setColor(1,0,0,1)
          br=IDE_normal_chars[b].copyTo(bh)
          br.setPos(-IDE_chars_offset,0,-IDE_chars_maxBaseline2top*1.05)
          br.setTexture(tex,1)
          br.setColor(IDE_COLOR_punct if IDE_doc.hilight else Vec4(1),1)
          if found:
   #           print 'L:',z,'CLOSE BR:',x
             bmh=IDE_REALbrMatchHL.copyTo(bh)
             bmh.setPos(IDE_doc.textParent,x*IDE_all_chars_maxWidth,0,-z*IDE_lineheight+IDE_chars_maxBaseline2top)
             brM=IDE_normal_chars[brMatch].copyTo(bmh)
             brM.setPos(-IDE_chars_offset,0,-IDE_chars_maxBaseline2top*1.05)
             brM.setTexture(tex,1)
             if IDE_doc.hilight:
                brM.setColor(IDE_COLOR_punct)

def IDE_updateLineMarksStatus():
    if IDE_doc:
       numMLs=len(IDE_doc.markedLines)
       if numMLs:
          Midx=IDE_doc.markedLines.index(IDE_doc.line)+1 if IDE_doc.line in IDE_doc.markedLines else '-'
          IDE_marksStatusText['text']='%s / %s'%(Midx,numMLs)
       else:
          IDE_marksStatusText['text']=''
    b3=IDE_marksStatusText.getTightBounds()
    s=((b3[1]-b3[0])[0]+IDE_SB_textEdge)/IDE_SB_bgSize
    sD=s-SB_Marks_BGparent.getSx()
    if IDE_SB_BGupdateThreshold<sD<0: return
    SB_Marks_BGparent.setSx(s)
    SB_Marks_BGparent.setTexScale(TextureStage.getDefault(),s,1)
    IDE_arrangeStatusBar()

def IDE_updateMacroNotif(lastCommand=''):
    recSym=SB_Macro_parent.find('recordSymbol')
    if IDE_doc:
       record=IDE_doc.recordMacro
       if IDE_doc.recordMacro:
          if recSym.isEmpty():
             SB_Macro_parent.unstashAll()
          IDE_macroNotif['text']='REC: '+lastCommand if lastCommand else 'REC'
       else:
          IDE_macroNotif['text']=''
          if not recSym.isEmpty():
             recSym.stash()
    else:
       record=False
       if not recSym.isEmpty():
          recSym.stash()
    b3=IDE_macroNotif.getTightBounds()
    s=((b3[1]-b3[0])[0]+IDE_SB_textEdge+IDE_SB_bgSize*record)/IDE_SB_bgSize
    sD=s-SB_Macro_BGparent.getSx()
    if IDE_SB_BGupdateThreshold<sD<0: return
    SB_Macro_BGparent.setSx(s)
    SB_Macro_BGparent.setTexScale(TextureStage.getDefault(),s,1)
    IDE_arrangeStatusBar()

def IDE_updateErrNotif():
    if IDE_doc:
       IDE_errNotif['text']='Errors : %s'%IDE_doc.numErrors if IDE_doc.numErrors else ''
    b3=IDE_errNotif.getTightBounds()
    s=((b3[1]-b3[0])[0]+IDE_SB_textEdge)/IDE_SB_bgSize
    sD=s-SB_Err_BGparent.getSx()
    if IDE_SB_BGupdateThreshold<sD<0: return
    SB_Err_BGparent.setSx(s)
    SB_Err_BGparent.setTexScale(TextureStage.getDefault(),s,1)
    IDE_arrangeStatusBar()

def IDE_setMessage(msg=None):
    if msg is not None:
       IDE_messageLine['text']=msg.replace('\n','  ')

def IDE_addMessage(msg):
    IDE_messageLine['text']+=msg.replace('\n','  ')

def IDE_updatePauseStatusText():
    IDE_pauseStatusText['text']='PAUSED' if IDE_isScenePaused else ''
    b3=IDE_pauseStatusText.getTightBounds()
    realSx=((b3[1]-b3[0])[0]+IDE_SB_textEdge)
    s=realSx/IDE_SB_bgSize
    SB_Pause_BGparent.setSx(s)
    SB_Pause_BGparent.setTexScale(TextureStage.getDefault(),s,1)
    SB_Pause_parent.getChild(2).setX(-realSx-IDE_SB_textEdge)
    IDE_arrangeStatusBar()

def IDE_loadTabTexture(name):
    skinLoc=IDE_CFG[CFG_fileTabSkin]
    texFile='%s/IDEtab_%s.png'%(skinLoc,name)
    if os.path.exists(joinPaths(IDE_tabSkinsPath,texFile)):
       return loader.loadTexture(texFile)
    else:
       return None

def IDE_loadSliderTextures(loc):
    global sliderEndTex, sliderBarTex
    sliderEndTex=loader.loadTexture(loc+'/IDE_sliderEnd.png')
    sliderEndTex.setWrapU(Texture.WMClamp)
    sliderBarTex=loader.loadTexture(loc+'/IDE_slider.png')
    sliderBarTex.setWrapU(Texture.WMClamp)

def IDE_handleCloseWindowEvent(win=None):
    if IDE_root.isHidden(): # restores IDE if it's not active
       IDE_goBackToIDE()
    if not IDE_isInMode((MODE_noFile,MODE_active,MODE_completing,MODE_chooseResolution)):
       return
    IDE_exit()

def IDE_handleWindowEvent(win=None,forced=False):
    global IDE_winX, IDE_winY, IDE_scale, IDE_frameWidth, IDE_frameColWidth, IDE_frameHeight
    IDE_resetModifierButtons(win)
    if win is None: return
    # NEW WINDOW JUST CREATED
    if base.buttonThrowers[0].getParent()!=IDE_BTnodePath.getParent():
       IDE_BTnodePath.reparentTo(base.buttonThrowers[0].getParent())
       IDE_2Droot.node().setMouseWatcher(base.buttonThrowers[0].getParent().node())
       relocateFRMeter()
       if not IDE_root.isHidden():
          IDE_disableDefaultUserBT()
    isForeground = win.getProperties().getForeground()
    if isForeground:
       IDE_textCursor.show()
    else:
       IDE_textCursor.hide()

    x,y = win.getXSize(),win.getYSize()
    if IDE_winX==x and IDE_winY==y and not forced:
       if IDE_doc and IDE_doc.isObsolete and \
          isForeground and not IDE_isInMode(MODE_pickFiles):
          IDE_doc.offerReload()
       return
    IDE_removeAnyMenuNcallTip()
    IDE_winX,IDE_winY = x,y
    # counter scale, so must be reversed (original/current)
    IDE_scale.setX(float(IDE_winOX)/IDE_winX)
    IDE_scale.setZ(float(IDE_winOY)/IDE_winY)

    newWidth=2.*IDE_winORatio/IDE_scale[0]
    newHeight=2./IDE_scale[2]
    IDE_docsTabsBG.setScale(IDE_scale)
    IDE_docsTabsBG['frameSize']=(0,newWidth)+IDE_docsTabsBG['frameSize'][2:]
    IDE_exposeTab()
    statusBar.setScale(IDE_scale)
    statusBar['frameSize']=(0,newWidth)+statusBar['frameSize'][2:]
    SB_Pref_parent.setX(render2dp,1-IDE_SB_itemsGap*statusBar.getSx(render2dp))
    IDE_arrangeStatusBar()
    ERR_waitText.setX(render2d,0)

    lineMarksAvail=bool(IDE_doc.markedLines) if IDE_doc else False
    Xoff=IDE_canvas_leftBgXR2D*lineMarksAvail
    IDE_frameWidth=newWidth-IDE_canvasThumbWidth-IDE_canvasThumbBorder-Xoff
    IDE_frameHeight=newHeight-IDE_tabsHeight-IDE_statusBarHeight
    IDE_frameColWidth=IDE_getFrameColWidth()
    IDE_frame.setScale(IDE_scale)
    IDE_frame.setZ(IDE_docsTabsBG,-IDE_tabsHeight)
    logInst=IDE_logOverSceneParent.find('**/log instance')
    if not logInst.isEmpty():
       logInst.setTransform(IDE_new_canvas.getParent().getTransform(IDE_2Droot))
    sliderInst=IDE_logOverSceneParent.find('**/slider instance')
    if not sliderInst.isEmpty():
       sliderInst.setTransform(SliderBG.getParent().getTransform(IDE_2Droot))
    IDE_frame['frameSize']=(0, IDE_frameWidth, -IDE_frameHeight, 0)
    IDE_frame.setX(IDE_docsTabsBG,Xoff)
    IDE_markersBar.setSz(IDE_frameHeight)

    SliderBG.setX(IDE_frameWidth)
    fr=list(SliderBG['frameSize'])
    fr[2]=-IDE_frameHeight
    SliderBG['frameSize']=fr
    sliderTrack['frameSize']=sliderTrack['frameSize'][:2]+(-IDE_frameHeight+IDE_canvasThumbBorder,-IDE_canvasThumbBorder)
    vsliderBottomEnd.setZ(-IDE_frameHeight)
    pageDnSkin.setZ(-IDE_frameHeight+pageArrowOffset)
    for ps in (pageUpSkin,pageDnSkin):
        ps.setSz(IDE_frameHeight)
        ps.setTexScale(TextureStage.getDefault(),ps.getSz()/IDE_canvasThumbWidth,1)

    IDE_objDesc.Frame.setScale(IDE_scale)
    IDE_objDesc.Frame.setPos(statusBar, IDE_objDesc.calcX(),0,IDE_objDesc.calcZ())
    IDE_objDesc.setFrameSize(0, newWidth-2*IDE_canvasThumbWidth-IDE_canvasThumbBorder,-IDE_frameHeight*IDE_CC_codeDesc_portion,0)
    IDE_availCodesList.Frame.setScale(IDE_scale)
    IDE_availCodesList.Frame.setPos(IDE_frame, IDE_availCodesList.calcX(),1,IDE_availCodesList.calcZ())
    IDE_availCodesList.setFrameSize(0, CC_width,-CC_height(),0)

    IDE_overlayParent.setScale(IDE_scale)
    LOG_TW.width=LOG_TW.calcWidth()

    SGB.childrenFrame.setScale(IDE_scale)
    
    IDE_resolutionsList.Frame.setScale(IDE_scale)

    adjustCanvasLength(IDE_doc.numLines if IDE_doc else 0,forced=True)
    populatePage(forced=True)
    relocateFRMeter(IDE=not IDE_root.isHidden())
    # adjust the veil size, so it remains covering the whole window
    veil = IDE_overlayParent.find('**/veil')
    if not veil.isEmpty():
       veil.node().setFrame(-newWidth,newWidth,-newHeight,newHeight)


# new render bins
CBM=CullBinManager.getGlobalPtr()
CBM.addBin('textCursorBin',CullBinEnums.BTUnsorted,500)
CBM.addBin('tabBin',CullBinEnums.BTBackToFront,500)
CBM.addBin('dialogsBin',CullBinEnums.BTUnsorted,1000)
CBM.addBin('overDialogsBin',CullBinEnums.BTUnsorted,1500)
CBM.addBin('gaugeBin',CullBinEnums.BTUnsorted,2000)

# creates IDE root under render2dp, to avoid clash with user's need of render2d & aspect2d
IDE_2Droot = render2dp.attachNewNode(PGTop('IDE_2Droot'))
IDE_2Droot.setTransform(aspect2d.getTransform())
IDE_2Droot.node().setMouseWatcher(base.buttonThrowers[0].getParent().node())
IDE_2Droot.node().setFinal(0)
IDE_2Droot.node().clearBounds()

IDE_root = IDE_2Droot.attachNewNode('IDE_root')
IDE_scale=Vec3(1.)
IDE_tabsHeight=2.*24/IDE_winY-.005
IDE_SB_bgSize=2.*16/IDE_winY
IDE_statusBarHeight=IDE_SB_bgSize*1.25
IDE_SB_itemsGap=IDE_statusBarHeight*.17
IDE_SB_itemsAlignGap = (IDE_SB_itemsGap,0)
IDE_SB_textScale=IDE_statusBarHeight*.585
IDE_SB_textEdge=IDE_statusBarHeight*.685
IDE_SB_textZ=IDE_statusBarHeight*.25
IDE_SB_BGupdateThreshold=-IDE_SB_textEdge*7
IDE_canvasLen=0.
IDE_canvasRatio=1.
IDE_canvasThumbMinZSize=IDE_tabsHeight*1.5
IDE_canvasThumbWidth=IDE_statusBarHeight*.6
IDE_canvasThumbBorder=IDE_canvasThumbWidth*.2
IDE_frameBorderWidth=.007
IDE_frameWidth=2.*base.getAspectRatio()-IDE_canvasThumbWidth-IDE_canvasThumbBorder
IDE_frameHeight=2.-IDE_tabsHeight-IDE_statusBarHeight
IDE_oldPrefix=''

IDE_frameGetColor=lambda:(IDE_COLOR_WSback[0],IDE_COLOR_WSback[1],IDE_COLOR_WSback[2],IDE_CFG[CFG_WSopacity]*.01)
# DirectScrolledFrame to hold script text quads
IDE_frame = DirectScrolledFrame(
    parent=IDE_root,pos=(-base.getAspectRatio(),0,.5*IDE_frameHeight), relief=DGG.GROOVE,
    state=DGG.NORMAL, # to be able to bind some button events
    frameSize=(0, IDE_frameWidth, -IDE_frameHeight, 0),
    frameColor=IDE_frameGetColor(),
    canvasSize=(0, 0, -IDE_frameHeight*.5, 0),
    borderWidth=(IDE_frameBorderWidth,IDE_frameBorderWidth),
    manageScrollBars=0, suppressMouse=0, enableEdit=0 ) # suppressMouse=1 halts mouse wheel
# I don't want its default sliders
IDE_frame.findAllMatches('**/DirectScrollBar*').detach()
# force the ScissorEffect for not spending some frame's space to the slider
IDE_frame['canvasSize']=(0,)*4
IDE_frame.setZ(1.-IDE_tabsHeight)
# the real canvas is "getCanvas()",
IDE_orig_canvas=IDE_frame.getCanvas()
# but no matter how I set the canvas Z pos, the transform stays fixed,
# so just create a new node under the canvas to be my canvas
IDE_new_canvas=IDE_orig_canvas.attachNewNode('IDE_canvas_parent')
IDE_canvas=IDE_new_canvas.attachNewNode('IDE_canvas')
IDE_canvas_minXR2D_noLineNo=-.9925
IDE_canvas_minXR2D=IDE_canvas_minXR2D_noLineNo

# left background
CM=CardMaker('')
CM.setFrame(-.2,0,-1,IDE_frameBorderWidth)
IDE_markersBar=IDE_frame.attachNewNode(CM.generate(),-10)
IDE_markersBar.setTransparency(TransparencyAttrib.MAlpha)
IDE_markersBarGetColor=lambda:Vec4(IDE_COLOR_markersBar[0],IDE_COLOR_markersBar[1],IDE_COLOR_markersBar[2],.6)
IDE_markersBar.setColorScale(IDE_markersBarGetColor(),10)
IDE_markersBar.setTextureOff(1)
IDE_markersBar.setSz(IDE_frameHeight)
IDE_markersBar.hide()

# slider background
SliderBGgetColor=lambda:Vec4(IDE_COLOR_sliderBG[0],IDE_COLOR_sliderBG[1],IDE_COLOR_sliderBG[2],.7)
SliderBG=DirectFrame( parent=IDE_frame, frameSize=(0,IDE_canvasThumbWidth*1.25,-IDE_frameHeight,0),
    frameColor=SliderBGgetColor(), pos=(IDE_frameWidth,0,-IDE_canvasThumbBorder*.5),
    enableEdit=0, suppressMouse=1)
SliderBG.setTransparency(1)
# slider thumb track
sliderTrack = DirectFrame( parent=SliderBG, relief=DGG.FLAT, state=DGG.NORMAL, frameColor=(1,1,1,.2),
    frameSize=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,
               -IDE_frameHeight+IDE_canvasThumbBorder,-IDE_canvasThumbBorder),
    enableEdit=0, suppressMouse=1)
# page bar stuff
pageUpDnSuspended=[0,0]
pageArrowTex=loader.loadTexture('IDE_pageArrow.png')
pageArrowAlphaTex=loader.loadTexture('IDE_pageArrow_alpha.png')
pageArrowAlphaTex.setWrapU(Texture.WMClamp)
pageArrowAlphaTS=TextureStage('pageArrowAlpha')
pageArrowInactiveColor=Vec4(.5,.5,.5,1)
pageArrowOffset=IDE_canvasThumbBorder*5
# page up
pageUpRegion=DirectFrame( parent=SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
             frameSize=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,0,0),
             frameColor=(0,0,0,0), enableEdit=0, suppressMouse=1)
pageUpRegion.bind(DGG.B1PRESS,__startScrollPage,[-1])
pageUpRegion.bind(DGG.ENTER,__continueScrollUp)
pageUpRegion.bind(DGG.EXIT,__suspendScrollUp)
pageUpSkin=SliderBG.attachNewNode(DU.createUVRect(align=0))
pageUpSkin.setSz(IDE_canvasThumbWidth)
pageUpSkin.setR(90)
pageUpSkin.flattenLight()
pageUpSkin.setPos(IDE_canvasThumbBorder,0,-pageArrowOffset)
pageUpSkin.setColorScale(pageArrowInactiveColor)
pageUpSkin.setTexture(pageArrowTex)
pageUpSkin.setTexture(pageArrowAlphaTS,pageArrowAlphaTex)
pageUpSkin.setSz(IDE_frameHeight)
pageUpSkin.setTexScale(TextureStage.getDefault(),pageUpSkin.getSz()/IDE_canvasThumbWidth,1)
pageUpSkin.hide()
# page down
pageDnRegion=DirectFrame( parent=SliderBG, relief=DGG.FLAT, state=DGG.NORMAL,
             frameSize=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,0,0),
             frameColor=(0,0,0,0), enableEdit=0, suppressMouse=1)
pageDnRegion.bind(DGG.B1PRESS,__startScrollPage,[1])
pageDnRegion.bind(DGG.ENTER,__continueScrollDn)
pageDnRegion.bind(DGG.EXIT,__suspendScrollDn)
pageDnSkin=pageUpSkin.copyTo(SliderBG)
pageDnSkin.setR(180)
pageDnSkin.setPos(IDE_canvasThumbWidth+IDE_canvasThumbBorder,0,-IDE_frameHeight+pageArrowOffset)
# slider bar
vertSliderBar=DirectButton(parent=SliderBG, frameColor=(1,1,1,0), # invisible frame
             frameSize=(IDE_canvasThumbBorder,IDE_canvasThumbWidth+IDE_canvasThumbBorder,0,0),
             enableEdit=0, suppressMouse=1,
             rolloverSound=0,clickSound=0)
vertSliderBar.bind(DGG.B1PRESS,__startdragSliderBar)
vertSliderBar.bind(DGG.ENTER,__enteringThumb)
vertSliderBar.bind(DGG.EXIT,__exitingThumb)
sliderBarDragPrefix=IDE_tasksName+'draggingvertSliderBar-'
cancelSliderBarDragEvent=sliderBarDragPrefix+'escape'
dragSliderBarTaskName=IDE_tasksName+'dragSliderBar %s'%id(IDE_frame)
# slider skins textures
IDE_loadSliderTextures(IDE_CFG[CFG_sliderSkin])
# slider bar skins
vsliderBarSkin2=vertSliderBar.attachNewNode(DU.createUVRect(align=0))
vsliderBarSkin2.setScale(IDE_canvasThumbWidth)
vsliderBarSkin2.setR(90)
vsliderBarSkin2.setPos(IDE_canvasThumbBorder,0,-IDE_canvasThumbBorder)
vsliderBarSkin2.setTexture(sliderBarTex)
vsliderBarSkin2.flattenLight()
vsliderBarSkin=vertSliderBar.attachNewNode(DU.createUVRect(align=0))
vsliderBarSkin.setScale(IDE_canvasThumbWidth)
vsliderBarSkin.setR(-90)
vsliderBarSkin.setX(IDE_canvasThumbWidth+IDE_canvasThumbBorder)
vsliderBarSkin.setTexture(sliderBarTex)
vsliderBarSkin.flattenLight()
# slider ends skins
vsliderTopEnd=SliderBG.attachNewNode(DU.createUVRect(align=0))
vsliderTopEnd.setScale(IDE_canvasThumbWidth)
vsliderTopEnd.setR(90)
vsliderTopEnd.flattenLight()
vsliderTopEnd.setPos(IDE_canvasThumbBorder,0,-IDE_canvasThumbBorder)
vsliderTopEnd.setTexture(sliderEndTex)
vsliderBottomEnd=vsliderTopEnd.copyTo(SliderBG)
vsliderBottomEnd.setR(180)
vsliderBottomEnd.setPos(IDE_canvasThumbWidth+IDE_canvasThumbBorder,0,IDE_canvasThumbBorder*1.2)
vsliderBottomEnd.flattenLight()
vsliderBottomEnd.setZ(-IDE_frameHeight)
vertSliderBar.hide()

IDE_overlayParent = IDE_root.attachNewNode('IDE_overlayParent',sort=2000)
IDE_calcMenuMinZ=lambda:render2d.getRelativePoint(statusBar,Point3(0,0,IDE_statusBarHeight*1.3))[2]

IDE_dialogScale=IDE_statusBarHeight*13
IDE_dialogUVscale=42.
IDE_dialogMsgScale=.052
IDE_dialogMsgPad=.3
IDE_msgScale=IDE_statusBarHeight*.7

IDE_tabsNstatusBarBGgetColor=lambda:(IDE_COLOR_tabsNstatusBar[0],IDE_COLOR_tabsNstatusBar[1],IDE_COLOR_tabsNstatusBar[2],.8)
# scripts tab background
IDE_docsTabsBG=DirectFrame( parent=IDE_root,
    frameSize=(0,2*base.getAspectRatio(),-IDE_tabsHeight,0),
    frameColor=IDE_tabsNstatusBarBGgetColor(),
    pos=(-base.getAspectRatio(),0,1), enableEdit=0, suppressMouse=1)
IDE_docsTabsHandle=IDE_docsTabsBG.attachNewNode('')
IDE_docLocation=IDE_docsTabsBG.attachNewNode('fileLoc')
IDE_docLocation.setScale(IDE_frame,IDE_statusBarHeight*.7)
IDE_docLocation.setPos(0,-.5,-IDE_tabsHeight*1.8)
IDE_docLocation.setBin('tabBin',0)
IDE_docsTabsBG.setTransparency(TransparencyAttrib.MAlpha)
# status bar
IDE_SB_shdTex=loader.loadTexture('LC-shd.png')
IDE_SB_litTex=loader.loadTexture('LC-lit.png')
for t in (IDE_SB_shdTex,IDE_SB_litTex):
    t.setMinfilter(Texture.FTLinearMipmapLinear)
    t.setMagfilter(Texture.FTLinearMipmapLinear)
    t.setWrapU(Texture.WMClamp)
    t.setWrapV(Texture.WMClamp)
statusBar=DirectFrame( parent=IDE_root,frameSize=(0,2*base.getAspectRatio(),0,IDE_statusBarHeight),
    frameColor=IDE_tabsNstatusBarBGgetColor(),pos=(-base.getAspectRatio(),0,-1),enableEdit=0, suppressMouse=1)
statusBar.setTransparency(TransparencyAttrib.MAlpha)

IDE_SB_BGcards = NodePath('SB item background cards')
IDE_SB_BGcards.attachNewNode(DU.createUVRect(align=0)).setTexture(IDE_SB_shdTex)
lit = IDE_SB_BGcards.attachNewNode(DU.createUVRect(align=1,flipU=1))
lit.setX(1)
lit.setTexture(IDE_SB_litTex)
lit.setAlphaScale(.5) # to melt better with statusbar BG color, not always white
IDE_SB_BGcards.setScale(IDE_SB_bgSize,1,IDE_SB_bgSize)
IDE_SB_BGcards.flattenLight()
IDE_SB_createLCpos()
IDE_SB_createBookMarks()
IDE_SB_createMacroNotif()
IDE_SB_createErrorsNotif()
IDE_SB_createPreferencesButton()
IDE_SB_createPause()
IDE_SB_createMessageBar()
IDE_setMessage('Loading..... please wait')
IDE_arrangeStatusBar()


################################################################################
def IDE_CC_display(codes,attr='',objType=None,displayCC=True):
    global IDE_CC_objType
    for i in range(codes.count('')):
        codes.remove('')
    if IDE_CC_IMPdictName in codes:
       codes.remove(IDE_CC_IMPdictName)
    codesLen=len(codes)
    if not codesLen:
       if IDE_isInMode(MODE_completing):
          IDE_CC_cancel()
       return
    leadingUS=[]
    leadingUSidx=[]
    for i in range(codesLen):
        if codes[i][0]=='_':
           leadingUSidx.append(i)
    for i in reversed(leadingUSidx):
        leadingUS.append(codes.pop(i))
    codes+=reversed(leadingUS)
    IDE_CC_objType=objType
    IDE_availCodesList.clear()
    if not displayCC:
       IDE_availCodesList.setItems(codes)
       return
    if not IDE_isInMode(MODE_completing):
       IDE_setMode(MODE_completing)
       IDE_CC_root.show()
    if objType is None:
       IDE_CC_classText['text']='builtins'
    else:
       if objType==importLine_CC_TEMP or objType in list(importLine_CC_TEMP.__dict__.values()):
          objTypeText='Module'
       elif IDE_CC_isSnippet:
          objTypeText='snippet'
       elif type(objType) in CLASSTYPE:
          objTypeText=objType.__name__
       else:
          objTypeText=objType.__class__.__name__
       IDE_CC_classText['text']=objTypeText
    IDE_CC_attrText['text']=attr
    if codesLen:
       IDE_availCodesList.setDisplay( display=IDE_CC_createText(codes),
                                      scale=IDE_textScale,
                                      vertSpacing=IDE_lineheight,
                                      baseline2top=IDE_chars_maxBaseline2top)
       IDE_availCodesList.setItems(codes)
       IDE_availCodesList.highlightItem(0)
       IDE_availCodesList.Frame.setX(IDE_frame, IDE_availCodesList.calcX())
       IDE_CC_displayDesc(later=False) # display it right away

def IDE_CC_getArgSpec(obj,wrapWidth=None):
    try:
        args=inspect.getargspec(obj)
        if args:
           if type(args[0])==list:
              args=args[0]
           if 'self' in args:
              args.remove('self')
           objName=obj.__name__
           if objName=='__init__':
              objName=obj.__self__.__class__.__name__
           if wrapWidth is None:
              wrapWidth=IDE_frameColWidth-4
           CC_TW.width=wrapWidth-len(objName)
           return CC_TW.fill(', '.join(args))
    except:
        return ''

def IDE_CC_displayDesc(later=True):
    if later:
       taskMgr.removeTasksMatching(IDE_tasksName+'show_description')
       taskMgr.doMethodLater(.25,IDE_CC_displayDesc,IDE_tasksName+'show_description',extraArgs=[False])
       return

    taskMgr.remove(IDE_tasksName+'show_description')

    if not IDE_objDescHidden:
       if IDE_objDesc.Frame.isHidden():
          IDE_objDesc.show()
       IDE_objDesc.clear(retainDisplay=1)
       attrName=IDE_availCodesList.getSelectedItem()
       attr=None
       if IDE_CC_objType is not None:
          attr=GET_ITEM(IDE_CC_objType,attrName)
       else:
          for loc in IDE_CC_locs:
              if hasattr(loc,attrName):
                 attr=getattr(loc,attrName)
                 break
       if attr is not None:
          isInstanceMethod=type(attr) in (types.FunctionType,types.MethodType)
          isModule=type(attr)==types.ModuleType
          isClass=type(attr) in CLASSTYPE
          docStr=attr.__doc__
          if not docStr and hasattr(attr,'__init__'):
             docStr=attr.__init__.__doc__
          if not docStr and not isClass:
             docStr=inspect.getcomments(attr)
             docStr='' if not docStr else '%s\n'%docStr
             # don't load binary source
             if hasattr(attr,'__file__') and not os.path.splitext(attr.__file__)[1] in DYN_LIB_EXT:
                try:
                   srcFull=inspect.getsource(attr)  # get the source lines
                   trsh=srcFull.find('\n',IDE_CFG[CFG_CCmaxSrc])
                   docStr+=srcFull if trsh<0 else srcFull[ :srcFull[:trsh].rstrip().rfind('\n')]+'\n.'*3
                except:
                   # get the expected arguments
                   args=IDE_CC_getArgSpec(attr)
                   docStr='Arguments : (%s)'%args.replace('\n','\n'+' '*12) if args else ''
          elif isInstanceMethod or isClass:
             args=IDE_CC_getArgSpec(attr) # get the expected arguments
             if not args and hasattr(attr,'__init__'):
                args=IDE_inspectDefSource(attr.__init__) # get the expected arguments
                if args:
                   docStr=args+'\n\n'+(docStr if docStr else '')
             else:
                docStr='%s(%s)\n\n%s'%(attrName,args.replace('\n','\n'+' '*(len(attrName)+1)),docStr if docStr else '')
          docs = docStr.splitlines() if (docStr and type(docStr) in STRINGTYPE) else ['<not documented>']
          if IDE_CC_isSnippet:
             attrType='\n'
          else:
             attrType='TYPE : %s\n'%('Class' if isClass else attr.__class__.__name__)
          desc=[attrName,attrType,'\n']
          if not IDE_CC_isSnippet:
             modFile=''
             if isModule and hasattr(attr,'__file__'):
                modFile=attr.__file__
             elif (hasattr(attr,'__module__') and attr.__module__ in  sys.modules and hasattr(sys.modules[attr.__module__],'__file__')):
                modFile=sys.modules[attr.__module__].__file__
             if modFile: desc.insert(2,'FILE : %s\n'%modFile)
          #____________________________________
          if type(attr) in (int,float):
             desc.insert(2,'VALUE : %s\n'%attr)
          elif type(attr) in STRINGTYPE:
             strVal=['%s :\n'%('SNIPPET' if IDE_CC_isSnippet else 'VALUE')]+attr.splitlines()
             desc=desc[:2]+strVal+desc[2:]
          else:
             desc+=docs
          if isInstanceMethod:
             del desc[0] # no need to display its name
       else:
          desc=[attrName,'TYPE : identifier or Python keyword\n']
       desc_disp=IDE_CC_createText(desc,bold=0)
       desc_disp.setColorScale(IDE_COLOR_codeDesc,1)

       oldSelQuad=IDE_objDesc.canvas.find('**/selQuad')
       if not oldSelQuad.isEmpty(): oldSelQuad.removeNode()
       IDE_objDesc.setDisplay( display=desc_disp,
                               scale=IDE_textScale,
                               vertSpacing=IDE_lineheight,
                               selectable=0,
                               )
       IDE_objDesc.setItems(desc)
       desc_disp.setZ(-IDE_chars_maxBaseline2top*IDE_textScale[2])

def IDE_CC_accept(code=None):
    global IDE_CC_sttBegin,IDE_CC_sttEnd
    if code is None:
       code=IDE_availCodesList.getSelectedItem()
    if code is not None:
       if IDE_CC_isSnippet:
          # means no match, so insert it at cursor
          if IDE_CC_sttBegin==IDE_CC_sttEnd:
             IDE_CC_sttBegin=IDE_CC_sttEnd=IDE_doc.column
          col=IDE_CC_sttBegin
       else:
          s=IDE_doc.File[IDE_doc.line]
          col=0
          if s:
             for i in range(IDE_CC_sttBegin-1,-1,-1):
                 if (
                    s[i] in string.whitespace or
                    s[i] in myPunctuation
                    ):
                    col=i+1
                    break
       IDE_doc.groupHistoryOn=False
       IDE_doc.column=col
       if IDE_CC_sttEnd-col:
          IDE_delChar(IDE_CC_sttEnd-col,completion=False)
       if IDE_CC_isSnippet:
          code,snipSel=SNIPPETS[code]
          snipSelActive=snipSel[0]-snipSel[1]
          tilEnd=code[:snipSel[1]]
          tilEndSplit=tilEnd.split('\n')
          snipSelEndLine=IDE_doc.line+tilEnd.count('\n')
          snipSelEndCol=IDE_doc.column+(len(tilEndSplit[-1]) if tilEndSplit else 0)
          if snipSelActive:
             tilStart=code[:snipSel[0]]
             tilStartSplit=tilStart.split('\n')
             snipSelStartLine=IDE_doc.line+tilStart.count('\n')
             snipSelStartCol=IDE_doc.column+(len(tilStartSplit[-1]) if tilStartSplit else 0)
       IDE_paste(code,processImp=True)
       if IDE_CC_isSnippet:
          IDE_doc.line,IDE_doc.column=snipSelEndLine,snipSelEndCol
          if snipSelActive:
             IDE_doc.isSelecting=True
             IDE_doc.blockStartLine,IDE_doc.blockStartCol=snipSelStartLine,snipSelStartCol
             IDE_updateBlock()
          IDE_updateCurPos()
          __exposeCurrentLine()
    IDE_CC_cancel()

def IDE_objDesc_RMBdown(mwp):
    codeDesc=IDE_objDesc.getItems()
    IDE_removeAnyMenuNcallTip()
    mposR2D=base.mouseWatcherNode.getMouse()
    mpos=IDE_objDesc.canvas.getRelativePoint(render2dp,Point3(mposR2D[0],0,mposR2D[1]))
    z=min(len(codeDesc)-1,-int(mpos[2]/(IDE_lineheight*IDE_textScale[2])))
    oldSelQuad=IDE_objDesc.canvas.find('**/selQuad')
    if not oldSelQuad.isEmpty(): oldSelQuad.removeNode()
    selQuad=IDE_REALblock.copyTo(IDE_objDesc.canvas,10)
    selQuad.setName('selQuad')
    selQuad.setColorScale(1,1,1,1)
    selQuad.setScale(IDE_textScale)
    selQuad.setZ(-z*IDE_lineheight*IDE_textScale[2])
    selQuad.setSx(len(codeDesc[z])*IDE_textScale[0])
    objDescPopupMenu = PopupMenu(
       parent=IDE_overlayParent,
       buttonThrower=IDE_BTnode,
       items=(
         ('_Copy line','IDE_copy.png',IDE_objDesc_copyDesc,codeDesc[z]),
         ('Copy _all','IDE_copy.png',IDE_objDesc_copyDesc,'\n'.join(codeDesc)),
       ),
       #~ font=IDE_FONT_digitalStrip, baselineOffset=-.35,
       #~ scale=IDE_statusBarHeight*.55, itemHeight=1.2,
       font=IDE_FONT_medrano, baselineOffset=-.27,
       scale=IDE_statusBarHeight*.65, itemHeight=1.05,
       leftPad=.2, separatorHeight=.45,
       underscoreThickness=2,
       BGColor=(.3,.3,.2,.9),
       BGBorderColor=(.8,.3,0,1),
       separatorColor=(1,1,1,1),
       frameColorHover=(1,.8,.3,1),
       frameColorPress=(0,1,0,1),
       textColorReady=(1,1,1,1),
       textColorHover=(0,0,0,1),
       textColorPress=(0,0,0,1),
       textColorDisabled=(.45,.45,.45,1),
       minZ=IDE_calcMenuMinZ()
    )
    objDescPopupMenu.menu.setBin('gaugeBin',1)

def IDE_objDesc_copyDesc(text):
    oldSelQuad=IDE_objDesc.canvas.find('**/selQuad')
    if not oldSelQuad.isEmpty(): oldSelQuad.removeNode()
    IDE_copy(text)

def IDE_processMissingFiles(missingFiles):
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_chooseRecentFiles)

    frame = wx.Frame(None, -1, 'Missing Files')
    frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
    panel = wx.Panel(frame)

    missingFilesSizer = wx.BoxSizer(wx.VERTICAL)
    actionsSizer = wx.BoxSizer(wx.HORIZONTAL)

    missingFilesText = wx.StaticText(panel, -1, 'These file(s) could not be found :')
    missingFilesList = SortableListCtrl(panel,-1,size=(440,415), images=LCimageList,
      style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
    missingFilesList.InsertColumn(0, 'Name',wx.LIST_FORMAT_LEFT,150)
    missingFilesList.InsertColumn(1, 'Location',wx.LIST_FORMAT_LEFT,270)
    dirsNfiles=(list(reversed(os.path.split(p))) for p in missingFiles)
    missingFilesList.initSorter(dirsNfiles)
#     textColor=(0,0,0)
#     for i in range(len(missingFiles)):
#         missingFilesList.SetItemTextColour(i,textColor)
    for i in range(len(missingFiles)):
        missingFilesList.Select(i,1)
    missingFilesList.SetFocus()

    retryOpenFilesBtn = wx.Button(panel, -1, '&Retry Open')
    retryOpenFilesBtn.Bind(wx.EVT_BUTTON,Functor(IDE_openMissingFiles,missingFiles,missingFilesList))
    retryOpenFilesBtn.SetFocus()

    cancelBtn = wx.Button(panel, -1, "I don't &care")
    cancelBtn.Bind(wx.EVT_BUTTON,Functor(IDE_closeWxInterface,frame))

    actionsSizer.Add(retryOpenFilesBtn, 0, wx.ALL|wx.ALIGN_CENTER, 5)
    actionsSizer.Add(cancelBtn, 0, wx.ALL|wx.ALIGN_CENTER, 5)

    missingFilesSizer.Add(missingFilesText, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    missingFilesSizer.Add(missingFilesList, 0, wx.ALL|wx.ALIGN_CENTER|wx.EXPAND, 5)
    missingFilesSizer.Add(actionsSizer, 0, wx.ALIGN_CENTER, 5)

    panel.SetSizer(missingFilesSizer)
    missingFilesSizer.Fit(frame)
    missingFilesSizer.SetSizeHints(frame)
    # handles navigational wx events
    if WIN:
       for c in getWxSizerWidgets(missingFilesSizer):
           c.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)
    frame.Center()
    frame.Show()

def IDE_openMissingFiles(missingFiles,FList,e):
    sel=[missingFiles[FList.GetItemData(i)] for i in range(len(missingFiles)) if FList.IsSelected(i)]
    # closes the window
    IDE_closeWxInterface(e.GetEventObject().GetGrandParent())
    IDE_openFiles(sel)

def IDE_openFilesFromSocket(files):
    files=GET_ITEMS_FROM_ARG(files)
    if IDE_root.isHidden(): # restores IDE if it's not active
       IDE_goBackToIDE()
    IDE_removeAnyMenuNcallTip()
    lastDoc=IDE_doc
    lastMode=IDE_getMode() if IDE_doc else None
    IDE_openFiles(files)
    if lastMode!=None and lastMode not in MODE_activeOrCompleting:
       lastDoc.setDocActive()
       IDE_setMode(lastMode)
    wp=WindowProperties()
    wp.setForeground(1)
    base.win.requestProperties(wp)

def IDE_openFiles(files,task=None):
    global IDE_doc, IDE_lastMode, IDE_recentFiles
    if type(files) in STRINGTYPE:
       manualOpen=False # it means the file opening is done by the IDE,
                        # ie. when an error occurs
       files=[files]
    else:
       manualOpen=True
    #~ files = [f for f in files if os.path.isfile(f)]
    #~ if not files:
       #~ IDE_setMode(IDE_lastMode)
       #~ return
    notFound = [f for f in files if not (os.path.exists(f) and os.path.isfile(f))]
    files = orderedDifference(files,notFound)
    # if it's already opened, remove it from the load list
    opened = None
    for d in IDE_documents:
        if d.FullPath in files:
           opened = IDE_documents.index(d)
           files.remove(d.FullPath)
    prevNumDocs = len(IDE_documents)
    invalidFiles = []

    if files:
       IDE_hideSGB()
       IDE_gauge.reset()
       IDE_gauge.show()
       filesSizes=[os.path.getsize(d) for d in files]
       filesSizes.reverse()
       totalSize=sum(filesSizes)
       # if files size is big enough, pause the scene to gain extra speed
       scenePaused=totalSize>30000 and not IDE_isScenePaused
       if scenePaused:
          IDE_toggleSceneActive()
       renderFrame(2)
       currFilesSize=0
       if UPDATE_RECENT_FILES:
          IDE_recentFiles=orderedDifference(IDE_recentFiles,files)
          # inserts the opened files to the recently opened files list
          IDE_recentFiles=(files+IDE_recentFiles)[:IDE_CFG[CFG_recentFilesLimit]]
       globalClock.setMode(ClockObject.MNormal)
       numFs=len(files)
       for d in files:
           IDE_setMessage('Loading %s file(s)..... please wait'%numFs)
           numFs-=1
           currSize=float(filesSizes.pop())
           IDE_gauge.setText(os.path.basename(d))
           renderFrame(2)
           progressRange=currSize/totalSize if currSize else 0
           IDE_documents.append(IDE_document(d,progressRange,reset=0))
           IDE_arrangeDocsTabs()
           doc=IDE_documents[-1]
           if doc.valid:
              # at IDE startup, save the CWD and arguments
              if doc.FullPath==APP_mainFile and not UPDATE_RECENT_FILES: 
                 doc.preferedCWD=APP_CWD
                 doc.preferedArgs=APP_args
              # first time opened
              if doc.FullPath and (not doc.FullPath in IDE_filesProps):
                 IDE_filesProps[doc.FullPath]=[ os.path.getsize(doc.FullPath),
                                                os.stat(doc.FullPath)[stat.ST_MTIME],
                                                doc.line,
                                                doc.column,
                                                list(doc.markedColumns.items()),
                                                doc.canvasXpos,
                                                doc.canvasZpos/IDE_lineScale[2],
                                                doc.preferedCWD,
                                                doc.preferedArgs,
                                              ]
           else:
              invalidFiles.append(doc)
       IDE_setMessage(IDE_MSG_ready)
       IDE_gauge.set(1)
       IDE_step()
       IDE_gauge.hide()
       IDE_saveFilesList() # always saves files list after opening a file
       if manualOpen and (IDE_getMode() in ( MODE_active,
                                             MODE_noFile,
                                             MODE_pickFiles,
                                             MODE_starting
                                           )):
          IDE_setMode(MODE_active)
       IDE_lastMode=MODE_active
       if scenePaused: # resumes scene if it was paused due to files size limit
          IDE_toggleSceneActive()
    elif opened is not None:
       prevNumDocs=opened
       IDE_setMode(IDE_lastMode)
    elif notFound: # all files not found
       print('NO FILE FOUND', file=IDE_DEV)
       IDE_processMissingFiles(notFound)
       return
    else: # not opening any file
       IDE_setMode(IDE_lastMode)
       return
    IDE_documents[prevNumDocs].setDocActive(arrangeTabs=1)
    if invalidFiles:
       names=''
       for d in invalidFiles:
           names+='%s"%s"'%(', '*(len(names)>0),d.FileName)
           IDE_doCloseDoc(d)
       msg=createMsg('Binary files not loaded',bg=(1,0,0,.85))
       putMsg(msg,'bin files no loaded',2)
       IDE_setMessage('Binary files are not loaded : '+names)
    if notFound:
       IDE_processMissingFiles(notFound)

def IDE_setWindowForeground():
    # IF MINIMIZED, SETTING FOREGROUND HARD CRASHES ON LINUX :
    if not base.mainWinMinimized:
       wp=WindowProperties()
#        wp.setMinimized(0)
       wp.setForeground(1)
       base.win.requestProperties(wp)

def IDE_closeWxInterface(ce,crap=None,restoreMode=True):
    frame=ce.GetEventObject() if ce.__class__.__bases__[0]==wx.Event else ce
    frame.Destroy()
    wxApp.ProcessIdle() # to actually remove the frame, without events loop
    if restoreMode:
       IDE_setMode(IDE_lastMode)
    IDE_resetModifierButtons()
    if WIN:
       stopWxLoop()
    IDE_setWindowForeground()

def IDE_openRecentFiles(openedFiles,FList,e):
    recentFiles=orderedDifference(IDE_recentFiles,openedFiles)
    sel=[recentFiles[FList.GetItemData(i)] for i in range(len(recentFiles)) if FList.IsSelected(i)]
    # closes the window
    IDE_closeWxInterface(e.GetEventObject().GetGrandParent())
    WxStep() # gives it a chance to be fully closed before loading files
    IDE_openFiles(sel)

def IDE_openRecentFilesInterface():
    # don't include the already opened recent files, and the log file too
    openedFiles=[d.FullPath for d in IDE_documents if d.FullPath]
    recentFiles=orderedDifference(IDE_recentFiles,openedFiles)
    numOpened=len(IDE_recentFiles)-len(recentFiles)
    if not recentFiles:
       IDE_SOUND_notAvail.play()
       return
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_chooseRecentFiles)

    frame = wx.Frame(None, -1, 'Open Recent Files')
    frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
    panel = wx.Panel(frame)

    openRecentFilesSizer = wx.BoxSizer(wx.VERTICAL)

    openRecentFilesText = wx.StaticText(panel, -1, '%s Recent Files'%len(recentFiles))
    openRecentFilesText.SetFont(wxBigFont)
    numRecentFilesText = wx.StaticText(panel, -1, '%s already opened and not listed'%numOpened)

    lastFilesList = SortableListCtrl(panel,-1,size=(440,415), images=LCimageList,
      style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
    lastFilesList.InsertColumn(0, 'Name',wx.LIST_FORMAT_LEFT,150)
    lastFilesList.InsertColumn(1, 'Location',wx.LIST_FORMAT_LEFT,270)

    dirsNfiles=(list(reversed(os.path.split(p))) for p in recentFiles)
    lastFilesList.initSorter(dirsNfiles)
#     textColor=(0,0,0)
#     for i in range(len(recentFiles)):
#         lastFilesList.SetItemTextColour(i,textColor)
    lastFilesList.SetFocus()

    openRecentFilesBtn = wx.Button(panel, -1, "Bring 'em !")
    openRecentFilesBtn.SetFont(wxBigFont)
    openRecentFilesBtn.Bind(wx.EVT_BUTTON,Functor(IDE_openRecentFiles,openedFiles,lastFilesList))
    removeFilesBtn = wx.Button(panel, wx.ID_REMOVE)
    removeFilesBtn.Bind(wx.EVT_BUTTON,Functor(IDE_removeRecentFiles,openedFiles,openRecentFilesText,lastFilesList))

    openRecentFilesSizer.Add(openRecentFilesText, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    openRecentFilesSizer.Add(numRecentFilesText, 0,wx.BOTTOM|wx.ALIGN_CENTER, 5)
    openRecentFilesSizer.Add(lastFilesList, 0, wx.TOP|wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER|wx.EXPAND, 5)
    openRecentFilesSizer.Add(openRecentFilesBtn, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    openRecentFilesSizer.Add(removeFilesBtn, 0, wx.BOTTOM|wx.ALIGN_CENTER, 5)

    panel.SetSizer(openRecentFilesSizer)
    openRecentFilesSizer.Fit(frame)
    openRecentFilesSizer.SetSizeHints(frame)
    # handles navigational wx events
    if WIN:
       for c in getWxSizerWidgets(openRecentFilesSizer):
           c.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)
    frame.Center()
    frame.Show()

def IDE_removeRecentFiles(openedFiles,openRecentText,FList,e):
    if FList.GetSelectedItemCount():
       numFs=FList.GetSelectedItemCount()
       IDE_spawnWxModal( IDE_spawnWxYesNoDialog,(
           'Are you sure to remove %s file%s from the list ?'\
             %('this' if numFs==1 else 'these '+str(numFs),'s' if numFs>1 else ''),
           IDE_doRemoveRecentFiles,[openedFiles,openRecentText,FList,e])
           )

def IDE_doRemoveRecentFiles(result):
    global IDE_recentFiles
    if not result: return
    openedFiles,openRecentText,FList,e=result
    recentFiles=orderedDifference(IDE_recentFiles,openedFiles)
    sel=[recentFiles[FList.GetItemData(i)] for i in range(len(recentFiles)) if FList.IsSelected(i)]
    IDE_recentFiles=orderedDifference(IDE_recentFiles,sel)
    IDE_saveFilesList()
    recentFiles=orderedDifference(IDE_recentFiles,openedFiles)
    dirsNfiles=(list(reversed(os.path.split(p))) for p in recentFiles)
    FList.DeleteAllItems()
    FList.initSorter(dirsNfiles,init=False)
    #~ textColor=(0,0,0)
    #~ for i in range(len(recentFiles)):
        #~ FList.SetItemTextColour(i,textColor)
    if FList._col>-1:
       FList.SortListItems(FList._col,FList._colSortFlag[FList._col])
       FList.OnSortOrderChanged()
    FList.SetFocus()
    openRecentText.SetLabel('%s Recent Files'%len(recentFiles))

def IDE_spawnWxModal(method,args=None,e=None):
    wasActive=not IDE_isScenePaused
    if wasActive:
       IDE_toggleSceneActive() # pauses the scene while user uses the interface
       renderFrame(2)
    method(*args)
    if wasActive:
       IDE_safeStep() # gives taskMgr a chance to kick the paused tasks out of taskslist
       IDE_toggleSceneActive() # resumes the scene

def IDE_spawnWxErrorDialog(message):
    msgDlg = wx.MessageDialog(None,
         message=message,
         caption='Ooooops',
         style=wx.ICON_ERROR)
    msgDlg.ShowModal()
    msgDlg.Destroy()

def IDE_spawnWxInfoDialog(message):
    msgDlg = wx.MessageDialog(None,
         message=message,
         caption='Please pay attention',
         style=wx.ICON_INFORMATION)
    msgDlg.ShowModal()
    msgDlg.Destroy()

def IDE_spawnWxYesNoCancelDialog(message,callback,args=None):
    Mdlg = wx.MessageDialog(None,message,
         caption='Confirmation',style=wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION|wx.CENTER)
    res=Mdlg.ShowModal()
    Mdlg.Destroy()
    if res==wx.ID_CANCEL: return
    if args is None:
       func=Functor(callback,res)
    else:
       func=Functor(callback,args,res)
    func()

def IDE_spawnWxYesNoDialog(message,callback,args=None):
    Mdlg = wx.MessageDialog(None,message,
         caption='Please confirm',style=wx.YES_NO|wx.NO_DEFAULT|wx.ICON_QUESTION|wx.CENTER)
    res=Mdlg.ShowModal()
    Mdlg.Destroy()
    if res==wx.ID_CANCEL: return
    if res==wx.ID_NO:
       args=''
    callback(args)

def IDE_saveFileAs(fullpath,task=None):
    if not fullpath:
       IDE_setMode(IDE_lastMode)
       return
    # all OSes have overwrite confirmation dialog already, no need to use this
#     if os.path.exists(fullpath):
#        IDE_openYesNoDialog('This file already exists.\nOverwrite it ?',IDE_doSaveFileAs,fullpath)
#     else:
#        IDE_doSaveFileAs(fullpath,True)
    IDE_doSaveFileAs(fullpath,True)

def IDE_doSaveFileAs(fullpath,result):
    if not result:
       IDE_setMode(IDE_lastMode)
       return
    # if the old file is the main file, save the new path
    if IDE_doc.FullPath==APP_mainFile:
       M.APP_mainFile=fullpath
    IDE_doc.saveNew(fullpath)

def IDE_saveCurrFile():
    if IDE_doc==None:
       return
    IDE_doc.saveFile()


################################################################################
IDE_SYNTAX_builtin = [
   '__all__', '__bases__', '__builtin__', '__builtins__', '__class__',
   '__init__',
   'globals', 'locals', 'min', 'max', 'self',
   ]+PythonVars
IDE_SYNTAX_keyword = keyword.kwlist
################################################################################

# create FileDialog
# IDE_FileDialog=FileDialog(
#    initialPath=os.path.dirname(APP_mainFile),
#    initialMultiSelect=1,
#    parent=IDE_2Droot, # attach to this parent node
#    frameSize=(1.5,1.2), buttonTextColor=(1,1,1,1),
#    font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
#    commandOpen=IDE_openFiles, # user defined method, executed when user has selected the files,
#                               # receives the files
#    commandSave=IDE_saveFileAs, # user defined method, executed when user has selected the files,
#                               # receives the files
#    commandCancel=IDE_cancelFileDialog, # user defined method, executed when user cancels it
#    autoFocus=0, # initial auto view-focus of newly added item
#    colorChange=1,
#    colorChangeDuration=.7,
#    newItemColor=(0,1,0,1),
#    rolloverColor=(1,.8,.2,1),
#    suppressMouseWheel=1,  # 1 : blocks mouse wheel events from being sent to all other objects.
#                           #     You can scroll the window by putting mouse cursor
#                           #     inside the scrollable window.
#                           # 0 : does not block mouse wheel events from being sent to all other objects.
#                           #     You can scroll the window by holding down the modifier key
#                           #     (defined below) while scrolling your wheel.
#    modifier='control'  # shift/control/alt
#    )
# IDE_FileDialog.dialogFrame.setBin('dialogsBin',0)
# IDE_FileDialog.hide()

################################################################################
IDE_CC_codes_portion = .6
IDE_CC_codeDesc_portion = 1.-IDE_CC_codes_portion
c2x = IDE_statusBarHeight*4.75
c1x = IDE_statusBarHeight*.35
cy = IDE_statusBarHeight*.4
CCtextBGheight=cy*6
# creates ScrolledList for available codes
IDE_CC_root = IDE_2Droot.attachNewNode('CC root')
IDE_CC_root.hide()
CC_width = IDE_statusBarHeight*12
CC_height = lambda:IDE_frameHeight*IDE_CC_codes_portion-CCtextBGheight
IDE_availCodesListGetColor = lambda:(IDE_COLOR_codesListBG[0],IDE_COLOR_codesListBG[1],IDE_COLOR_codesListBG[2],IDE_CFG[CFG_CCopacity]*.01)
IDE_availCodesListFGgetColor = lambda:(IDE_COLOR_codesListFG[0],IDE_COLOR_codesListFG[1],IDE_COLOR_codesListFG[2],1)
IDE_availCodesList = ScrolledList(
    parent=IDE_CC_root, # attach to this parent node
    frameColor=IDE_availCodesListGetColor(),
    frameSize=(CC_width,CC_height()),
#     font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
#     font=IDE_defaultFont, itemScale=.042, itemTextScale=1, itemTextZ=0,
    vertScrollPos=1,
    thumbWidth=IDE_statusBarHeight*.5,
    thumbMinHeight=IDE_statusBarHeight*.8,
    command=IDE_CC_accept, # user defined method, executed when an item get selected,
                           # receiving extraArgs (which passed to addItem)
    # user defined method, executed when an item (single) clicked
    clickCommand=Functor(IDE_CC_displayDesc,False),
    autoFocus=0, # initial auto view-focus on newly added item
    colorChange=0,
    colorChangeDuration=.7,
    newItemColor=(0,1,0,1),
    rolloverColor=IDE_availCodesListFGgetColor(),
    suppressMouseWheel=1,  # 1 : blocks mouse wheel events from being sent to all other objects.
                           #     You can scroll the window by putting mouse cursor
                           #     inside the scrollable window.
                           # 0 : does not block mouse wheel events from being sent to all other objects.
                           #     You can scroll the window by holding down the modifier key
                           #     (defined below) while scrolling your wheel.
    modifier='control',  # shift/control/alt
    BTnode=IDE_BTnode
    )
IDE_availCodesList.calcX = lambda:clampScalar(0,IDE_frameWidth-CC_width-IDE_canvasThumbWidth,
   (IDE_CC_sttEnd+2)*IDE_all_chars_maxWidth*IDE_textScale[0]+IDE_canvas.getX())
IDE_availCodesList.calcZ = lambda:-CCtextBGheight
IDE_availCodesList.Frame.setPos(IDE_frame,0,1,IDE_availCodesList.calcZ())
IDE_availCodesList.Frame.setBin('dialogsBin',0)

CCtextBG = DirectFrame( parent=IDE_availCodesList.Frame,
   frameSize=(0,CC_width+IDE_canvasThumbWidth,cy*.1,CCtextBGheight*.95),
   frameColor=IDE_availCodesListGetColor(),enableEdit=0, suppressMouse=1)

OnscreenText(parent=IDE_availCodesList.Frame,
   text='Type           :', font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.75, pos=(c1x,cy*4.2),
   fg=(1,1,1,1),align=TextNode.ALeft)
IDE_CC_classText=OnscreenText(parent=IDE_availCodesList.Frame,
   text='', font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.75, pos=(c2x,cy*4.2),
   fg=(1,1,1,1),align=TextNode.ALeft,mayChange=1)
OnscreenText(parent=IDE_availCodesList.Frame,
   text='Mode            :', font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.675, pos=(c1x,cy*2.4),
   fg=(1,1,1,1),align=TextNode.ALeft)
IDE_CC_modeText=OnscreenText(parent=IDE_availCodesList.Frame,
   text=IDE_CC_MODE_desc[IDE_CC_MODE], font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.7, pos=(c2x,cy*2.4),
   fg=(0,1,0,1),align=TextNode.ALeft,mayChange=1)
OnscreenText(parent=IDE_availCodesList.Frame,
   text='looking for :', font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.7, pos=(c1x,cy*.7),
   fg=(1,1,1,1),align=TextNode.ALeft)
IDE_CC_attrText=OnscreenText(parent=IDE_availCodesList.Frame,
   text='', font=IDE_FONT_transmetals,
   scale=IDE_statusBarHeight*.75, pos=(c2x,cy*.7),
   fg=(1,.8,.2,1),align=TextNode.ALeft,mayChange=1)


# creates ScrolledList for object description
IDE_objDesc = ScrolledList(
    parent=IDE_CC_root, # attach to this parent node
    frameSize=( IDE_frameWidth-IDE_canvasThumbWidth,
                IDE_frameHeight*IDE_CC_codeDesc_portion),
    frameColor=IDE_availCodesListGetColor(),
#     font=None, itemScale=.04, itemTextScale=1, itemTextZ=0,
    vertScrollPos=0,
    thumbWidth=IDE_statusBarHeight*.5,
    thumbMinHeight=IDE_statusBarHeight*.8,
    autoFocus=0, # initial auto view-focus on newly added item
    optimize=0,
    colorChange=0,
    colorChangeDuration=.7,
    newItemColor=(0,1,0,1),
    rolloverColor=(1,1,1,1),
    suppressMouseWheel=1,  # 1 : blocks mouse wheel events from being sent to all other objects.
                           #     You can scroll the window by putting mouse cursor
                           #     inside the scrollable window.
                           # 0 : does not block mouse wheel events from being sent to all other objects.
                           #     You can scroll the window by holding down the modifier key
                           #     (defined below) while scrolling your wheel.
    modifier='control',  # shift/control/alt
    BTnode=IDE_BTnode
    )
IDE_objDesc.calcX = lambda:IDE_canvasThumbWidth*IDE_objDesc.Frame.getSx(statusBar)
IDE_objDesc.Frame.setX(statusBar, IDE_objDesc.calcX())
IDE_objDesc.calcZ = lambda:IDE_statusBarHeight+IDE_frameHeight*IDE_CC_codeDesc_portion
IDE_objDesc.Frame.setZ(statusBar, IDE_objDesc.calcZ())
IDE_objDesc.Frame.setBin('dialogsBin',0)
IDE_objDesc.Frame.bind(DGG.B3PRESS,IDE_objDesc_RMBdown)
IDE_objDesc.hide()
IDE_objDescHidden = True



def IDE_cancelResolutionChange():
    IDE_resolutionsList.hide()
    if IDE_isInMode(MODE_chooseResolution):
       IDE_setMode(IDE_lastMode)
def IDE_applyResolution(res=None):
    IDE_cancelResolutionChange()
    if res is None:
       res=IDE_resolutionsList.getSelectedItem()
    x,y = res.split(' x ')
    wp = WindowProperties()
    wp.setSize(int(x),int(y))
    base.win.requestProperties(wp)
    IDE_toggleFullscreen()

# creates ScrolledList for monitor resolutions
IDE_resolutionsList = ScrolledList(
    parent=IDE_2Droot,
    frameColor=IDE_availCodesListGetColor(),
    frameSize=(CC_width,CC_width),
#     font=None, itemScale=.045, itemTextScale=1, itemTextZ=0,
#     font=IDE_defaultFont, itemScale=.042, itemTextScale=1, itemTextZ=0,
    vertScrollPos=1,
    thumbWidth=IDE_statusBarHeight*.5,
    thumbMinHeight=IDE_statusBarHeight*.8,
    command=IDE_applyResolution,
    autoFocus=0,
    colorChange=0,
    newItemColor=(0,1,0,1),
    rolloverColor=IDE_availCodesListFGgetColor(),
    suppressMouseWheel=1,
    BTnode=IDE_BTnode
    )
# IDE_resolutionsList.Frame.setScale(IDE_scale)
IDE_resolutionsList.Frame.setBin('dialogsBin',0)
IDE_resolutionsList.noteBG = DirectFrame( parent=IDE_resolutionsList.Frame,
   frameSize=(0,CC_width+IDE_canvasThumbWidth,0,IDE_statusBarHeight*5),
   frameColor=Vec4(1,0,0,.85), enableEdit=0, suppressMouse=1)
Aligner.alignTo(IDE_resolutionsList.noteBG, IDE_resolutionsList.Frame, DGG.LL, DGG.UL, (0,IDE_statusBarHeight*.2))
IDE_resolutionsList.noteText = 'Current resolution\n(X)\nis not supported in fullscreen mode.\n\nPlease choose 1 of the following :'
IDE_resolutionsList.note = OnscreenText(parent=IDE_resolutionsList.noteBG,
   text=IDE_resolutionsList.noteText, font=IDE_FONT_medrano,
   scale=IDE_statusBarHeight*.65, fg=(0,0,0,1))
Aligner.alignTo(NodePath(IDE_resolutionsList.note), IDE_resolutionsList.noteBG, DGG.C)
IDE_resolutionsList.Frame.hide()

################################################################################

base.setFrameRateMeter(1)
# sets frameRateMeter's viewport sort order to a high integer value
if base.frameRateMeter:
   base.frameRateMeter.getDisplayRegion().setSort(MAXINT)
# sets render2dp's viewport sort order exactly below the frameRateMeter
[base.win.getDisplayRegion(i) for i in range(base.win.getNumDisplayRegions()) \
   if not base.win.getDisplayRegion(i).getCamera().isEmpty() and \
   base.win.getDisplayRegion(i).getCamera()==base.cam2dp][0].setSort(MAXINT-2)
# let the blank IDE displayed during startup,
# before creating the letters and loading the files, which takes a while
IDE_2Droot.hide()
IDE_safeStep()
IDE_safeStep()
# pause user's scene
IDE_toggleSceneActive()
# and render the blank IDE
renderFrame()
#fixedSizeWinWP=WindowProperties()
#fixedSizeWinWP.setFixedSize(1)
#base.win.requestProperties(fixedSizeWinWP)

################################################################################

#~ VCTarray = GeomVertexArrayFormat()
#~ VCTarray.addColumn(InternalName.make('vertex'), 3, Geom.NTFloat32, Geom.CPoint)
#~ VCTarray.addColumn(InternalName.make('color'), 3, Geom.NTFloat32, Geom.CColor)
#~ VCTarray.addColumn(InternalName.make('texcoord'), 2, Geom.NTFloat32, Geom.CTexcoord)
#~ VCTformat = GeomVertexFormat()
#~ VCTformat.addArray(VCTarray)
#~ VCTVtxFormat = GeomVertexFormat.registerFormat(VCTformat)

################################################################################
# IDE_defaultFontName='Courier New.ttf'
# IDE_defaultFontName='Courier New Bold.ttf'
# IDE_defaultFontName='Monospace.ttf'
# IDE_defaultFontName='Monospace Bold.ttf'
IDE_defaultFontName='lucon.ttf'

IDE_fontPageSize=512
IDE_fontPixelsPerUnit=IDE_CFG[CFG_WSfontPPU]
IDE_fontTexMargin=IDE_CFG[CFG_WSfontSpacing]
IDE_defaultFont=loader.loadFont(IDE_defaultFontName)
IDE_textScale=Vec3(1)
IDE_getFrameColWidth=lambda:IDE_frameWidth/(IDE_textScale[0]*IDE_all_chars_maxWidth)
IDE_CHARS_lettersProps={}
IDE_normal_chars={}
ASCIIchars=[chr(i) for i in range(33,128)]#+[ws for ws in string.whitespace]
blankASCIIchars=difference([chr(i) for i in range(256)],ASCIIchars)

def IDE_setupWSfont():
#     global IDE_chars_maxBaseline2top,IDE_fontTexActual,IDE_normal_chars,
#       IDE_normal_chars_maxWidth,IDE_normal_chars_maxHeight,IDE_CHARS_lettersProps,
#       IDE_normal_chars_tex,IDE_bold_chars_maxWidth,IDE_bold_chars_maxHeight,
#       IDE_all_chars_maxWidth,IDE_all_chars_maxHeight,
#       IDE_lineheight,IDE_chars_offset,
    IDE_defaultFont.clear()
    IDE_defaultFont.setPointSize(10)
    IDE_defaultFont.setPixelsPerUnit(IDE_fontPixelsPerUnit)
    IDE_defaultFont.setScaleFactor(1)
    IDE_defaultFont.setPageSize(IDE_fontPageSize,IDE_fontPageSize)
    # use larger quad to rescue the texcoord which might be compromised upon flattenStrong
    IDE_defaultFont.setTextureMargin(IDE_fontTexMargin)
    IDE_defaultFont.setMinfilter(Texture.FTNearest)
    IDE_defaultFont.setMagfilter(Texture.FTNearest)
    IDE_defaultFont.setNativeAntialias(0)

    #________________________________________________________
    # IDE_defaultBoldFontName='Courier New Bold.ttf'
    # IDE_defaultBoldFontName=IDE_defaultFontName
    # IDE_defaultBoldFont=loader.loadFont(IDE_defaultBoldFontName)
    # IDE_defaultBoldFont.setPageSize(IDE_fontPageSize,IDE_fontPageSize)
    ################################################################################
    M.IDE_chars_maxBaseline2top=0
    M.IDE_fontTexActual=.385
    IDE_CHARS_lettersProps.clear()
    IDE_normal_chars.clear()
    M.IDE_normal_chars_maxWidth=M.IDE_normal_chars_maxHeight=0
    InternalName_Texcoord=InternalName.make('texcoord')
    loadPrcFileData('','notify-level-text fatal')
    for c in ASCIIchars:
        TX=TextNode(c)
        TX.setFont(IDE_defaultFont)
        TX.setText(c)
        TN=NodePath(TX.generate())
        TNP=TN.getChild(0)
        validChar=False
        if TNP.node().getNumGeoms():
           vd=TNP.node().getGeom(0).getVertexData()
           if vd.hasColumn(InternalName_Texcoord):
              validChar=True
        if validChar:
           IDE_normal_chars[c]=TNP
           TNP.setTexOffset(TextureStage.getDefault(), 0.4/IDE_fontPageSize, -0.4/IDE_fontPageSize)
           TNP.setName(c)
           TB1,TB2=TNP.getTightBounds()
           TB=TB2-TB1
           M.IDE_normal_chars_maxWidth=max(IDE_normal_chars_maxWidth,TB[0])
           M.IDE_normal_chars_maxHeight=max(IDE_normal_chars_maxHeight,TB[2])
           M.IDE_chars_maxBaseline2top=max(IDE_chars_maxBaseline2top,TB2[2])
           vVR=GeomVertexReader(vd,'vertex')
           tVR=GeomVertexReader(vd,'texcoord')
           vVR.setColumn(0)
           vtxPos=(
             vVR.getData3f(),
             vVR.getData3f(),
             vVR.getData3f(),
             vVR.getData3f(),
           )
           tVR.setColumn(1)
           vtxUV=(
             tVR.getData2f(),
             tVR.getData2f(),
             tVR.getData2f(),
             tVR.getData2f(),
           )
           if IDE_TDExtensionAvail:
              IDE_TextDrawer.storeLetterProps(ord(c),*(vtxPos+vtxUV))
           IDE_CHARS_lettersProps[c]=(vtxPos,vtxUV)
        else:
           IDE_CHARS_lettersProps[c]=None
    for c in blankASCIIchars:
        IDE_CHARS_lettersProps[c]=None
        IDE_normal_chars[c]=NodePath(c)
    M.IDE_normal_chars_maxWidth*=IDE_fontTexActual
    M.IDE_normal_chars_tex=IDE_defaultFont.getPage(0)
    IDE_normal_chars_tex.setMinfilter(Texture.FTNearest)
    IDE_normal_chars_tex.setMagfilter(Texture.FTNearest)

    # print>>IDE_DEV, 'font num pages:',IDE_defaultFont.getNumPages()
    # print>>IDE_DEV, IDE_normal_chars.keys()
    # print>>IDE_DEV, len(IDE_normal_chars)
    # print>>IDE_DEV, 'IDE_normal_chars_maxWidth :',IDE_normal_chars_maxWidth
    # print>>IDE_DEV, 'IDE_normal_chars_maxHeight:',IDE_normal_chars_maxHeight
    ################################################################################
    # IDE_bold_chars={}
    M.IDE_bold_chars_maxWidth=0
    M.IDE_bold_chars_maxHeight=0
    # # for c in string.printable+' ':
    # for c in [chr(i) for i in range(256)]:
    #     TN=TextNode(c)
    #     TN.setFont(IDE_defaultBoldFont)
    #     TN.setText(c)
    #     TNP=NodePath(TN.generate()).getChild(0)
    #     IDE_bold_chars[c]=TNP
    #     TB1,TB2=TNP.getTightBounds()
    #     TB=TB2-TB1
    #     IDE_bold_chars_maxWidth=max(IDE_bold_chars_maxWidth,TB[0])
    #     IDE_bold_chars_maxHeight=max(IDE_bold_chars_maxHeight,TB[2])
    #     IDE_chars_maxBaseline2top=max(IDE_chars_maxBaseline2top,TB2[2])
    # IDE_bold_chars_maxWidth*=IDE_fontTexActual
    # print>>IDE_DEV, IDE_bold_chars.keys()
    # print>>IDE_DEV, len(IDE_bold_chars)
    # print>>IDE_DEV, 'IDE_bold_chars_maxWidth :',IDE_bold_chars_maxWidth
    # print>>IDE_DEV, 'IDE_bold_chars_maxHeight:',IDE_bold_chars_maxHeight
    ################################################################################
    loadPrcFileData('','notify-level-text warning')
    M.IDE_all_chars_maxWidth=max(IDE_normal_chars_maxWidth,IDE_bold_chars_maxWidth)
    M.IDE_all_chars_maxHeight=max(IDE_normal_chars_maxHeight,IDE_bold_chars_maxHeight)
    M.IDE_lineheight=IDE_all_chars_maxHeight*(1-IDE_fontTexActual)*1.1
    M.IDE_chars_maxBaseline2top*=(1-IDE_fontTexActual)
    M.IDE_chars_offset=IDE_all_chars_maxWidth*(1-IDE_fontTexActual)
    if IDE_TDExtensionAvail:
       IDE_TextDrawer.setOffsetAndWidth(-IDE_chars_offset,IDE_all_chars_maxWidth)
    
    M.IDE_textScale=Vec3(IDE_winORatio*IDE_fontPixelsPerUnit/(.5*IDE_winX*IDE_scale[0]), 1.0, IDE_fontPixelsPerUnit/(.5*IDE_winY*IDE_scale[2]))
    M.IDE_lineScale=IDE_textScale*IDE_lineheight
    IDE_lineScale.setY(1)
#     print>>IDE_DEV, 'IDE_textScale :',IDE_textScale
#     print>>IDE_DEV, 'IDE_lineheight :',IDE_lineheight
#     print>>IDE_DEV, 'IDE_lineScale :',IDE_lineScale
    IDE_new_canvas.setZ(-IDE_chars_maxBaseline2top*IDE_textScale[2])
    M.IDE_canvas_leftBgXR2D=-1.+IDE_textScale[0]*IDE_winORatio*1.1-IDE_canvas_minXR2D
    M.IDE_frameColWidth=IDE_getFrameColWidth()

IDE_setupWSfont()

logTexGenText='Log text texture is %s.\n%s it now.....'
if os.path.exists(IDE_logOverSceneTexPath):
   isLogTexObsolete = os.path.getmtime(IDE_logOverSceneTexPath) < IDE_textTexturesUpdateDate
   msgText=logTexGenText%('obsolete','Updating')
else:
   isLogTexObsolete=True
   msgText=logTexGenText%('not found','Creating')

def createLogTextTexture(msgText):
    if isLogTexObsolete:
       msg=createMsg(msgText,bg=(0,1,0,.85))
       putMsg(msg,'',0)
       renderFrame(2)
       msg.removeNode()
       textBGimage=PNMImage()
       textFGimage=PNMImage()
       page=IDE_normal_chars_tex
       page.store(textFGimage)
       page.store(textBGimage)
       textBGimage.addAlpha()
       for i in range(7):
           textBGimage.gaussianFilter()
       for x in range(textFGimage.getXSize()):
           for y in range(textFGimage.getYSize()):
               textBGimage.setAlpha(x,y,textBGimage.getRed(x,y)*7)
       textBGimage.blendSubImage(textFGimage,0,0)
       textBGimage.write(Filename.fromOsSpecific(IDE_logOverSceneTexPath))
       renderFrame()
    if hasattr(M,'IDE_logOverSceneTex'):
       IDE_logOverSceneTex.reload()
    else:
       M.IDE_logOverSceneTex=loader.loadTexture(IDE_logOverSceneTexName)
    IDE_logOverSceneTex.setMinfilter(Texture.FTNearest)
    IDE_logOverSceneTex.setMagfilter(Texture.FTNearest)
createLogTextTexture(msgText)

# CM=CardMaker('')
# card=IDE_2Droot.attachNewNode(CM.generate(),sort=2000)
# card.setTexture(IDE_defaultFont.getPage(0))
# card.setTransparency(TransparencyAttrib.MAlpha)
# card.setPos(-1,0,-.5)
#
# CM=CardMaker('')
# card=IDE_2Droot.attachNewNode(CM.generate(),sort=2000)
# card.setTexture(IDE_defaultBoldFont.getPage(0))
# card.setTransparency(TransparencyAttrib.MAlpha)
# card.setPos(0,0,-.5)

################################################################################
def IDE_updateCallTipAlpha():
    if IDE_doc and not IDE_doc.callTipParent.isHidden():
       pos=IDE_textCursor.getPos(IDE_doc.callTipBG)
       f=IDE_doc.callTipBG['frameSize']
       a=.2 if f[0]<pos[0]<f[1] and f[2]<pos[2]<f[3]+IDE_lineheight else 1
       IDE_doc.callTipParent.setAlphaScale(a)

def IDE_gotoNextLine(num=1,isSelecting=False,center=False):
    # this is to avoid continuous scrolling after releasing the button,
    # when the keypress repeat is so short
    if mustBeHalted(): return
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    IDE_setSelection(isSelecting)
    IDE_doc.line = clampScalar(0,IDE_doc.numLines-1,IDE_doc.line+num)
    maxCol=len( IDE_doc.File[IDE_doc.line].rstrip() )
    IDE_doc.column=clampScalar(0,maxCol,IDE_doc.lastMaxColumn)
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine(center=center,moveDir=-1)
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_nextLine,num,isSelecting],False)
    if num>1:
       IDE_forceRender()

def IDE_gotoPrevLine(num=1,isSelecting=False,center=False):
    # this is to avoid continuous scrolling after releasing the button,
    # when the keypress repeat is so short
    if mustBeHalted(): return
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    IDE_setSelection(isSelecting)
    IDE_doc.line=clampScalar(0,IDE_doc.numLines-1,IDE_doc.line-num)
    maxCol=len( IDE_doc.File[IDE_doc.line] )-1
    IDE_doc.column=clampScalar(0,maxCol,IDE_doc.lastMaxColumn)
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine(center=center,moveDir=1)
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_prevLine,num,isSelecting],False)
    if num>1:
       IDE_forceRender()

def IDE_gotoNextColumn(num=1,isSelecting=False):
    IDE_setSelection(isSelecting)
    maxCol=len( IDE_doc.File[IDE_doc.line].rstrip('\n') )
    IDE_doc.column=clampScalar(0,maxCol,IDE_doc.column+num)
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_nextColumn,num,isSelecting],False)

def IDE_gotoPrevColumn(num=1,isSelecting=False):
    IDE_setSelection(isSelecting)
    maxCol=len( IDE_doc.File[IDE_doc.line].rstrip('\n') )
    IDE_doc.column=clampScalar(0,maxCol,IDE_doc.column-num)
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_prevColumn,num,isSelecting],False)

def IDE_gotoFront(isSelecting=False, forceReal=False, exposeLine=True):
    IDE_setSelection(isSelecting)
    if forceReal:
       IDE_doc.column=0
    else:
       l=IDE_doc.File[IDE_doc.line]
       col=[ 0, l.find(l.lstrip()) ] if IDE_CFG[CFG_realLineStart] else [ l.find(l.lstrip()), 0 ]
       IDE_doc.column=col[ IDE_doc.column==col[0] ]
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    if exposeLine:
       __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_lineStart,isSelecting],False)

def IDE_gotoBack(isSelecting=False, forceReal=False, exposeLine=True):
    IDE_setSelection(isSelecting)
    l=IDE_doc.File[IDE_doc.line].rstrip('\n')
    if forceReal:
       IDE_doc.column=len(l)
    else:
       col=[ len(l), len(l.rstrip()) ] if IDE_CFG[CFG_realLineEnd] else [ len(l.rstrip()), len(l) ]
       IDE_doc.column=col[ IDE_doc.column==col[0] ]
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    if exposeLine:
       __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_lineEnd,isSelecting],False)

def IDE_gotoDocBeg(isSelecting=False):
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    IDE_setSelection(isSelecting)
    IDE_doc.line=0
    IDE_doc.column=0
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_docStart,isSelecting],False)

def IDE_gotoDocEnd(isSelecting=False):
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    IDE_setSelection(isSelecting)
    IDE_doc.line=IDE_doc.numLines-1
    IDE_gotoBack(isSelecting)
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_docEnd,isSelecting],False)

def IDE_gotoPageBeg(isSelecting=False):
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    canvasZ=IDE_canvas.getZ()
    IDE_setSelection(isSelecting)
    pageLineBeg=int(canvasZ/IDE_lineScale[2])
    if pageLineBeg*IDE_lineScale[2]<canvasZ/IDE_lineScale[2]:
       pageLineBeg+=1
    IDE_doc.line=pageLineBeg
    IDE_doc.column=0
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_pageStart,isSelecting],False)

def IDE_gotoPageEnd(isSelecting=False):
    if not isSelecting:
       if IDE_doc.processImports(IDE_doc.line,IDE_doc.line+1): return
    canvasZ=IDE_canvas.getZ()
    IDE_setSelection(isSelecting)
    pageLineEnd=min(int((IDE_canvas.getZ()+IDE_frameHeight)/IDE_lineScale[2]-1.5),IDE_doc.numLines-1)
    IDE_doc.line=pageLineEnd
    IDE_doc.column=0
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_pageEnd,isSelecting],False)

def IDE_areSameType(chars):
    c1,c2=chars
    c1Type=(c1 in myLettersDigits, c1 in myPunctuation, c1 in string.whitespace)
    c2Type=(c2 in myLettersDigits, c2 in myPunctuation, c2 in string.whitespace)
    return c1Type==c2Type

def IDE_gotoNextWord(isSelecting=False,exposeLine=True):
    IDE_setSelection(isSelecting)
    maxCol=len( IDE_doc.File[IDE_doc.line].rstrip('\n') )
    if IDE_doc.column==maxCol:
       return
    cch=IDE_doc.File[IDE_doc.line][IDE_doc.column]
    seq=IDE_doc.File[IDE_doc.line][IDE_doc.column+1:]
    minC=100000
    if cch in string.whitespace:
       for s in myLettersDigits+myPunctuation:
           c=seq.find(s)
           if c<minC and c>=0:
              minC=c
    elif cch in myPunctuation:
       for s in myLettersDigits+string.whitespace:
           c=seq.find(s)
           if c<minC and c>=0:
              minC=c
    else:
       for s in myPunctuationWhitespace:
           c=seq.find(s)
           if c<minC and c>=0:
              minC=c
    if minC==100000:
       IDE_doc.column=maxCol
    else:
       IDE_doc.column=IDE_doc.column+1+minC
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    if exposeLine:
       __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_nextWord,isSelecting],False)

def IDE_gotoPrevWord(isSelecting=False,exposeLine=True):
    IDE_setSelection(isSelecting)
    if IDE_doc.column==0:
       return
    cch=IDE_doc.File[IDE_doc.line][IDE_doc.column-1]
    seq=IDE_doc.File[IDE_doc.line][:IDE_doc.column-1]
    maxC=0
    if cch in string.whitespace:
       for s in myLettersDigits+myPunctuation:
           c=seq.rfind(s)
           maxC=max(c,maxC)
    elif cch in myPunctuation:
       for s in myLettersDigits+string.whitespace:
           c=seq.rfind(s)
           maxC=max(c,maxC)
    else:
       for s in myPunctuationWhitespace:
           c=seq.rfind(s)
           maxC=max(c,maxC)
    if maxC==0:
       IDE_doc.column=0
    else:
       IDE_doc.column=maxC+1
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    if exposeLine:
       __exposeCurrentLine()
    IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_prevWord,isSelecting],False)

def IDE_adjustLineMarks(s,e,inc):
    nextMLs=[l for l in IDE_doc.markedLines if l>=s]
    if inc<0: # lines are deleted
       mustBeRemovedMLs=[l for l in nextMLs if l<e]
       for m in mustBeRemovedMLs:
           IDE_doc.markedLines.remove(m)
           del IDE_doc.markedColumns[m]
           IDE_doc.lineMarkParent.find(str(m)).removeNode()
       remainingMLs=difference(nextMLs,mustBeRemovedMLs)
    else: # lines are inserted
       remainingMLs=nextMLs
    # clear it only when removing lines. Inserting lines won't possibly remove any mark.
    if not IDE_doc.markedLines and inc<0:
       IDE_doClearAllLineMarks(1)
    if not remainingMLs:
       return
    Ldiff=inc*(e-s)
    Zdiff=inc*(s-e)*IDE_lineheight
    for m in remainingMLs:
        mark=IDE_doc.lineMarkParent.find(str(m))
        mark.setName(str(m+Ldiff))
        mark.setZ(mark,Zdiff)
    remainingMLs.sort()
    remaining1stIdx=IDE_doc.markedLines.index(remainingMLs[0])
    mustBeShifted=list(range(remaining1stIdx,remaining1stIdx+len(remainingMLs)))
    if Ldiff>=0:
       mustBeShifted.reverse()
    for r in mustBeShifted:
        l=IDE_doc.markedLines[r]
        IDE_doc.markedColumns[l+Ldiff]=IDE_doc.markedColumns.pop(l)
        IDE_doc.markedLines[r]+=Ldiff
    if remaining1stIdx and IDE_doc.markedLines[remaining1stIdx-1]==IDE_doc.markedLines[remaining1stIdx]:
       IDE_doc.lineMarkParent.find(str(IDE_doc.markedLines[remaining1stIdx])).removeNode()
       del IDE_doc.markedColumns[IDE_doc.markedLines.pop(remaining1stIdx)]

def IDE_updateLines(l=None,updateNext=False,forced=False,numStatic=1):
    if not UPDATE_DISPLAY or REPLACING: return
    if l is None:
       l=IDE_doc.line
    if IDE_doc.hilight:
#        print 'IDE_updateLines forced:',forced
       quoteChanged=IDE_doc.updateQuotedLines(l+1,forced=forced,numStatic=numStatic)
    else:
       quoteChanged=False
    __exposeCurrentLine()
#     print 'quoteChanged:',quoteChanged
    if UPDATE_DISPLAY or quoteChanged or forced:
       if l in IDE_doc.displayed:
          textLine=IDE_doc.displayed[l]
          # maybe shifted due to indent, so clear it
          textLine.setX(0)
       else:
          textLine=IDE_doc.textParent.attachNewNode(str(l))
          textLine.setZ(-l*IDE_lineheight)
          IDE_doc.displayed[l]=textLine
       isQuoted,color=IDE_doc.getLineQuotedNColor(l)
       color,isQuoted=IDE_doc.drawTextLine(l,textLine,color,isQuoted)
       if quoteChanged or updateNext:
          populatePage(startLine=l)

def IDE_delSelection():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    s=IDE_doc.File[IDE_doc.line]
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    # redirects to delChar if the selected text is EoL
    if startLine==endLine and s[startCol:endCol]=='\n':
       IDE_doc.isSelecting=False
       if IDE_doc.column>=len(s):
          IDE_doc.column-=1
       IDE_delChar(completion=False)
       return
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delSelection])
    if HISTORY_ON:
       if startLine==endLine: # a single line
          chars=s[startCol:endCol]
       else:                  # multiple lines
          chars=IDE_doc.File[startLine][startCol:]
          for l in range(startLine+1,endLine):
              chars+=IDE_doc.File[l]
          chars+=IDE_doc.File[endLine][:endCol]
       IDE_truncateHistory()
       IDE_doc.history.append( [EDIT_delSel,
                               [IDE_doc.line,IDE_doc.column,
                               IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                               startLine,startCol,
                               chars]] )
       IDE_doc.historyIdx+=1
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    if startLine==endLine: # a single line
       s=s[:startCol]+s[endCol:]
       IDE_doc.File[IDE_doc.line]=s
       if isLoadedFile:
          IDE_updateLines()
    else:                  # multiple lines
       left=IDE_doc.File[startLine]
       right=IDE_doc.File[endLine]
       s=left[:startCol]+right[endCol:]
       IDE_doc.File[startLine]=s
       nextL=startLine+1
       for crap in range(nextL,endLine+1):
           del IDE_doc.File[nextL]
           if isLoadedFile and IDE_doc.hilight:
              del IDE_doc.quoted[nextL]
       IDE_doc.line=startLine
       IDE_doc.numLines-=endLine-startLine
       # update
       if isLoadedFile:
          IDE_updateLines(updateNext=True)
          if UPDATE_DISPLAY:
             adjustCanvasLength(IDE_doc.numLines)
          IDE_adjustLineMarks(startLine,endLine,-1)
    IDE_doc.column=startCol
    IDE_doc.lastMaxColumn=IDE_doc.column
    if not isLoadedFile:
       return
    IDE_doc.isSelecting=False
    if UPDATE_DISPLAY:
       IDE_updateCurPos()
       # removes block quads
       IDE_updateBlock()
    if not UNDO_REPLACE:
       IDE_doc.setChangedStatus(1) # update isChanged attr

def IDE_delChar(num=1,completion=True):
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    if IDE_doc.isSelecting: ###### DELETES SELECTION
       IDE_delSelection()
    else:  ################## DELETES AT CURSOR
       l=IDE_doc.File[IDE_doc.line]
       if IDE_doc.line==IDE_doc.numLines-1 and IDE_doc.column==len(l):
          print('END OF FILE', file=IDE_DEV)
          return 0
       if l[IDE_doc.column]=='\n':
          s=l[:-1]+IDE_doc.File.pop(IDE_doc.line+1)
          IDE_doc.numLines-=1
          if isLoadedFile:
             IDE_doc.File[IDE_doc.line]=s
             if IDE_doc.hilight:
                del IDE_doc.quoted[IDE_doc.line+1]
             IDE_updateLines(updateNext=True)
             # update
             if UPDATE_DISPLAY:
                adjustCanvasLength(IDE_doc.numLines)
             IDE_adjustLineMarks(IDE_doc.line,IDE_doc.line+1,-1)
             num=1 # EDIT HISTORY must know that it's obviously 1, not 0
#           print>>IDE_DEV, 'EOL deleted'
       else:
          s=l[:IDE_doc.column]+l[IDE_doc.column+num:]
          IDE_doc.File[IDE_doc.line]=s
          IDE_updateLines()
       if not isLoadedFile:
          return
       if IDE_doc.recordMacro:
          IDE_addCommandToMacro([COM_delNextChar,num,False])
       if HISTORY_ON:
          chars=l[IDE_doc.column:IDE_doc.column+num]
          Hlen=IDE_truncateHistory()
          if Hlen and IDE_doc.history[-1][0]==EDIT_del and IDE_doc.groupHistoryOn:
             IDE_doc.history[-1][1][-1]+=chars
          else:
             IDE_doc.history.append( [EDIT_del,[IDE_doc.line,IDE_doc.column,chars]] )
             IDE_doc.historyIdx+=1
          # updates group history status
          if not IDE_doc.groupHistoryOn:
             IDE_doc.groupHistoryOn=True
       if IDE_doc.recordMacro:
          IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    IDE_updateCurPos()
    if not UNDO_REPLACE:
       IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()
    # code completion________________________________________________
    if completion:
       IDE_completion()

def IDE_delLineTail():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delLineTail])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    hasLF=IDE_doc.File[IDE_doc.line].rfind('\n')>-1
    chars=IDE_doc.File[IDE_doc.line][IDE_doc.column:len(IDE_doc.File[IDE_doc.line].rstrip('\n'))]
    if chars:
       if HISTORY_ON:
          IDE_truncateHistory()
          IDE_doc.history.append( [EDIT_delLineTail,
                                  [IDE_doc.line,IDE_doc.column,chars]] )
          IDE_doc.historyIdx+=1
       IDE_doc.File[IDE_doc.line]=IDE_doc.File[IDE_doc.line][:IDE_doc.column]+('\n'*hasLF)
    IDE_doc.isSelecting=False
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    if isLoadedFile:
       IDE_updateLines()
       IDE_updateCurPos()
       IDE_updateBlock()
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_delLineHead():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delLineHead])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    chars=IDE_doc.File[IDE_doc.line][:IDE_doc.column]
    if chars:
       if HISTORY_ON:
          IDE_truncateHistory()
          IDE_doc.history.append( [EDIT_delLineHead,
                                  [IDE_doc.line,IDE_doc.column,chars]] )
          IDE_doc.historyIdx+=1
       IDE_doc.File[IDE_doc.line]=IDE_doc.File[IDE_doc.line][IDE_doc.column:]
    IDE_doc.isSelecting=False
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    if isLoadedFile:
       IDE_updateLines()
       IDE_doc.column=IDE_doc.lastMaxColumn=0
       IDE_updateCurPos()
       IDE_updateBlock()
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_delWordTail():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delWordTail])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    lastColumn=IDE_doc.column
    lineLen=len(IDE_doc.File[IDE_doc.line])
    IDE_gotoNextWord()
#     if IDE_doc.column==lineLen and lineLen==0:
    if lineLen:
       if ( not (IDE_doc.column==lineLen and lineLen>0) and
            IDE_doc.File[IDE_doc.line][IDE_doc.column] in string.whitespace
          ):
             IDE_gotoNextWord()
       wordEnd=IDE_doc.column
       IDE_doc.column=lastColumn
       IDE_delChar(wordEnd-lastColumn)
    else:
       IDE_doc.column=lastColumn
    IDE_doc.lastMaxColumn=lastColumn
    IDE_updateCurPos()
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_delWordHead():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delWordHead])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    lastColumn=IDE_doc.column
    lineLen=len(IDE_doc.File[IDE_doc.line])
    IDE_gotoPrevWord()
    if lineLen and IDE_doc.File[IDE_doc.line][IDE_doc.column] in string.whitespace:
       IDE_gotoPrevWord()
    wordHead=IDE_doc.column
    IDE_doc.column=lastColumn
    if lastColumn==0:
       IDE_backSpcChar()
    else:
       IDE_backSpcChar(None,lastColumn-wordHead)
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_delLine():
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    IDE_setSelection(0)
    if IDE_doc.File[IDE_doc.line]=='': # is it an empty line ?
#        print>>IDE_DEV, 'EMPTY EMPTY EMPTY EMPTY'
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_delLine])
    if HISTORY_ON:
       chars=IDE_doc.File[IDE_doc.line]
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_delLine and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=chars
       else:
          IDE_doc.history.append( [EDIT_delLine,[IDE_doc.line,IDE_doc.column,chars]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    hasLineBreak=IDE_doc.File[IDE_doc.line].endswith('\n')
    if hasLineBreak:
       del IDE_doc.File[IDE_doc.line]
       if IDE_doc.hilight:
          del IDE_doc.quoted[IDE_doc.line]
       IDE_doc.column=min(IDE_doc.column,len(IDE_doc.File[IDE_doc.line].rstrip('\n')))
       IDE_doc.numLines-=1
       IDE_updateLines(max(0,IDE_doc.line-1),updateNext=True) # update since last line
       # update
       adjustCanvasLength(IDE_doc.numLines)
    else:
       IDE_doc.File[IDE_doc.line]=''
       IDE_updateLines()
       IDE_doc.column=0
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_adjustLineMarks(IDE_doc.line,IDE_doc.line+1,-1)
    IDE_updateCurPos()
    IDE_updateBlock()
#     __exposeCurrentLine()
    IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()

def IDE_backSpcChar(column=None,num=1,fineIndentNum=None,completion=True):
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    indentSel=0
    if IDE_doc.isSelecting:
       completion=False
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       if startLine==endLine: ## DELETES SELECTION
          IDE_delSelection()
       else:                  ## UNINDENT SELECTION
          if IDE_doc.recordMacro:
             IDE_addCommandToMacro([COM_unindent,None,num,fineIndentNum,False])
          if fineIndentNum is not None: ## FINE TUNE SELECTION UNINDENT
             # GO UNINDENT THEM NOW !
             IDE_unindentSelection(IDE_CFG[CFG_fixedIndentSpaces])
             IDE_doc.lastMaxColumn=IDE_doc.column
             IDE_doc.setChangedStatus(1) # update isChanged attr
             return
          # SELECTION AUTO-UNINDENT
          lastLine=IDE_doc.line
          lastColumn=IDE_doc.column
          min1stCol=None
          min1stLine=startLine
          comment1stLineCol=None
          for l in range(startLine,endLine+1):
              s=IDE_doc.File[l]
              sLs=s.lstrip()
              if len(sLs):
                 if sLs[0]=='#': # comments
                    if comment1stLineCol is None:
                       comment1stLineCol=(l,s.find(sLs))
                 else:
                    col1st=max(0,s.find(sLs))
                    if col1st>0:
                       min1stCol=col1st
                       min1stLine=l
                       break
          if min1stCol is None: # MEANS NO CODE LINE FOUND
             if comment1stLineCol is None: # NOTHING BUT EMPTY LINES
                return
             else:              # COMMENT EXISTS
                min1stLine,min1stCol=comment1stLineCol
          # sets the line to the 1st non-empty one
          IDE_doc.line=min1stLine
          # sets the column to use the 1st char
          IDE_doc.column=min1stCol
          indentSel=1 # indent them later after getting the next notch
    l=-1
    if column==None:
       column=IDE_doc.column
    if column==0:
       if indentSel:
          # restore line & column
          IDE_doc.line=lastLine
          IDE_doc.column=lastColumn
       else:
          if IDE_doc.line==0:
             return
          s=IDE_doc.File[IDE_doc.line-1]
          IDE_doc.column=len(s)
          s=s[:-1]+IDE_doc.File.pop(IDE_doc.line)
          if IDE_doc.hilight:
             del IDE_doc.quoted[IDE_doc.line]
          IDE_doc.line-=1
          IDE_doc.numLines-=1
          IDE_updateLines(updateNext=True)
#           print>>IDE_DEV, 'EOL deleted'
          # update
          adjustCanvasLength(IDE_doc.numLines)
          IDE_adjustLineMarks(IDE_doc.line,IDE_doc.line+1,-1)
    else:
       s=IDE_doc.File[IDE_doc.line]
       if column==IDE_doc.column:
          if fineIndentNum:
             num=clampScalar(0,IDE_doc.column,IDE_CFG[CFG_fixedIndentSpaces])
             s=s[:IDE_doc.column-num]+s[IDE_doc.column:]
          else:
             sLS=s.lstrip()
             if len(sLS) and not indentSel:
                wsNum=s.find(sLS)
             else:
                wsNum=IDE_doc.column
             if wsNum>=IDE_doc.column:  # left side is clear
                num=IDE_doc.column
                l=IDE_doc.line-1
                while num>=IDE_doc.column and l>=0:
                      prevL=IDE_doc.File[l]
                      prevLstrip=prevL.lstrip()
                      if len(prevLstrip) and prevLstrip[0]!='#': # ignore comments
                         prevLws=prevL.find(prevLstrip)
                         num=clampScalar(0,num,prevLws)
                      if num>=IDE_doc.column:
                         l-=1
                if num==IDE_doc.column: # no left edge found 'til 1st line
                   num=0 # flush it left then
                s=s[:num]+s[IDE_doc.column:]
                num=IDE_doc.column-num
                if indentSel:  # UNINDENTS SELECTION
                   # restore line & column
                   IDE_doc.line=lastLine
                   IDE_doc.column=lastColumn
                   # GO UNINDENT THEM NOW !
                   IDE_unindentSelection(num,min1stLine=min1stLine,refLine=l)
             else:  # there are some chars before the cursor
                s=s[:IDE_doc.column-num]+s[IDE_doc.column:]
       else:
          s=s[:column-num]+s[column:]
    if not indentSel:
       if IDE_doc.recordMacro:
          IDE_addCommandToMacro([COM_delPrevChar,None,1])
       if HISTORY_ON:
          chars=IDE_doc.File[IDE_doc.line][IDE_doc.column-num:IDE_doc.column]
          Hlen=IDE_truncateHistory()
          if Hlen and IDE_doc.history[-1][0]==EDIT_backsp and IDE_doc.groupHistoryOn:
             if chars=='\n':
                IDE_doc.history[-1][1][0]=IDE_doc.history[-1][1][0]-1
             IDE_doc.history[-1][1][-2]=IDE_doc.column-num
             IDE_doc.history[-1][1][-1]=chars+IDE_doc.history[-1][1][-1]
          else:
             IDE_doc.history.append( [EDIT_backsp,[IDE_doc.line,IDE_doc.column-num,chars]] )
             IDE_doc.historyIdx+=1
       if IDE_doc.recordMacro:
          IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
       lastRecordMacro=IDE_doc.recordMacro
       IDE_doc.recordMacro=False
       IDE_doc.File[IDE_doc.line]=s
       IDE_updateLines()
       IDE_gotoPrevColumn(num)
       if fineIndentNum:
          IDE_drawIndentHelperLine(IDE_doc.line,-1) # to immediately hide the helper line
       else:
          IDE_drawIndentHelperLine(IDE_doc.line,refLine=l)
       # updates group history status
       if HISTORY_ON and not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
       IDE_doc.recordMacro=lastRecordMacro
    #________________________________________________________________
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()
    # code completion________________________________________________
    if completion:
       IDE_completion()

def IDE_indentLine(fineIndentNum=None):
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_indent,fineIndentNum])
    indentSel=0
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       if startLine==endLine: ###### DELETES SELECTION
          IDE_delSelection()
       else:                  ###### INDENTS SELECTION
          if fineIndentNum is not None:  ## FINE TUNE SELECTION INDENT
             # GO INDENT THEM NOW !
             IDE_indentSelection(IDE_CFG[CFG_fixedIndentSpaces])
             IDE_doc.lastMaxColumn=IDE_doc.column
             IDE_doc.setChangedStatus(1) # update isChanged attr
             return
          ## SELECTION AUTO-INDENT
          lastLine=IDE_doc.line
          lastColumn=IDE_doc.column
          min1stCol=None
          min1stLine=startLine
          comment1stLineCol=None
          for l in range(startLine,endLine+1):
              s=IDE_doc.File[l]
              sLs=s.lstrip()
              if len(sLs):
                 if sLs[0]=='#':
                    if comment1stLineCol is None:
                       comment1stLineCol=(l,s.find(sLs))
                 else:
                    col1st=max(0,s.find(sLs))
                    if not s.isspace() and col1st>=0:
                       min1stCol=col1st
                       min1stLine=l
                       break
          if min1stCol is None: # MEANS NO CODE LINE FOUND
             if comment1stLineCol is None: # NOTHING BUT EMPTY LINES
                return # I don't think I need to do something
             else:              # COMMENT FOUND
                min1stLine,min1stCol=comment1stLineCol
          # sets the line to the 1st non-empty one
          IDE_doc.line=min1stLine
          # sets the column to use the 1st char
          IDE_doc.column=min1stCol
          indentSel=1 # indent them later after getting the next notch
    s=IDE_doc.File[IDE_doc.line]
    if not indentSel and fineIndentNum is not None:
       num=IDE_CFG[CFG_fixedIndentSpaces] if fineIndentNum==-1 else fineIndentNum
       l=-1
    else:
       wsNum=IDE_doc.column
       num=wsNum
       l=IDE_doc.line-1
       maxLen=wsNum
       while num<=wsNum and l>=0:
             prevL=IDE_doc.File[l].rstrip()
             prevLstrip=prevL.lstrip()
             if len(prevLstrip) and prevLstrip[0]!='#':  # ignore comments
                prevLws=prevL.find(prevLstrip)
                prevLen=len(prevL)
                if prevLws>maxLen:
                   num=prevLws
                elif prevLen>maxLen:
                   notWS=prevL[maxLen] not in string.whitespace
                   lastNum=num
                   for sp in range(maxLen,prevLen):
                       if prevL[sp] in string.whitespace:
                          notWS=0
                       else:
                          if not notWS:
                             num=sp
                             break
                          notWS=1
                   if lastNum==num:
                      num=prevLen
                maxLen=max(maxLen,prevLen)
             if num<=wsNum:
                l-=1
       if num==wsNum:  # jumps off the right edge, or no possible notch
          num=2  # use <num> spaces
       else:
          num-=IDE_doc.column
    if indentSel:  # INDENTS SELECTION
       # restore line & column
       IDE_doc.line=lastLine
       IDE_doc.column=lastColumn
       # GO INDENT THEM NOW !
       IDE_indentSelection(num,min1stLine,refLine=l)
    else:
       if HISTORY_ON:
          char=' '*num
          Hlen=IDE_truncateHistory()
          if Hlen and IDE_doc.history[-1][0]==EDIT_type and IDE_doc.groupHistoryOn:
             IDE_doc.history[-1][1][-1]+=char
          else:
             IDE_doc.history.append( [EDIT_type,[IDE_doc.line,IDE_doc.column,char]] )
             IDE_doc.historyIdx+=1
       if IDE_doc.recordMacro:
          IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
       lastRecordMacro=IDE_doc.recordMacro
       IDE_doc.recordMacro=False
       s=s[:IDE_doc.column]+' '*num+s[IDE_doc.column:]
       IDE_doc.File[IDE_doc.line]=s
       IDE_updateLines()
       IDE_gotoNextColumn(num)
       IDE_drawIndentHelperLine(IDE_doc.line,refLine=l)
       # updates group history status
       if HISTORY_ON and not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
       IDE_doc.recordMacro=lastRecordMacro
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()

def IDE_indentSelection(num,min1stLine=None,refLine=-1):
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_indentSel and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=num
       else:
          IDE_doc.history.append( [EDIT_indentSel,
                                    [IDE_doc.line,IDE_doc.column,
                                    IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                                    num]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    WS=' '*num
    for l in range(startLine,endLine+1):
        s=IDE_doc.File[l]
        isQuoted,color=IDE_doc.getLineQuotedNColor(l)
        # if it's a comment created by this IDE, keeps the '#' at the 1st column
        if not isQuoted and len(s)>2 and (s[:2]=='# ' or s[:2]=='##'):
           if s[:2]=='# ':
              IDE_doc.File[l]='# '+WS+s[2:]
           else:
              IDE_doc.File[l]=WS+s
           IDE_updateLines(l)
        else:
           if not s.isspace():
              IDE_doc.File[l]=WS+s
              if l in IDE_doc.displayed:
                 # no need to redraw, just slide it aside
                 IDE_doc.displayed[l].setX(IDE_doc.displayed[l],num*IDE_all_chars_maxWidth)
              else:
                 IDE_updateLines(l)
    IDE_doc.column=clampScalar(0,len(IDE_doc.File[IDE_doc.line])-1,IDE_doc.column+num)
    IDE_doc.blockStartCol+=num
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateBlock()
    IDE_updateCurPos()
    if min1stLine is None:
       min1stLine=startLine
    IDE_drawIndentHelperLine(min1stLine,refLine)

def IDE_unindentSelection(num,min1stLine=None,refLine=-1):
    lastLine,lastCol=IDE_doc.line,IDE_doc.column
    blockStartLine,blockStartCol=IDE_doc.blockStartLine,IDE_doc.blockStartCol
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    lastCodeShift=MAXINT
    for l in range(startLine,endLine+1):
        s=IDE_doc.File[l]
        rescueRealComment=0
        if num>0 and s[num:num+2]=='# ':
           # must replace indented '# ' with '##',
           # otherwise, once flushed left, it will stuck there
           rescueRealComment=1
#            print>>IDE_DEV, 'RESCUE REAL COMMENT'
        isQuoted,color=IDE_doc.getLineQuotedNColor(l)
        # if it's a comment created by this IDE, keeps the '#' at the 1st column
        if not isQuoted and len(s)>2 and (s[:2]=='# ' or s[:2]=='##' or rescueRealComment):
           if rescueRealComment:
              IDE_doc.File[l]='## '+s[num+2:]
           else:
              num=min(num,s[2:].find(s[2:].lstrip()))
              if s[:2]=='# ':
                 IDE_doc.File[l]='# '+s[num+2:]
              else:
                 IDE_doc.File[l]='##'+s[2:]
           IDE_updateLines(l)
        elif lastCodeShift>0:
           lineWS=s.find(s.lstrip())
           minShift=min(num,lineWS)
           if not s.isspace():
              lastCodeShift=minShift
           IDE_doc.File[l]=s[minShift:]
           if l in IDE_doc.displayed:
              # no need to redraw, just slide it aside
              IDE_doc.displayed[l].setX(IDE_doc.displayed[l],-minShift*IDE_all_chars_maxWidth)
           else:
              IDE_updateLines(l)
    if lastCodeShift==0: # no change
       return
    num=min(num,lastCodeShift)
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_indentSel and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]-=num
       else:
          IDE_doc.history.append( [EDIT_indentSel,
                                    [lastLine,lastCol,
                                    blockStartLine,blockStartCol,
                                    -num]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    IDE_doc.column=max(0,IDE_doc.column-num)
    IDE_doc.blockStartCol=max(0,IDE_doc.blockStartCol-num)
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_updateBlock()
    IDE_updateCurPos()
    if min1stLine is None:
       min1stLine=startLine
    IDE_drawIndentHelperLine(min1stLine,refLine)

def IDE_adjustSelection(inc):
    if not IDE_doc.isSelecting:
       IDE_doc.isSelecting=True
       IDE_doc.blockStartLine,IDE_doc.blockStartCol=IDE_doc.line,IDE_doc.column
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    if startLine==endLine and startCol==endCol:
       if inc<0:
          IDE_doc.isSelecting=False
          if IDE_SOUND_oops.status()==AudioSound.READY:
             IDE_SOUND_oops.play()
          return
       else:
          inc=-inc
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_expandSelection if inc else COM_shrinkSelection,inc],False)
    colInc=inc*( (startLine==IDE_doc.line and startCol==IDE_doc.column)*2-1 )
    if IDE_doc.column-colInc<0:
       if IDE_doc.line>0:
          IDE_doc.line-=1
          IDE_doc.column=len(IDE_doc.File[IDE_doc.line].rstrip('\n'))
    elif IDE_doc.column-colInc>len(IDE_doc.File[IDE_doc.line].rstrip('\n')):
       if IDE_doc.line<IDE_doc.numLines-1:
          IDE_doc.line+=1
          IDE_doc.column=0
    else:
       IDE_doc.column-=colInc
    if IDE_doc.blockStartCol+colInc<0:
       if IDE_doc.blockStartLine>0:
          IDE_doc.blockStartLine-=1
          IDE_doc.blockStartCol=len(IDE_doc.File[IDE_doc.blockStartLine].rstrip('\n'))
    elif IDE_doc.blockStartCol+colInc>len(IDE_doc.File[IDE_doc.blockStartLine].rstrip('\n')):
       if IDE_doc.blockStartLine<IDE_doc.numLines-1:
          IDE_doc.blockStartLine+=1
          IDE_doc.blockStartCol=0
    else:
       IDE_doc.blockStartCol+=colInc
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    if startLine==endLine and startCol==endCol:
       IDE_doc.isSelecting=False
    IDE_updateBlock()
    IDE_updateCurPos()
    __exposeCurrentLine()

def IDE_injectChar(char,column=None,completion=True,insert=True):
    global IDE_lastInjectedChar
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if mustBeHalted(): return
    if IDE_doc.isSelecting: ###### DELETES SELECTION
       IDE_delSelection()
    charLen=len(char)
    retract=0
    pairs=False
    s=IDE_doc.File[IDE_doc.line]
    if HISTORY_ON:
       if charLen==1:
          if char in IDE_bracketsPairs:
             char+=IDE_bracketsPairs[char]
             retract=1
             IDE_doc.groupHistoryOn=False
             pairs=True
          elif char in IDE_QUOTES:
             char*=2
             retract=1
             IDE_doc.groupHistoryOn=False
             pairs=True
    if IDE_doc.recordMacro:
       if len(IDE_doc.macro) and IDE_doc.macro[-1][0]==COM_type and \
            IDE_doc.groupHistoryOn and IDE_doc.macro[-1][2]==column:
          IDE_doc.macro[-1][1]+=char
       else:
          IDE_addCommandToMacro([COM_type,char[0] if pairs else char,None,False])
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       insert&=IDE_insert
       if insert:
          if Hlen and IDE_doc.history[-1][0]==EDIT_type and IDE_doc.groupHistoryOn:
             IDE_doc.history[-1][1][-1]+=char
          else:
             IDE_doc.history.append( [EDIT_type,[IDE_doc.line,IDE_doc.column,char]] )
             IDE_doc.historyIdx+=1
       else:
          col=IDE_doc.column if column is None else column
          ovrChar=s[col:col+len(char)].rstrip('\n')
          if Hlen and IDE_doc.history[-1][0]==EDIT_typeOvr and IDE_doc.groupHistoryOn:
             IDE_doc.history[-1][1][-2]+=ovrChar
             IDE_doc.history[-1][1][-1]+=char
          else:
             IDE_doc.history.append( [EDIT_typeOvr,[IDE_doc.line,IDE_doc.column,ovrChar,char]] )
             IDE_doc.historyIdx+=1
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    if s=='':
       s=char
    else:
       if column is None:
          maxIdx=len(s.rstrip('\n'))
          s=s[:IDE_doc.column]+char+s[min(maxIdx,IDE_doc.column+len(char)*(not insert)):]
       else:
          s=s[:column]+char+s[column:]
    IDE_doc.File[IDE_doc.line]=s
    IDE_updateLines()
    IDE_gotoNextColumn(len(char)-retract)
    IDE_doc.lastMaxColumn=IDE_doc.column
    IDE_doc.setChangedStatus(1) # update isChanged attr
    # updates group history status
    if HISTORY_ON and not IDE_doc.groupHistoryOn and retract==0: # and char!=' '
       IDE_doc.groupHistoryOn=True
    IDE_doc.recordMacro=lastRecordMacro
    if charLen==1:
       if char==IDE_lastInjectedChar:
          IDE_forceRender()
       else:
          IDE_lastInjectedChar=char
    # code completion________________________________________________
    if completion:
       IDE_completion()

def IDE_repeatCharsKEYDOWN(args,ce):
    if ce.GetKeyCode() in (wx.WXK_NUMPAD_ENTER,wx.WXK_RETURN):
       if args[-1] is not None:
          IDE_processRepeatedChars(*(args+(ce,)))
    elif ce.GetKeyCode()==wx.WXK_ESCAPE:
       args[-2].GetGrandParent().Close()
    else:
       ce.Skip()

def IDE_repeatChars():
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_repeatChars)
    frame = wx.Frame(None, -1, 'Repeat characters')
    frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
    panel = wx.Panel(frame)

    insCharsSizer = wx.BoxSizer(wx.VERTICAL)
    charsSizer = wx.BoxSizer(wx.HORIZONTAL)
    optionsSizer = wx.BoxSizer(wx.HORIZONTAL)

    charsText = wx.StaticText(panel, -1, "Characters :")
    charsInput = wx.TextCtrl(panel,value=IDE_REPEATCHARS_lastChars,size=(150,-1))

    numSizer = wx.StaticBoxSizer(wx.StaticBox(panel),wx.HORIZONTAL)
    numText = wx.StaticText(panel, -1, "Counts :")
    numInput = wx.TextCtrl(panel,value=IDE_REPEATCHARS_lastCount,size=(50,-1))

    colSizer = wx.StaticBoxSizer(wx.StaticBox(panel),wx.HORIZONTAL)
    colText = wx.StaticText(panel, -1, 'Fill until column :')
    colInput = wx.TextCtrl(panel,value=IDE_REPEATCHARS_lastColumn,size=(50,-1))

    frame.Bind(wx.EVT_KEY_DOWN,Functor(IDE_repeatCharsKEYDOWN,(charsInput,None)))

    charsInput.Bind(wx.EVT_KEY_DOWN,Functor(IDE_repeatCharsKEYDOWN,(charsInput,None)))
    numInput.Bind(wx.EVT_KEY_DOWN,Functor(IDE_repeatCharsKEYDOWN,(IDE_doc,charsInput,numInput,colInput,True)))
    colInput.Bind(wx.EVT_KEY_DOWN,Functor(IDE_repeatCharsKEYDOWN,(IDE_doc,charsInput,numInput,colInput,False)))

    charsSizer.Add(charsText, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
    charsSizer.Add(charsInput, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)

    insCharsSizer.Add(charsSizer, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    insCharsSizer.Add(optionsSizer, 0, wx.ALL, 5)

    optionsSizer.Add(numSizer, 0, wx.RIGHT, 5)
    optionsSizer.Add(colSizer)

    numSizer.Add(numText, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    numSizer.Add(numInput, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    colSizer.Add(colText, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    colSizer.Add(colInput, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)

    panel.SetSizer(insCharsSizer)
    insCharsSizer.Fit(frame)
    insCharsSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    charsInput.SetFocus()

def IDE_processRepeatedChars(doc,charsInput,numInput,colInput,useCount,ce):
    input=charsInput.GetValue()
    if input=='': return
    try:
        num=int((numInput if useCount else colInput).GetValue().strip())
    except:
        return
    # closes the window
    IDE_closeWxInterface(ce.GetEventObject().GetGrandParent())
    if doc!=IDE_doc:
       doc.setDocActive()
    IDE_doInsertRepeatedChars(input,useCount,num)

def IDE_doInsertRepeatedChars(input,useCount,num):
    global IDE_REPEATCHARS_lastChars,IDE_REPEATCHARS_lastCount,IDE_REPEATCHARS_lastColumn
    if useCount:
       chars=num*input
       if not IDE_doc.recordMacro: IDE_REPEATCHARS_lastCount=str(num)
    else:
       chars=(input*(1+num/len(input)))[:max(0,num-IDE_doc.column)]
       if not IDE_doc.recordMacro: IDE_REPEATCHARS_lastColumn=str(num)
    if not IDE_doc.recordMacro: IDE_REPEATCHARS_lastChars=input
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_repeatChar,input,useCount,num])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    IDE_injectChar(chars,completion=False)
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_changeCase(case,completion=True):
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_changeCase,case,False])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       if HISTORY_ON:
          if startLine==endLine: # a single line
             chars=IDE_doc.File[startLine][startCol:endCol]
          else:                  # multiple lines
             chars=IDE_doc.File[startLine][startCol:]
             for l in range(startLine+1,endLine):
                 chars+=IDE_doc.File[l]
             chars+=IDE_doc.File[endLine][:endCol]
          IDE_truncateHistory()
          IDE_doc.history.append( [EDIT_changeCaseSel,
                                    [IDE_doc.line,IDE_doc.column,
                                    IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                                    chars,case]] )
          IDE_doc.historyIdx+=1
       if lastRecordMacro:
          IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
       if startLine==endLine: # single line
          s=IDE_doc.File[IDE_doc.line]
          sel=s[startCol:endCol]
          if case==0:
             selC=sel.swapcase()
          elif case==1:
             selC=sel.upper()
          else:
             selC=sel.lower()
          if selC==sel:
             IDE_doc.recordMacro=lastRecordMacro
             return
          IDE_doc.File[IDE_doc.line]=s[:startCol]+selC+s[endCol:]
          IDE_updateLines()
       else: # multi lines
          dispUpdt=[]
          # 1st line ____________________
          s=IDE_doc.File[startLine]
          sel=s[startCol:]
          if case==0:
             selC=sel.swapcase()
          elif case==1:
             selC=sel.upper()
          else:
             selC=sel.lower()
          if selC!=sel:
             IDE_doc.File[startLine]=s[:startCol]+selC
             dispUpdt.append(startLine)
          # middle ____________________
          for l in range(startLine+1,endLine):
              s=IDE_doc.File[l]
              if case==0:
                 selC=s.swapcase()
              elif case==1:
                 selC=s.upper()
              else:
                 selC=s.lower()
              if selC!=s:
                 IDE_doc.File[l]=selC
                 dispUpdt.append(l)
          # last line ____________________
          s=IDE_doc.File[endLine]
          sel=s[:endCol]
          if case==0:
             selC=sel.swapcase()
          elif case==1:
             selC=sel.upper()
          else:
             selC=sel.lower()
          if selC!=sel:
             IDE_doc.File[endLine]=selC+s[endCol:]
             dispUpdt.append(endLine)
          # update display
          for l in dispUpdt:
              IDE_updateLines(l)
    else:
       s=IDE_doc.File[IDE_doc.line]
       lineLen=len(s)
       if lineLen and lineLen>IDE_doc.column and s[IDE_doc.column]!='\n':
          sel=s[IDE_doc.column]
          if case==0:
             selC=sel.swapcase()
          elif case==1:
             selC=sel.upper()
          else:
             selC=sel.lower()
          if selC==sel:
             IDE_gotoNextColumn()
             IDE_doc.recordMacro=lastRecordMacro
             return
          if HISTORY_ON:
             char=sel
             Hlen=IDE_truncateHistory()
             if Hlen and IDE_doc.history[-1][0]==EDIT_changeCase and \
                  IDE_doc.history[-1][1][-2]==case and IDE_doc.groupHistoryOn:
                IDE_doc.history[-1][1][-1]+=char
             else:
                IDE_doc.history.append( [EDIT_changeCase,[IDE_doc.line,IDE_doc.column,case,char]] )
                IDE_doc.historyIdx+=1
          if lastRecordMacro:
             IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
          IDE_doc.File[IDE_doc.line]=s[:IDE_doc.column]+selC+s[IDE_doc.column+1:]
          IDE_updateLines()
          IDE_gotoNextColumn()
          # updates group history status
          if HISTORY_ON and not IDE_doc.groupHistoryOn:
             IDE_doc.groupHistoryOn=True
       else:
          IDE_doc.recordMacro=lastRecordMacro
          return
    IDE_doc.recordMacro=lastRecordMacro
    IDE_doc.setChangedStatus(1) # update isChanged attr
    # code completion________________________________________________
    IDE_completion()

def IDE_breakLine():
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.isSelecting: ###### DELETES SELECTION
       IDE_delSelection()
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_breakLine])
    IDE_adjustLineMarks(IDE_doc.line,IDE_doc.line+1,1)
    s=IDE_doc.File[IDE_doc.line]
    oldLine=s[:IDE_doc.column]+'\n'
    oldLineLS=oldLine.lstrip()
    if oldLine.isspace():
       newLineCol=IDE_doc.column*(not UNDO)
    else:
       newLineCol=oldLine.find(oldLineLS)*(not UNDO)
    newLine=' '*newLineCol+s[IDE_doc.column:]
    IDE_doc.File[IDE_doc.line]=oldLine

    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_breakLine and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=1
       else:
          IDE_doc.history.append( [EDIT_breakLine,[IDE_doc.line,len(oldLine)-1,newLineCol,1]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    isQuoted,color=IDE_doc.getLineQuotedNColor()
    isQuoted=IDE_doc.hilightLine(IDE_doc.File[IDE_doc.line],None,isQuoted)
    IDE_doc.line+=1
    # insert the tail line piece
    IDE_doc.File.insert(IDE_doc.line,newLine)
    if IDE_doc.hilight:
       IDE_doc.quoted.insert(IDE_doc.line,IDE_doc.quoted[IDE_doc.line-(IDE_doc.line>len(IDE_doc.quoted)-1)])
    IDE_doc.numLines+=1
    IDE_doc.column=newLineCol
    IDE_updateLines(IDE_doc.line-1,updateNext=True,forced=True)
    # auto-indent
    if HISTORY_ON:
       oldLineLSsplit=oldLineLS.split()
       if len(oldLineLSsplit):
          word_0=oldLineLSsplit[0].rstrip(':')
          if word_0 in IDE_CFG[CFG_smartIndent]:
             numIndent=IDE_CFG[CFG_smartIndent][word_0]
             IDE_indentLine(numIndent if numIndent else None)
             # packs different type actions in a tuple
             IDE_doc.history[-2]=tuple(IDE_doc.history[-2:])
             IDE_doc.history.pop()
             IDE_doc.historyIdx-=1
    IDE_doc.lastMaxColumn=IDE_doc.column
    # update
    adjustCanvasLength(IDE_doc.numLines)
    IDE_updateCurPos()
    __exposeCurrentLine()
    IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()
    IDE_doc.processImports(IDE_doc.line-1,IDE_doc.line)

def IDE_drawIndentHelperLine(currLine,refLine):
    if IDE_doc.isSelecting:
       currL=IDE_doc.File[currLine]
       c1=currL.find(currL.lstrip())
    else:
       c1=IDE_doc.column
    __exposeCurrentLine(currLine,col=c1)
    if refLine<0 or currLine-refLine<=1:
       IDE_doc.helperLine.hide()
       IDE_finishIndentCloseUpViewIval()
       return
    IDE_doc.helperLine.setPos((c1+.5*(not IDE_insert))*IDE_all_chars_maxWidth,0,-(currLine-.2)*IDE_lineheight)
    Zscale=(currLine-refLine-.7)*IDE_lineheight
    IDE_doc.helperLine.setSx(Zscale)
    IDE_doc.helperLine.getChild(1).setTexScale(TextureStage.getDefault(),Zscale,1)
    # if the reference line invisible, bring it closer to me in a viewport
    refLineInvisible=refLine*IDE_lineheight*IDE_textScale[2]<IDE_canvas.getZ()
    if refLineInvisible:
#        print>>IDE_DEV, 'REF :',IDE_doc.File[refLine]
       closeUpParent=NodePath('closeup parent')
       closeUpParent.setDepthTest(0)
       closeUpParent.setDepthWrite(0)
       textParent=closeUpParent.attachNewNode('text parent')
       textParent.setTexture(IDE_normal_chars_tex)
       textParent.setScale(IDE_doc.textParent.getScale(IDE_2Droot))
       beg=max(0,refLine-10)
       end=min(refLine+10,IDE_doc.numLines)
       for z in range(beg,end):
           textLine=textParent.attachNewNode('')
           isQuoted,color=IDE_doc.getLineQuotedNColor(z)
           IDE_doc.drawTextLine(z,textLine,color,isQuoted)
           textLine.setZ(-z*IDE_lineheight)

       helperLineInst=IDE_doc.helperLine.instanceTo(textParent)
       helperLineInst.setAlphaScale(1)
       helperLineInst.show()
       IDE_textCursor.instanceTo(textParent)

       l=0;  r=1.-.5*(IDE_canvasThumbWidth+IDE_canvasThumbBorder)*IDE_scale[0]/IDE_winORatio
       b=.6; t=1.-IDE_tabsHeight*.55*IDE_scale[2]
       VPcam = Camera('closeup vpcam')
       VPcam.copyLens(base.cam2dp.node().getLens())
       VPcam.setScene(closeUpParent)
       VPcamNP = closeUpParent.attachNewNode(VPcam)
       VPcamNP.setX(IDE_winORatio*(r-2*l)-(IDE_canvas.getX(render2dp)+1)*IDE_winORatio)
       VPcamNP.setZ(textParent,-refLine*IDE_lineheight)
       VPcamNP.setScale(IDE_winORatio*(r-l),1,(t-b))
       VPcamNP.setTransparency(1)

       dr=base.win.makeDisplayRegion(l,r,b,t)
       dr.setCamera(VPcamNP)
       dr.setSort(MAXINT-1)

       VPcam.showFrustum()
       b3=VPcamNP.getChild(0).getTightBounds()
       VPcam.hideFrustum()
       CM=CardMaker('')
       CM.setFrameFullscreenQuad()
       card=VPcamNP.attachNewNode(CM.generate())
       card.wrtReparentTo(closeUpParent)
       card.setColor(0,0,0,.75)
       card.setTransparency(1)
       card.setY(10)
       l=b3[0][0]; b=b3[0][2]; r=b3[1][0]; t=b3[1][2]
       LS=LineSegs()
       LS.setThickness(4)
       LS.setColor(0,.7,1,1)
       LS.moveTo(l,0,t)
       LS.drawTo(r,0,t)
       LS.drawTo(r,0,b)
       LS.drawTo(l,0,b)
       LS.drawTo(l,0,t)
       frame=VPcamNP.attachNewNode(LS.create(),1000)
       frame.setBin('dialogsBin',0)

       Sequence(
                Wait(.8),
                closeUpParent.colorScaleInterval(.5,Vec4(1,1,1,0)),
                Func(base.win.removeDisplayRegion,dr),
                Func(closeUpParent.removeChildren),
                Func(closeUpParent.removeNode),
                name=IDE_ivalsName+'closeup hide'
                ).start()
    else:
       IDE_finishIndentCloseUpViewIval()

    Sequence(
             Func(IDE_doc.helperLine.show),
             Func(IDE_doc.helperLine.setAlphaScale,1),
             Wait(.5),
             IDE_doc.helperLine.colorScaleInterval(.3,Vec4(1,1,1,0)),
             Func(IDE_doc.helperLine.hide),
             name=IDE_ivalsName+'indentation helper show hide'
             ).start()

def IDE_scrollView(direction,moveCursor=None):
    # this is to avoid continuous movement after releasing the button,
    # when the keypress repeat is so short
    if mustBeHalted(): return
    if HISTORY_ON and not PLAYING_MACRO:
       if moveCursor is None:
          moveCursor=not IDE_doc.isSelecting
       __scrollCanvas(IDE_CFG[CFG_linesPerScroll]*IDE_lineScale[2]*direction,moveCursor)
       IDE_forceRender()

def IDE_moveLines(direction):
    global HISTORY_ON, MOVING_LINES
    # this is to avoid continuous movement after releasing the button,
    # when the keypress repeat is so short
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return

    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       numSelLines=endLine-startLine+1
       lastLineDelta=IDE_doc.line-startLine
       lastBSLineDelta=IDE_doc.blockStartLine-startLine
       lastBCol=IDE_doc.blockStartCol
    else:
       startLine=endLine=IDE_doc.line
       numSelLines=1

    insLine=startLine+direction
    if not ( 0 <= insLine <= IDE_doc.numLines-numSelLines ):
       return

    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_moveLines,direction])
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_moveLines and IDE_doc.history[-1][1][-2]==direction and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=1
       else:
          IDE_doc.history.append( [EDIT_moveLines,
                                    [IDE_doc.line,IDE_doc.column,
                                    IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                                    IDE_doc.isSelecting,direction,1]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

    historyWasOn=HISTORY_ON
    HISTORY_ON=False
    wasRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    MOVING_LINES=True

#     # THE POPPED LINE
#     zOffset=numSelLines*direction*IDE_lineheight
#     poppedLine=NodePath('')
#     isQuoted,color=IDE_doc.getLineQuotedNColor(popLine)
#     IDE_doc.drawTextLine(popLine,poppedLine,color,isQuoted)
#     poppedLine.setZ(-insLine*IDE_lineheight)
#     if HISTORY_ON:
#        Sequence(
#           Func(poppedLine.hide),
#           Wait(.2),
#           Func(poppedLine.show),
#           name=IDE_ivalsName+'moveRealLine_%s'%id(poppedLine)
#           ).start()
#        # a little visual effect
#        poppedLineCopy=poppedLine.copyTo(IDE_doc.textParent)
#        poppedLineCopy.setName('movedLineDuplicate')
#        pos=poppedLineCopy.getPos()
#        Sequence(
#           poppedLineCopy.posInterval(.15, pos+Point3(2,0,.5*direction*IDE_lineheight),
#                                           pos-Point3(0,0,zOffset)),
#           poppedLineCopy.posInterval(.05, pos),
#           Func(poppedLineCopy.removeNode),
#           name=IDE_ivalsName+'moveFakeLine_%s'%id(poppedLineCopy)
#           ).start()

    selMLs=[l for l in IDE_doc.markedLines if startLine<=l<=endLine]
    selMCs=[IDE_doc.markedColumns[m] for m in selMLs]
    selMLs=[insLine+m-startLine for m in selMLs]

    movedText=''.join(IDE_doc.File[startLine:endLine+1])
    lastLineHasBreak=not movedText.endswith('\n')
    if lastLineHasBreak:
       movedText+='\n'
       IDE_doc.File[startLine-1]=IDE_doc.File[startLine-1][:-1]
    wasSelecting=IDE_doc.isSelecting
    lastCol=IDE_doc.column
    IDE_doc.isSelecting=True
    IDE_doc.blockStartLine=startLine
    IDE_doc.blockStartCol=0
    if endLine==IDE_doc.numLines-1:
       IDE_doc.line=endLine
       IDE_doc.column=len(IDE_doc.File[endLine])
    else:
       IDE_doc.line=endLine+1
       IDE_doc.column=0
    IDE_delSelection()
    IDE_doc.line=insLine
    IDE_doc.column=0
    if lastLineHasBreak:
       IDE_doc.numLines-=1
       adjustCanvasLength(IDE_doc.numLines)
    if insLine==IDE_doc.numLines:
       if not IDE_doc.File[insLine-1].endswith('\n'):
          IDE_doc.File[insLine-1]+='\n'
          movedText=movedText[:-1]
       IDE_doc.File.append('')
       IDE_doc.quoted.append(0)
       IDE_doc.numLines+=1
       adjustCanvasLength(IDE_doc.numLines)
    IDE_paste(movedText,smartPaste=False)

    IDE_doc.recordMacro=wasRecordMacro
    HISTORY_ON=historyWasOn
    MOVING_LINES=False

    # restores the deleted marks
    for m in range(len(selMLs)):
        IDE_toggleMarkLine(selMLs[m],selMCs[m])

    if wasSelecting:
       IDE_doc.isSelecting=True
       IDE_doc.line=insLine+lastLineDelta
       IDE_doc.blockStartLine=insLine+lastBSLineDelta
       IDE_doc.blockStartCol=lastBCol
    else:
       IDE_doc.line=insLine
    IDE_doc.column=lastCol
    IDE_updateCurPos()
    IDE_updateBlock()
    if direction>0: # downward
       __exposeCurrentLine(insLine+numSelLines+10)
    else:           # upward
       __exposeCurrentLine(insLine-10)
    if not (UNDO or REDO):
       IDE_doc.setChangedStatus(1) # update isChanged attr
       IDE_forceRender()

def IDE_duplicateLine(direction):
    if mustBeHalted(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.isSelecting:
       print(NOT_YET, file=IDE_DEV)
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_duplicateLine,direction])
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_copyLine and IDE_doc.history[-1][1][-2]==direction and IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=1
       else:
          IDE_doc.history.append( [EDIT_copyLine,[IDE_doc.line,IDE_doc.column,direction,1]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    origDir=direction
    if IDE_doc.line+direction<0:
       direction=1
    s=IDE_doc.File[IDE_doc.line]
    if not s.endswith('\n'):
       s+='\n'
    IDE_doc.File.insert(IDE_doc.line,s)
    isQuoted,color=IDE_doc.getLineQuotedNColor()
    if IDE_doc.hilight:
       IDE_doc.quoted.insert(IDE_doc.line,IDE_QUOTE2IDX[isQuoted])
    IDE_adjustLineMarks(IDE_doc.line-(not origDir>0),IDE_doc.line+(origDir>0),1)
    IDE_doc.numLines+=1
    IDE_updateLines(updateNext=True,forced=True)
    IDE_doc.line+= origDir>0
    # update
    adjustCanvasLength(IDE_doc.numLines)
    IDE_updateCurPos()
#     __exposeCurrentLine()
    IDE_doc.setChangedStatus(1) # update isChanged attr
    IDE_forceRender()

def IDE_joinLines(conn=' ',stripSpaces=True):
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    elif not IDE_doc.isSelecting:
       return
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    if startLine==endLine: # it's just 1 line
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_joinLines,conn,stripSpaces])
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       IDE_doc.history.append( [EDIT_joinLines,[IDE_doc.line,IDE_doc.column,\
                                IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                                startLine,''.join(IDE_doc.File[startLine:endLine+1]),
                                conn,stripSpaces
                                ]] )
       IDE_doc.historyIdx+=1
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    nextLines=[IDE_REptr_backSlsAtEnd.sub('',l.strip() if stripSpaces else l.rstrip()) for l in IDE_doc.File[startLine+1:endLine]]
    nextLines+=[IDE_doc.File[endLine].lstrip() if stripSpaces else IDE_doc.File[endLine]]
    joinedLine=IDE_REptr_backSlsAtEnd.sub('',IDE_doc.File[startLine].rstrip())+conn+conn.join(nextLines)
    if IDE_doc.File[endLine].endswith('\n'):
       joinedLine+='\n'
    IDE_doc.line=startLine
    IDE_doc.File[IDE_doc.line]=joinedLine
    del IDE_doc.File[startLine+1:endLine+1]
    if IDE_doc.hilight:
       del IDE_doc.quoted[startLine+1:endLine+1]
    IDE_doc.numLines-=endLine-startLine
    # update current display line
    IDE_updateLines(updateNext=True,forced=True)
    IDE_adjustLineMarks(IDE_doc.line,endLine,-1)
    # update
    adjustCanvasLength(IDE_doc.numLines)
    IDE_doc.isSelecting=False
    IDE_updateCurPos()
    IDE_updateBlock()
#     __exposeCurrentLine()
    IDE_doc.setChangedStatus(1) # update isChanged attr

def IDE_clearAllLineMarks():
    if not IDE_doc.markedLines: return
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_noInput)
    IDE_openYesNoDialog('Are you sure to clear all bookmarks ?',IDE_clearAllLineMarksConfirmed)

def IDE_clearAllLineMarksConfirmed(yes):
    IDE_setMode(IDE_lastMode)
    IDE_doClearAllLineMarks(yes)

def IDE_doClearAllLineMarks(yes):
    global IDE_frameWidth
    if not yes: return
    IDE_doc.markedLines=[]
    IDE_doc.markedColumns={}
    IDE_doc.lineMarkParent.removeChildren()
    IDE_frameWidth=2.*IDE_winORatio/IDE_scale[0]-IDE_canvasThumbWidth-IDE_canvasThumbBorder
    fr=Vec4(IDE_frame.node().getFrame())
    fr.setY(IDE_frameWidth)
    IDE_frame['frameSize']=fr
    IDE_frame.setX(IDE_docsTabsBG,0)
    SliderBG.setX(IDE_frameWidth)
    IDE_markersBar.hide()
    IDE_updateLineMarksStatus()

def IDE_toggleMarkLine(line=None,column=None):
    global IDE_frameWidth
    if line is None:
       line=IDE_doc.line
    if line in IDE_doc.markedLines:
       IDE_doc.markedLines.remove(line)
       del IDE_doc.markedColumns[line]
       IDE_doc.lineMarkParent.find(str(line)).removeNode()
    else:
       mark=IDE_lineMark.instanceUnderNode(IDE_doc.lineMarkParent,str(line))
       mark.setZ(-line*IDE_lineheight)
       IDE_doc.markedLines.append(line)
       IDE_doc.markedLines.sort()
       IDE_doc.markedColumns[line]=IDE_doc.column if column is None else column
    lineMarksAvail=bool(IDE_doc.markedLines)
    if lineMarksAvail:
       IDE_markersBar.show()
    else:
       IDE_markersBar.hide()
    Xoff=IDE_canvas_leftBgXR2D*lineMarksAvail
    IDE_frameWidth=2.*IDE_winORatio/IDE_scale[0]-IDE_canvasThumbWidth-IDE_canvasThumbBorder-Xoff
    fr=Vec4(IDE_frame.node().getFrame())
    fr.setY(IDE_frameWidth)
    IDE_frame['frameSize']=fr
    IDE_frame.setX(IDE_docsTabsBG,Xoff)
    SliderBG.setX(IDE_frameWidth)
    IDE_updateLineMarksStatus()

def IDE_gotoPrevMarkedLine():
    global IDE_lineMarksCycleTime,IDE_lineMarksLastTime
    rt=globalClock.getRealTime()
    if rt-IDE_lineMarksLastTime>.2:
       IDE_lineMarksCycleTime=0
    IDE_lineMarksLastTime=rt
    prevMLs=[l for l in IDE_doc.markedLines if l<IDE_doc.line]
    if prevMLs:
       if IDE_lineMarksCycleTime<0:
          IDE_lineMarksCycleTime-=globalClock.getDt()
          if IDE_lineMarksCycleTime<-1-IDE_lineMarksWrapThreshold:
             IDE_lineMarksCycleTime=0
       else:
          IDE_doc.lastMaxColumn=IDE_doc.markedColumns[prevMLs[-1]]
          IDE_gotoPrevLine(num=IDE_doc.line-prevMLs[-1],center=None)
    elif IDE_doc.markedLines and IDE_doc.line==IDE_doc.markedLines[0]:
       IDE_lineMarksCycleTime+=globalClock.getDt()
       if IDE_lineMarksCycleTime>IDE_lineMarksWrapThreshold:
          IDE_doc.lastMaxColumn=IDE_doc.markedColumns[IDE_doc.markedLines[-1]]
          IDE_gotoNextLine(num=IDE_doc.markedLines[-1]-IDE_doc.line,center=None)
          IDE_lineMarksCycleTime=-1

def IDE_gotoNextMarkedLine():
    global IDE_lineMarksCycleTime,IDE_lineMarksLastTime
    rt=globalClock.getRealTime()
    if rt-IDE_lineMarksLastTime>.2:
       IDE_lineMarksCycleTime=0
    IDE_lineMarksLastTime=rt
    nextMLs=[l for l in IDE_doc.markedLines if l>IDE_doc.line]
    if nextMLs:
       if IDE_lineMarksCycleTime<0:
          IDE_lineMarksCycleTime-=globalClock.getDt()
          if IDE_lineMarksCycleTime<-1-IDE_lineMarksWrapThreshold:
             IDE_lineMarksCycleTime=0
       else:
          IDE_doc.lastMaxColumn=IDE_doc.markedColumns[nextMLs[0]]
          IDE_gotoNextLine(num=nextMLs[0]-IDE_doc.line,center=None)
    elif IDE_doc.markedLines and IDE_doc.line==IDE_doc.markedLines[-1]:
       IDE_lineMarksCycleTime+=globalClock.getDt()
       if IDE_lineMarksCycleTime>IDE_lineMarksWrapThreshold:
          IDE_doc.lastMaxColumn=IDE_doc.markedColumns[IDE_doc.markedLines[0]]
          IDE_gotoPrevLine(num=IDE_doc.line-IDE_doc.markedLines[0],center=None)
          IDE_lineMarksCycleTime=-1

def IDE_selectAll():
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_selectAll],False)
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    oldZ=IDE_canvas.getZ()
    IDE_gotoDocBeg()
    IDE_gotoDocEnd(isSelecting=True)
    __updateCanvasZpos(oldZ) # let's keep it unscrolled
    IDE_doc.recordMacro=lastRecordMacro

def IDE_cut():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_cut])
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    cutLine=not IDE_doc.isSelecting
    if cutLine:
       # put it at soft-begin, so upon gotoFront, it will be put at real-begin
       IDE_doc.column=IDE_doc.File[IDE_doc.line].find(IDE_doc.File[IDE_doc.line].lstrip())
       IDE_gotoFront()
       if IDE_doc.File[IDE_doc.line].endswith('\n'):
          IDE_gotoNextLine(isSelecting=True)
       else:
          IDE_gotoBack(isSelecting=True)
          if not IDE_CFG[CFG_realLineEnd]:
             IDE_gotoBack(isSelecting=True)
       IDE_doc.isSelecting=True
    IDE_copy()
    IDE_delChar()
    IDE_doc.recordMacro=lastRecordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)

def IDE_copy(text=False):
    global IDE_CLIPBOARD
    if IDE_doc.recordMacro and not text:
       IDE_addCommandToMacro([COM_copy])
    if text:
       textStr=text
    else:
       textClip=[]
       if IDE_doc.isSelecting:
          startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
          if startLine==endLine: # a single line
             textClip.append(IDE_doc.File[startLine][startCol:endCol])
          else:                  # multiple lines
             textClip.append(IDE_doc.File[startLine][startCol:])
             for l in range(startLine+1,endLine):
                 textClip.append(IDE_doc.File[l])
             textClip.append(IDE_doc.File[endLine][:endCol])
       else: # if there isn't anything selected, copy the whole line
          textClip.append(IDE_doc.File[IDE_doc.line])
       textStr=''.join(textClip)
    if textStr:
       IDE_CLIPBOARD=textStr
       # store it in the OS' clipboard for wider range of usage
       if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
          wx.TheClipboard.SetData(wx.TextDataObject(IDE_CLIPBOARD))
          wx.TheClipboard.Flush() # Close() is not enough, somehow the OS' clipboard
                                  # simply unavailable
       joinedLines=IDE_CLIPBOARD.replace('\n',' __/^\\__ ')
       IDE_setMessage('CLIP: '+(joinedLines[:200]+'.....' if len(joinedLines)>200 else joinedLines))
#        print>>IDE_DEV, 'COPIED'

def encodeToUTF8(text):
    encodedText = text.encode('utf-8')
#     return encodedText
    if len(encodedText)!=len(text):
       extractedEncodedText=''
       clear=True
       for c in range(len(encodedText)):
           if ord(encodedText[c])>127:
              if clear:
                 extractedEncodedText+=encodedText[c+1]
                 clear=False
              else:
                 clear=True
           else:
              extractedEncodedText+=encodedText[c]
              clear=True
       return extractedEncodedText
    else:
       return encodedText

def IDE_paste(pasted=None,smartPaste=True,stickCursor=False,processImp=False):
    global IDE_CLIPBOARD
    if pasted is None:
       if IDE_doc.readonly:
          warnReadonlyDoc()
          return
       if mustBeHalted(): return
       if wx.TheClipboard.IsOpened() or wx.TheClipboard.Open():
          td = wx.TextDataObject()
          isText = wx.TheClipboard.GetData(td)
          wx.TheClipboard.Close()
          if isText:
             # use universal newline
             textClip= td.GetText().replace('\r\n','\n').replace('\r','\n')
#              text = td.GetText().replace('\r\n','\n').replace('\r','\n')
#              textClip=encodeToUTF8(text)
             IDE_CLIPBOARD=textClip # also store it to IDE's clipboard,
                                    # in case the following happens
          else:
             # OS' clipboard isn't text format, so use the last stored text,
             # but no need to store it to OS' clipboard.
             # I want this IDE less brutal, so let's use the last text internally,
             # without damaging other people's good time :)
             textClip=IDE_CLIPBOARD
    else:
       textClip=pasted#.replace('\r\n','\n').replace('\r','\n') # use universal newline
    textClipLines=textClip.splitlines(1)
    if textClipLines:
       IDE_doPaste(textClip,textClipLines,pasted,smartPaste,stickCursor,processImp)
       if IDE_doc!=IDE_log:
          IDE_forceRender()

def IDE_doPaste(textClip,textClipLines,pasted,smartPaste,stickCursor,processImp):
    if IDE_doc.isSelecting: ###### DELETES SELECTION
       IDE_delSelection()
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    origCurrLine=IDE_doc.line
    origCurrCol=IDE_doc.column
    if IDE_doc.recordMacro:
       IDE_confirmPasteType(textClip,stickCursor,IDE_doc.historyIdx)
    if HISTORY_ON and not IDE_doc.readonly:
       chars=textClip
       Hlen=IDE_truncateHistory()
       if Hlen and IDE_doc.history[-1][0]==EDIT_paste and \
            IDE_doc.history[-1][1][-2]==chars and IDE_doc.history[-1][1][-3]==stickCursor and\
            IDE_doc.groupHistoryOn:
          IDE_doc.history[-1][1][-1]+=1
       else:
          IDE_doc.history.append( [EDIT_paste,[IDE_doc.line,IDE_doc.column,smartPaste,stickCursor,chars,1]] )
          IDE_doc.historyIdx+=1
       # updates group history status
       if not IDE_doc.groupHistoryOn:
          IDE_doc.groupHistoryOn=True
    s=IDE_doc.File[IDE_doc.line]
    if textClipLines[-1].endswith('\n'):
       textClipLines.append('')
    textClipNumLines=len(textClipLines)
    if textClipNumLines==1:  # a single line
       s=s[:IDE_doc.column]+textClipLines[0]+s[IDE_doc.column:]
       IDE_doc.File[IDE_doc.line]=s
       if isLoadedFile:
          IDE_updateLines()
       IDE_doc.column+=len(textClipLines[0])
    else:                    # multiple lines
       if pasted is None:
          IDE_setMessage('Pasting.....')
          renderFrame(2)
       tail=textClipLines[-1]+s[IDE_doc.column:]
       s=s[:IDE_doc.column]+textClipLines[0]
       IDE_doc.File[IDE_doc.line]=s
       if (IDE_doc and IDE_doc==IDE_log) or not smartPaste:
          emptyLineBeg=''
       else:
          emptyLineBeg=' '*IDE_doc.column
       IDE_adjustLineMarks(IDE_doc.line,IDE_doc.line+textClipNumLines-1,1)
       # creates the middle lines
       for l in textClipLines[1:-1]:
           IDE_doc.line+=1
           IDE_doc.File.insert(IDE_doc.line,emptyLineBeg+l)
           if IDE_doc.hilight:
              IDE_doc.quoted.insert(IDE_doc.line,0)
       # creates the tail part line
       IDE_doc.line+=1
       IDE_doc.File.insert(IDE_doc.line,emptyLineBeg+tail)
       if IDE_doc.hilight:
          IDE_doc.quoted.insert(IDE_doc.line,0)
       if smartPaste:
          # set it to the last line in the clipboard
          IDE_doc.column+=len(textClipLines[-1].rstrip('\n'))
       else:
          #~ IDE_doc.column=0
          IDE_doc.column=len(textClip)-1-textClip.rfind('\n')
       IDE_doc.numLines+=textClipNumLines-1
       IDE_updateLines(origCurrLine,updateNext=True,forced=True,numStatic=textClipNumLines)

    if not isLoadedFile:
       return
    if pasted is None:
       IDE_setMessage('Pasted.')
    if IDE_doc==IDE_log: return
    if stickCursor: # restore the line & column if it should not move
       IDE_doc.line=origCurrLine
       IDE_doc.column=origCurrCol
    # update
    if UPDATE_DISPLAY:
       adjustCanvasLength(IDE_doc.numLines)
       IDE_updateCurPos()
       __exposeCurrentLine()
    if not UNDO_REPLACE:
       IDE_doc.setChangedStatus(1) # update isChanged attr
    # TEMPORARY IMPORT FOR CODE COMPLETION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    if pasted is None or processImp:
       textClipNumLines=textClip.count('\n')
       IDE_doc.processImports( IDE_doc.line-textClipNumLines*(not stickCursor),
                               IDE_doc.line+textClipNumLines*stickCursor)

def IDE_confirmPasteType(textClip,stickCursor,historyIdx):
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_confirmMacroPaste)
    frame = wx.Frame(None, -1, 'Paste text options')
    panel = wx.Panel(frame)

    optSizer = wx.BoxSizer(wx.VERTICAL)
    fixedInsSizer = wx.StaticBoxSizer(wx.StaticBox(panel),wx.VERTICAL)
    liveInsSizer = wx.StaticBoxSizer(wx.StaticBox(panel),wx.VERTICAL)

    fixedInsertButton = wx.Button(panel, -1, "Fixed text")
    fixedInsertText = wx.StaticText(panel, -1, "always insert this text,\nwithout copying from clipboard anymore")
    fixedInsertButton.Bind(wx.EVT_BUTTON,Functor(IDE_doRecordMacroPaste,textClip,stickCursor,historyIdx,frame))
    if WIN:
       fixedInsertButton.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)

    liveInsertButton = wx.Button(panel, -1, "Live text")
    liveInsertText = wx.StaticText(panel, -1, "always insert text from clipboard")
    liveInsertButton.Bind(wx.EVT_BUTTON,Functor(IDE_doRecordMacroPaste,None,stickCursor,historyIdx,frame))
    if WIN:
       liveInsertButton.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)

    fixedInsSizer.Add(fixedInsertButton, 0, wx.ALIGN_CENTER, 5)
    fixedInsSizer.Add(fixedInsertText, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)
    liveInsSizer.Add(liveInsertButton, 0, wx.ALIGN_CENTER, 5)
    liveInsSizer.Add(liveInsertText, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM, 5)

    optSizer.Add(fixedInsSizer, 0, wx.ALL|wx.EXPAND, 5)
    optSizer.Add(liveInsSizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 5)

    panel.SetSizer(optSizer)
    optSizer.Fit(frame)
    optSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    fixedInsertButton.SetFocus()

def IDE_doRecordMacroPaste(textClip,stickCursor,historyIdx,frame,ce):
    IDE_addCommandToMacro([COM_paste,textClip,True,stickCursor],historyIdx=historyIdx)
    IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    # closes the window
    IDE_closeWxInterface(frame)

def IDE_toggleInsert(insert=None):
#     if IDE_doc.readonly:
#        warnReadonlyDoc()
#        return
#     IDE_doc.groupHistoryOn=False
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_toggleInsert,insert],False)
    IDE_doToggleInsert(insert)

def IDE_doToggleInsert(insert):
    global IDE_insert
    if insert==None:
       IDE_insert=not IDE_insert
       IDE_textCursor.getChild(0).toggleVis()
       IDE_textCursor.getChild(1).toggleVis()
    else:
       IDE_insert=insert
       if insert:
          IDE_textCursor.getChild(0).show()
          IDE_textCursor.getChild(1).hide()
       else:
          IDE_textCursor.getChild(0).hide()
          IDE_textCursor.getChild(1).show()

def IDE_toggleComment():
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    global HISTORY_ON
    if IDE_doc.recordMacro:
       IDE_addCommandToMacro([COM_toggleComment])
    if HISTORY_ON:
       Hlen=IDE_truncateHistory()
       IDE_doc.history.append( [EDIT_comment,
                                 [IDE_doc.line,IDE_doc.column,
                                 IDE_doc.blockStartLine,IDE_doc.blockStartCol,
                                 IDE_doc.isSelecting]] )
       IDE_doc.historyIdx+=1
    if IDE_doc.recordMacro:
       IDE_doc.macro_redoIdx[IDE_doc.historyIdx]=len(IDE_doc.macro)
    historyWasOn=HISTORY_ON
    HISTORY_ON=False
    lastRecordMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    lastCol=IDE_doc.column
    lastMaxColPos=IDE_doc.lastMaxColumn
    isMultiLine=False
    wasSelecting=IDE_doc.isSelecting
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       isMultiLine=startLine!=endLine
       IDE_doc.isSelecting=False
    if isMultiLine:
       codeLineExists=False
       for l in range(startLine,endLine+1):
           s=IDE_doc.File[l].lstrip()
           if len(s) and s[0]!='#':
              codeLineExists=True
              break
       colOffset=0 if UNDO else codeLineExists*2-1
       if codeLineExists: # comment out
          for l in range(startLine,endLine+1):
              s=IDE_doc.File[l].lstrip()
              if len(s):# and s[0]!='#':
                 IDE_doc.File[l]='# '+IDE_doc.File[l]
       else: # uncomment
          for l in range(startLine,endLine+1):
              s=IDE_doc.File[l]
              if len(s)>2 and s[:2]=='# ':
                 IDE_doc.File[l]=IDE_doc.File[l][2:]
       IDE_updateLines(startLine,updateNext=True)
       if not startLine in IDE_doc.displayed:
          populatePage(startLine=startLine,forced=True)
    else:  # SINGLE LINE
       uncomment=len(IDE_doc.File[IDE_doc.line]) and IDE_doc.File[IDE_doc.line][0]=='#'
       colOffset=0 if UNDO else (not uncomment)*2-1
       blockStartCol=IDE_doc.blockStartCol
       # uncomment
       if uncomment:
          if len(IDE_doc.File[IDE_doc.line])>2:
             if IDE_doc.File[IDE_doc.line][1] in string.whitespace:
                IDE_backSpcChar(2,2,completion=False)
             else:
                IDE_backSpcChar(1,1,completion=False)
          else:
             IDE_backSpcChar(1,1,completion=False)
       else: # comment out
          IDE_injectChar('# ',0,completion=False)
       if wasSelecting:
          IDE_doc.blockStartCol=blockStartCol
    IDE_doc.column=clampScalar(0,len(IDE_doc.File[IDE_doc.line].rstrip('\n')),lastCol+colOffset*2)
    IDE_doc.lastMaxColumn=lastMaxColPos
    if wasSelecting:
       IDE_doc.blockStartCol=clampScalar(0,len(IDE_doc.File[IDE_doc.blockStartLine].rstrip()),IDE_doc.blockStartCol+colOffset*2)
       IDE_doc.isSelecting=True
       IDE_updateBlock()
    IDE_updateCurPos()
    IDE_doc.setChangedStatus(1) # update isChanged attr
    HISTORY_ON=historyWasOn
    IDE_doc.recordMacro=lastRecordMacro

def IDE_getPointerPos(clampToPage=False):
    mposR2D=base.mouseWatcherNode.getMouse()
    mpos=IDE_canvas.getRelativePoint(render2dp,Point3(mposR2D[0],0,mposR2D[1]))
    canvasZ=IDE_canvas.getZ()
    pageStartLine=int(canvasZ/IDE_lineScale[2])
    pageEndLine=int((canvasZ+IDE_frameHeight)/IDE_lineScale[2])-1
    pureLine=-int(mpos[2]/(IDE_lineheight*IDE_textScale[2])-.5)
    l=clampScalar(
        pageStartLine if clampToPage else 0,
        min(pageEndLine,IDE_doc.numLines-1) if clampToPage else IDE_doc.numLines-1,
        pureLine)
    maxCol=len( IDE_doc.File[l].rstrip('\n') )
    c=int( clampScalar(0,maxCol,int(mpos[0]/(IDE_all_chars_maxWidth*IDE_textScale[0]))) )
    return (l,c,pureLine<=pageStartLine,pureLine>=pageEndLine) if clampToPage else (l,c)

def IDE_canvas_LMBdown(mwp):
    # find out if any menu is active
    currMode = base.buttonThrowers[0].node().getPrefix() if IDE_root.isHidden() else IDE_getMode()
    anyActiveMenu = currMode.find('menu-')==0
    if not IDE_doc or\
       (anyActiveMenu and IDE_isAnyModifierDown()):
       return
    shiftDown = base.mouseWatcherNode.isButtonDown(MODIF_shift)
    IDE_CC_cancel()
    IDE_hideSGB()
    IDE_cancelResolutionChange()
    if IDE_doc.recordMacro:
       IDE_SOUND_blockedKeyb.play()
       IDE_setMessage('You should only record movement by keyboard.')
       return
    if not IDE_isInMode(MODE_active):
       return
    if not base.mouseWatcherNode.hasMouse():
       return
    global IDE_SELECTMODE, IDE_lastClickObj
    IDE_doc.groupHistoryOn = False
    #~ print>>IDE_DEV, 'LMB down'
    dt = globalClock.getRealTime()-IDE_lastClickTime
    l,c = IDE_getPointerPos()
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    validDoubleClick = dt<.3 and \
      (
        (not IDE_doc.isSelecting and IDE_doc.line==l and IDE_doc.column==c) \
          or \
        ( IDE_doc.isSelecting and (
  #           startLine<l<endLine or \ # shouldn't cycle, but drag n drop instead
            (startLine==l and startCol<=c) or (endLine==l and c<=endCol)
          )
        )
      )
    if IDE_doc.isSelecting:
       lastL,lastC = IDE_doc.blockStartLine,IDE_doc.blockStartCol
    else:
       lastL,lastC = IDE_doc.line,IDE_doc.column
    IDE_doc.line,IDE_doc.column = l,c
    if validDoubleClick:
       IDE_SELECTMODE+=1
       IDE_SELECTMODE%=IDE_SELECTMODE_line+1
       obj=IDE_lastClickObj
    else:
       IDE_SELECTMODE = IDE_SELECTMODE_char
       obj = lambda:0
       if shiftDown:
          IDE_doc.blockStartLine,IDE_doc.blockStartCol = lastL,lastC
          obj.clickLine,obj.clickCol = lastL,lastC
          IDE_doc.isSelecting = True
       else:
          obj.clickLine,obj.clickCol = IDE_doc.line,IDE_doc.column
       IDE_lastClickObj = obj
    #~ print 'IDE_SELECTMODE:',IDE_SELECTMODE
    if IDE_SELECTMODE==IDE_SELECTMODE_char:
       IDE_doc.blockStartLine,IDE_doc.blockStartCol = obj.clickLine,obj.clickCol
    elif IDE_SELECTMODE==IDE_SELECTMODE_word:
       if validDoubleClick:
          IDE_selectWithMouse(obj,forced=True)
       else:
          IDE_doc.isSelecting = False
          IDE_gotoPrevWord()
          IDE_gotoNextWord(isSelecting=True)
    elif IDE_SELECTMODE==IDE_SELECTMODE_line:
       IDE_doc.isSelecting=False
       IDE_gotoFront(forceReal=True)
       IDE_gotoBack(isSelecting=True,forceReal=True,exposeLine=False)
    IDE_doc.lastMaxColumn = IDE_doc.column
    IDE_updateCurPos()
    IDE_updateBlock()
    obj.l,obj.c = IDE_doc.line,IDE_doc.column
    taskMgr.add(IDE_selectWithMouse, IDE_tasksName+'selecting with mouse',extraArgs=[obj])
    IDE_DO.acceptOnce(MODE_selecting+MODE_SUFFIX+'mouse1-up',IDE_canvas_LMBup,[IDE_doc])
    if anyActiveMenu:
       taskMgr.doMethodLater(.01,IDE_setMode,IDE_tasksName+'delayedSelect',extraArgs=[MODE_selecting])
    else:
       IDE_setMode(MODE_selecting)

def IDE_canvas_LMBup(doc):
    M.IDE_lastClickTime = globalClock.getRealTime()
    IDE_setMode(MODE_active)
    taskMgr.remove(IDE_tasksName+'selecting with mouse')
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock(doc)
    if startLine==endLine and startCol==endCol:
       doc.isSelecting = False

def IDE_selectWithMouse(obj,forced=False):
    if base.mouseWatcherNode.hasMouse():
       l,c,beyondPageStartLine,beyondPageEndLine=IDE_getPointerPos(clampToPage=True)
       if l!=obj.l or c!=obj.c or forced:
          obj.l,obj.c=l,c
          if IDE_SELECTMODE==IDE_SELECTMODE_char:
             IDE_setSelection(isSelecting=True)
             IDE_doc.line,IDE_doc.column=l,c
             IDE_updateCurPos()
             IDE_updateBlock()
          else:
             forward=l>obj.clickLine or (l==obj.clickLine and c>=obj.clickCol)
             IDE_doc.line,IDE_doc.column=obj.clickLine,obj.clickCol
             if IDE_SELECTMODE==IDE_SELECTMODE_word:
                (IDE_gotoPrevWord if forward else IDE_gotoNextWord)(exposeLine=False)
                IDE_doc.blockStartLine=IDE_doc.line
                IDE_doc.blockStartCol=IDE_doc.column
                IDE_doc.line,IDE_doc.column=l,c
                IDE_doc.isSelecting=True
                if forward:
                   IDE_gotoNextWord(isSelecting=True,exposeLine=False)
                else:
                   s=IDE_doc.File[IDE_doc.line]
                   if len(s)>IDE_doc.column and IDE_doc.column>0 and \
                        IDE_areSameType(s[IDE_doc.column-1:IDE_doc.column+1]):
                      IDE_gotoPrevWord(isSelecting=True,exposeLine=False)
                IDE_updateCurPos()
                IDE_updateBlock()
             elif IDE_SELECTMODE==IDE_SELECTMODE_line:
                (IDE_gotoFront if forward else IDE_gotoBack)(forceReal=True,exposeLine=False)
                IDE_doc.blockStartLine=IDE_doc.line
                IDE_doc.blockStartCol=IDE_doc.column
                IDE_doc.line,IDE_doc.column=l,c
                IDE_doc.isSelecting=True
                (IDE_gotoBack if forward else IDE_gotoFront)(isSelecting=True,forceReal=True,exposeLine=False)
          IDE_doc.lastMaxColumn=IDE_doc.column
       if beyondPageStartLine:
          __scrollCanvas(-globalClock.getDt())
       elif beyondPageEndLine:
          __scrollCanvas(globalClock.getDt())
       __exposeColumn()
    return Task.cont

def IDE_canvas_RMBdown(mwp):
    if mwp.getModifierButtons().isAnyDown() or \
       not IDE_getMode() in MODE_activeOrCompleting:
       return
    IDE_removeAnyMenuNcallTip()
    IDE_CC_cancel()
    IDE_hideSGB()
    IDE_cancelResolutionChange()

    isSaved=hasattr(IDE_doc,'DirName')
    menuItems=[
      ('Cut','IDE_cut.png',0 if IDE_doc.readonly else IDE_cut),
      ('Copy','IDE_copy.png',IDE_copy),
      ('Paste','IDE_paste.png',0 if IDE_doc.readonly else IDE_paste),
      0, # separator
      ('Select _all','IDE_selectall.png',IDE_selectAll),
      ('Select inside _brackets','IDE_closeBr.png',IDE_selectInsideBrackets,True),
      ('Select inside brackets','IDE_openBr.png',IDE_selectInsideBrackets,False),
      0, # separator
      ('Join lines',0,IDE_joinLines if IDE_doc.isSelecting and not IDE_doc.readonly else 0),
      ('Save to _snippets',0,IDE_saveToSnippets),
      0, # separator
      ('Pick color','IDE_color.png', (
        ('0..1','IDE_color.png',IDE_chooseColor,0),
        ('0..255','IDE_color.png',IDE_chooseColor,1),
        ('0..1 | 0..255','IDE_color.png',IDE_chooseColor,2),
      )),
      ('_Highlighter',0,(
         ('_None', 'IDE_text.png',
              IDE_setHilighter if IDE_doc.hilight!=IDE_HL_None else 0,IDE_HL_None),
         ('_Python', 'IDE_py.png',
              IDE_setHilighter if IDE_doc.hilight!=IDE_HL_Python else 0,IDE_HL_Python),
      ) if IDE_doc!=IDE_log else []
      ),
      0, # separator
      ('_Go to directory',0,IDE_doc.gotoDir if isSaved else 0),
      ('_Revert to save point',0,IDE_doc.revertToSavePoint if IDE_doc!=IDE_log and IDE_doc.historyIdxOnSave!=IDE_doc.historyIdx else 0),
      ('Re_load',0,IDE_doc.confirmReload if IDE_doc.isObsolete else 0),
      ('Save _duplicate as ...',0,IDE_saveDocDuplicateAs),
      ('_Close','IDE_close.png',IDE_closeDoc, IDE_doc),
    ]
    if IDE_doc==IDE_log:
       menuItems.insert(-1,('Clea_r log','IDE_clear.png',IDE_clearLog))
    myPopupMenu = PopupMenu(
       parent=IDE_overlayParent,
       onDestroy=IDE_textCursorIval.resume,
       buttonThrower=IDE_BTnode,
       items=menuItems,
       #~ font=IDE_FONT_digitalStrip, baselineOffset=-.35,
       #~ scale=IDE_statusBarHeight*.55, itemHeight=1.2,
       font=IDE_FONT_medrano, baselineOffset=-.27,
       scale=IDE_statusBarHeight*.65, itemHeight=1.05,
       leftPad=.2, separatorHeight=.45,
       underscoreThickness=2,
       BGColor=(.3,.3,.2,.9),
       BGBorderColor=(.8,.3,0,1),
       separatorColor=(1,1,1,1),
       frameColorHover=(1,.8,.3,1),
       frameColorPress=(0,1,0,1),
       textColorReady=(1,1,1,1),
       textColorHover=(0,0,0,1),
       textColorPress=(0,0,0,1),
       textColorDisabled=(.45,.45,.45,1),
       minZ=IDE_calcMenuMinZ()
    )
    myPopupMenu.menu.setBin('gaugeBin',1)
    IDE_textCursorIval.pause()
    

def IDE_setHilighter(h):
    IDE_doc.hilight=h
    if h==IDE_HL_None:
       IDE_doc.quoted=[]
    elif h==IDE_HL_Python:
       IDE_doc.collectQuotedLines()
    IDE_refreshWorkspace()

def IDE_refreshWorkspace(all=False):
    docs = IDE_documents if all else [IDE_doc]
    for d in docs:
        if d:
           d.displayed.clear()
           if d==IDE_doc:
              populatePage()

def IDE_removeAnyMenuNcallTip():
    if IDE_doc:
       IDE_doc.hideCallTip()
    currMode = base.buttonThrowers[0].node().getPrefix() if IDE_root.isHidden() else IDE_getMode()
    if currMode.find('menu-')==0:
       currMenu = messenger.whoAccepts(currMode+'escape')
       if currMenu:
          menuCandidate = list(currMenu.keys())[0]
          if type(menuCandidate)==tuple:
             messenger._getObject(menuCandidate).destroy(delParents=True)
          else:
             menuCandidate.destroy(delParents=True)

def IDE_checkImports(l):
    if not IDE_doc.hilight: return
    # is it import line ?
    s=IDE_doc.File[l]
    sLen=len(s.strip())
    if sLen:# ignore empty lines
       isQuoted,color=IDE_doc.getLineQuotedNColor(l)
       charsColor=IDE_doc.hilightLine(s,color,isQuoted)[2]
       imp=s.find('import ')
       frm=s.find('from ')
       if (imp>=0 and charsColor[imp] not in COLORIDX_notCode) or\
          (frm>=0 and charsColor[frm] not in COLORIDX_notCode):
          try:
             IDE_CC_TEMP.doImport(s)
          except Exception:
             print(IDE_errShoutout)
             traceback.print_exc()
             IDE_processException(traceback.format_exc(),l+1)

def IDE_clearPools():
    ModelPool.releaseAllModels()
    TexturePool.releaseAllTextures()
    text='Model and Texture pools cleared'
    msg=createMsg(text,bg=(0,1,0,.85))
    putMsg(msg,'pools cleared',2,stat=True)

def IDE_syncConfigInPreferences(cfg,val):
    IDE_CFG[cfg] = val
    if IDEPreferences.PREF_OPEN:
       IDEPreferences.CFG_ORIG[cfg] = val

def IDE_toggleResetCameraTransform():
    IDE_syncConfigInPreferences(CFG_resetCamTransform, not IDE_CFG[CFG_resetCamTransform])
    # update the value in Preferences window, if open
    if IDEPreferences.PREF_OPEN:
       checkBox = IDEPreferences.prefScreen.FindWindowByName(IDEPreferences.RESET_CAM)
       checkBox.Value = IDE_CFG[CFG_resetCamTransform]
#     base.cam2d.clearTransform()
#     base.camera.clearTransform()
#     mat=Mat4(base.camera.getMat())
#     mat.invertInPlace()
#     base.mouseInterfaceNode.setMat(mat)
    text='Camera transform %sCLEARED on update'%['NOT ',''][IDE_CFG[CFG_resetCamTransform]]
    msg=createMsg(text,bg=(0,1,0,.85))
    putMsg(msg,'toggle reset cam transform',2,stat=True)

def IDE_toggleFullscreen():
    fs = not base.win.getProperties().getFullscreen()
    wp = WindowProperties()
    wp.setFullscreen(fs)
    base.win.requestProperties(wp)
    IDE_step() # render frame to get updated properties
    # GOING FULLSCREEN FAILS
    currWP = base.win.getProperties()
    if fs and not currWP.getFullscreen():
       IDE_CC_cancel()
       if not hasattr(IDE_resolutionsList, 'modes'):
          modes = set()
          di = base.pipe.getDisplayInformation()
          for i in range(di.getTotalDisplayModes()):
              if di.getDisplayModeFullscreenOnly(i):
                 modes.add((di.getDisplayModeWidth(i), di.getDisplayModeHeight(i)))
          modes = ['%s x %s'%m for m in sorted(list(modes))]
          IDE_resolutionsList.modes = modes
          IDE_resolutionsList.setDisplay( display=IDE_CC_createText(modes),
                              scale=IDE_textScale,
                              vertSpacing=IDE_lineheight,
                              baseline2top=IDE_chars_maxBaseline2top)
          IDE_resolutionsList.setItems(modes)
       M.IDE_lastMode = IDE_getMode()
       IDE_setMode(MODE_chooseResolution)
       IDE_resolutionsList.note['text'] = IDE_resolutionsList.noteText.replace('X', '%s x %s'%(currWP.getXSize(),currWP.getYSize()))
       IDE_resolutionsList.highlightItem(0)
       IDE_resolutionsList.show()
#     IDE_handleWindowEvent(base.win,forced=True)

def IDE_cleanupScene(explicit=False):
    global APP_cursorHidden, APP_mouseRelative, APP_pointerNrestPos
    if IDE_isScenePaused:
       IDE_resumeScene(forced=1) # force resume
    if explicit:
       text = 'Clearing scene.....'
       msg = createMsg(text,bg=(0,1,0,.85))
       putMsg(msg,'clearing scene',0,stat=True)
       IDE_step()
       IDE_step()
    # CLEANUP...., must be done before removing cameras, or else
    # image processing camera which replaces the default main camera
    # would be gone prematurely and FilterManager wouldn't be usable anymore.
    exc = myFinder.cleanup()
    # kills all user-created cameras
    IDE_cleanupMessenger.send('killAllCameras')
    # now removes all buffers which might not have a camera yet,
    # e.g. when an error occurs before a camera is set to it
    for win in [base.graphicsEngine.getWindow(i) for i in range(base.graphicsEngine.getNumWindows())]:
        hasCams=False
        for d in range(win.getNumDisplayRegions()):
            hasCams|=not win.getDisplayRegion(d).getCamera().isEmpty()
        if not hasCams:
           base.graphicsEngine.removeWindow(win)
    # restores & updates buffer viewer
    base.bufferViewer.setSort('fixed',10000)
    base.bufferViewer.setLayout('hline')
    base.bufferViewer.setPosition('lrcorner')
    base.bufferViewer.refreshReadout()
    # stops all sounds
    for sm in base.sfxManagerList: 
        sm.stopAllSounds()
    # SOMETHING WAS WRONG DURING CLEANUP
    if type(exc)==bytes:
       return exc
    IDE_removeDoLaterTasks()
    IDE_removeTasks()
    # close window event
    base.win.setCloseRequestEvent(closeWindowEventName)
    # restores as many Panda's default values
    bgCol=[ConfigVariable('background-color').getDoubleWord(i) for i in range(3)]+[1]
    base.setBackgroundColor(*bgCol)
    base.trackball.node().setForwardScale(.3)
    enableMouse2Cam()
    base.enableMouse()
    # removes all user's button throwers
    for bt in asList(IDE_getAPPButtonThrowers(stashed=True)):
        bt.removeNode()
    # restores the default button throwers properties
    for bt,prefix,timeFlag in ( [base.timeButtonThrower, 'time-', 1],
                                [base.buttonThrowers[0], '',      0]):
        bt.removeChildren()
        btNode=bt.node()
        btNode.clearThrowButtons()
        btNode.setButtonDownEvent('')
        btNode.setButtonRepeatEvent('')
        btNode.setButtonUpEvent('')
        btNode.setCandidateEvent('')
        btNode.setKeystrokeEvent('')
        btNode.setMoveEvent('')
        btNode.setSpecificFlag(True)
        btNode.setThrowButtonsActive(False)
        btNode.setPrefix(prefix)
        btNode.setTimeFlag(timeFlag)
    mods = ModifierButtons()
    mods.addButton(KeyboardButton.shift())
    mods.addButton(KeyboardButton.control())
    mods.addButton(KeyboardButton.alt())
    mods.addButton(KeyboardButton.meta())
    base.buttonThrowers[0].node().setModifierButtons(mods)
    # restores render states
    ShaderPool.releaseAllShaders()
    emptyRenderState=RenderState.makeEmpty()
    for o in (render,render2d,aspect2d):
        # this should clear all attribs on the node
        o.setState(emptyRenderState)
    # actually clears shaders on camera
    base.cam.node().setInitialState(emptyRenderState)
    base.camLens.clear()
    base.camLens.setAspectRatio(base.getAspectRatio())
    base.cam2d.node().setInitialState(emptyRenderState)
    cam2dLens=base.cam2d.node().getLens()
    cam2dLens.clear()
    cam2dLens.setFilmSize(2, 2)
    cam2dLens.setNearFar(-1000, 1000)

    render2d.setDepthTest(0)
    render2d.setDepthWrite(0)
    render2d.setMaterialOff(1)
    render2d.setTwoSided(1)
    aspect2d.setScale(1.0 / base.getAspectRatio(), 1.0, 1.0)
    aspect2d.setBin('unsorted',0)

    APP_cursorHidden=APP_mouseRelative=False
    APP_pointerNrestPos=None
    if explicit:
       text='Scene cleared'
       msg=createMsg(text,bg=(0,1,0,.85))
       putMsg(msg,'scene cleared',.7,stat=True)
       IDE_refreshSGB()

def IDE_doWriteFile(path,strlist):
    global IDE_lastMode
    try:
        f=open(path,'w')
        f.writelines(strlist)
        f.close()
        return False
    except IOError as xxx_todo_changeme:
        (errno,errstr) = xxx_todo_changeme.args
        lastMode=IDE_getMode()
        if lastMode!=MODE_exiting:
           IDE_lastMode=IDE_getMode()
        IDE_setMode(MODE_noInput)
        IDE_openOkDialog('E R R O R :\n'+errstr+'\n\nUnable to save %s'%os.path.basename(path),
           IDE_setMode,IDE_lastMode,colorScale=Vec4(2,0,0,1),msgColor=Vec4(1))
        return errstr

def IDE_saveAllAndUpdate(autoJumpToScene=False,clearTexturePool=False,clearModelPool=False):
    global IDE_lastMode, APP_cursorHidden, APP_mouseRelative, APP_pointerNrestPos,\
           RunningAPP_mainFile,RunningAPP_CWD,RunningAPP_modDir
    IDE_CC_cancel()
    # collects all new unsaved files
    unsavedNewFiles=[d for d in IDE_documents if d.isChanged and d.FullPath is None]
    if unsavedNewFiles:
       unsavedNewFiles[0].setDocActive()
       IDE_lastMode=IDE_getMode()
       IDE_setMode(MODE_noInput)
       IDE_openOkDialog('This new file is not saved yet.\nPlease save all new files before proceed.',IDE_setMode,IDE_lastMode)
       return
    # saves all files before rebinding any class
    # only save if it was changed
    mustBeSavedFiles=[d for d in IDE_documents if d.isChanged]
    mustBeRebound=[]
    for d in mustBeSavedFiles:
        if IDE_doWriteFile(d.FullPath,d.File):
           d.setDocActive()
           return
        d.setChangedStatus(0) # update isChanged attr
        d.errors=[]
        d.numErrors=0
        d.stopBlinkTab()
        IDE_updateErrNotif()
        # rebind it only if it's already imported,
        # otherwise, it could be an unrelated module file,
        # which might has unisolated run().
        name=joinPaths(d.DirName,os.path.splitext(d.FileName)[0])
        for m in list(sys.modules.values()):
            if m and hasattr(m,'__file__'):
               if name==os.path.splitext(m.__file__)[0]:
                  mustBeRebound.append(d)
                  break
        print('--> SAVED :',d.FullPath, file=IDE_DEV)
    IDE_saveFilesList()
    # restores the scene if it's paused, THIS MUST BE DONE BEFORE REBIND
    if IDE_isScenePaused:
       IDE_resumeScene(forced=1) # force resume
       IDE_safeStep()

    getModelPath().clear()
    IDE_setLoaderPaths()
    getModelPath().appendPath(APP_CWD)
    os.chdir(APP_CWD)
    VirtualFileSystem.getGlobalPtr().chdir(Filename.fromOsSpecific(APP_CWD))

    # sets the running app if it's not the current main module
    if RunningAPP_mainFile!=APP_mainFile:
       underPyPaths=[1 for p in PY_PATHS if OldAPP_CWD.find(p)==0]
       # remove the old main file CWD, so it won't be scanned for modules completion
       if OldAPP_CWD!=APP_CWD and not underPyPaths and OldAPP_CWD in sys.path:
          sys.path.remove(OldAPP_CWD)
       RunningAPP_mainFile=APP_mainFile
       RunningAPP_CWD=APP_CWD
       modDir=os.path.dirname(RunningAPP_mainFile)
       RunningAPP_modDir=modDir if len(modDir)<RunningAPP_CWD else RunningAPP_CWD
#        print>>IDE_DEV, 'moduleName:',APP.moduleName
    # clear pools before rebind
    if clearTexturePool:
       TexturePool.releaseAllTextures()
    if clearModelPool:
       ModelPool.releaseAllModels()

    # REBIND CLASSES
    # should be safe to rebind now, but don't rebind main module now, do it later after
    # cleaning up, who knows user does something in module's global namespace
    mainMod = [d for d in mustBeRebound if d.FullPath==APP_mainFile]
    if mainMod:
       mustBeRebound.pop(mustBeRebound.index(mainMod[0]))
    for d in mustBeRebound:
        d.rebind()

    # CLEANUP....
    exc = IDE_cleanupScene()
    if type(exc)==bytes: # SOMETHING WAS WRONG
       IDE_processException(exc)
       IDE_removeDoLaterTasks()
       return
    realClass=exc

    IDE_setMessage('Running main module.   Please wait.....')
    renderFrame(2)
    # restores P3D's config default values
#     cfg_winSize=ConfigVariable('win-size')
#     cfg_winTitle=ConfigVariable('window-title')
#     cfg_winOrigin=ConfigVariable('win-origin')
#     for cv in (cfg_winSize,cfg_winTitle,cfg_winOrigin):
#         cv.clearLocalValue()

    # REBINDS MAIN MODULE
#     APP.moduleName=os.path.splitext( os.path.basename(APP_mainFile) )[0]
#     APP.moduleName='__main__' # it's already __main__
    sys.argv = [APP_mainFile]+APP_args
    exc = myFinder.rebindClass(__builtins__, APP_mainFile, APP.moduleName)
    mat = Mat4(camera.getMat())
    mat.invertInPlace()
    base.mouseInterfaceNode.setMat(mat)
    if exc: # EXCEPTION
       globalClock.setMode(ClockObject.MNormal)
       IDE_showCursor()
       IDE_setMouseAbsolute()
       disableMouse2Cam()
       # disables all user's button throwers
       IDE_getAPPButtonThrowers().stash()
       IDE_processException(exc)
       # CLEANUP AGAIN
       exc = IDE_cleanupScene()
       if type(exc)==bytes: # SOMETHING WAS WRONG
          IDE_processException(exc)
    else:
       # this also serves to clear the shaders in pool which doesn't happen
       # in current frame
       renderFrame(2)
       # RESTART
       exc = myFinder.restart(realClass)
       globalClock.setMode(ClockObject.MNormal)
       # disables all user's button throwers
       IDE_getAPPButtonThrowers().stash()
       renderFrame() # to get the actual windowproperties
       APP_cursorHidden = base.win.getProperties().getCursorHidden()
       APP_mouseRelative = base.win.getProperties().getMouseMode()==WindowProperties.MRelative
       IDE_showCursor()
       IDE_setMouseAbsolute()
       disableMouse2Cam()
       APP_pointerNrestPos = None
       if exc: # EXCEPTION
          IDE_processException(exc)
          # CLEANUP AGAIN
          exc = IDE_cleanupScene()
          if type(exc)==bytes: # SOMETHING WAS WRONG
             IDE_processException(exc)
          return
       elif autoJumpToScene:
          # let some frames pass by to let the pointer movement recorded, if any
          taskMgr.doMethodLater(.05,IDE_jumpToScene,IDE_tasksName+'autoJumpToScene',extraArgs=[])
       IDE_setMessage('Main module is running.')
    if not base.win.getCloseRequestEvent():
       base.win.setCloseRequestEvent(closeWindowEventName)
    IDE_refreshSGB()
'''       # updates window properties
       w,h=cfg_winSize.getIntWord(0),cfg_winSize.getIntWord(1)
       ox,oy=cfg_winOrigin.getIntWord(0),cfg_winOrigin.getIntWord(1)
       title=cfg_winTitle.getStringValue()
       # and requests it
       wp=WindowProperties()
       wp.setSize(w,h)
       wp.setTitle(title)
       wp.setOrigin(ox,oy)
       base.win.requestProperties(wp)'''

def IDE_removeUselessTasks(tasks):
    for t in tasks:
        func=taskFunc(t)
        mod=func.__module__
        # not IDE's task (-1), or >1, but not 0
        if t and t.name.find(IDE_tasksName) and hasattr(t,taskFuncNameQuery(t)) and (
              (not mod in sys.modules) or mod=='__main__' or \
              mod.find('direct.interval')==0 or \
              (sys.modules[mod].__file__.find(directModulesDir)==-1)
           ):
           t.remove()

def IDE_removeDoLaterTasks():
    IDE_removeUselessTasks(taskMgr.getDoLaters())

def IDE_removeTasks():
    IDE_removeUselessTasks(taskMgr.getTasks())

def IDE_processException(exc,noFileErrLine=None):
    ''' exceptions handler, both for rebind and runtime exceptions
    '''
    def alertUser(errLine,errCol,nStr):
        errLine = int(errLine)-1
        newErr = True
        for l,c,s in IDE_doc.errors:
            if errLine==l and errCol==c and nStr==s:
               newErr=False
               break
        if newErr:
           IDE_doc.errors.append((errLine,errCol,nStr))
           IDE_doc.blinkTab()
           IDE_doc.numErrors+=1
           IDE_updateErrNotif()
        if IDE_doc.numErrors!=len(IDE_doc.errHLivals):
           errHiLight = IDE_REALblock.copyTo(IDE_doc.blockParent,10)
           errHiLight.setName('error')
           errHiLight.setColor(1,0,0,.7,10)
           errHiLight.setPos(0,0,-errLine*IDE_lineheight+IDE_chars_maxBaseline2top)
           errHiLight.setSx(max(1000,len(IDE_doc.File[errLine])))
           errMsg = createMsg(errStr,pad=(1,1,.3,.1))
           errMsg.setName('error')
           errMsg.reparentTo(IDE_doc.blockParent)
           errMsg.setScale(IDE_frame,IDE_statusBarHeight*.725)
           errMsg.setX(render2dp,0)
           z=errLine-1+3*(errLine<3)
           errMsg.setZ(-z*IDE_lineheight)
           errMsg.setBin('dialogsBin',-1)
           errMsg.setTexture(IDE_gradingAlphaTexV0_1 if z>0 else IDE_gradingAlphaTexV1_1)
           errHLival=Sequence(
              errHiLight.colorScaleInterval(.2,Vec4(1,1,1,0)),
              errHiLight.colorScaleInterval(.15,Vec4(1,1,1,1)),
              name=IDE_ivalsName+'errHL_%s'%globalClock.getRealTime()
              )
           errHLival.loop()
           IDE_doc.errHLivals.append(errHLival)
           # always puts cursor to the 1st notified error
           if len(IDE_doc.errHLivals)==1:
              IDE_doc.line=errLine
              if errCol==None:
                 errCol=max(0,IDE_doc.File[IDE_doc.line].find(nStr))
              else:
                 errCol+=IDE_doc.File[IDE_doc.line].find(IDE_doc.File[IDE_doc.line].lstrip())
              IDE_doc.column=min(errCol,len(IDE_doc.File[IDE_doc.line].rstrip()))
              IDE_updateCurPos()
              __exposeCurrentLine(center=True)
        else:
           __exposeCurrentLine(center=True)

        IDE_CC_cancel()
        taskMgr.removeTasksMatching(IDE_CC_tasksName)
        # disables all input for a while
        lastMode=IDE_getMode()
        if (
           lastMode in (MODE_active,MODE_noFile,MODE_completing) and
           lastMode!=MODE_errorOccurs
           ):
           IDE_setMode(MODE_errorOccurs)
           Sequence( IDE_errorWait,
                     Func(IDE_setMode,lastMode),
                     name=IDE_ivalsName+'restore last mode after error'
                     ).start()

    IDE_hideSGB()
    IDE_cancelResolutionChange()
    IDE_SOUND_error.play()

    excLines=exc.splitlines()
    excLines.reverse()
    blankLines=[l for l in excLines if l.isspace()]
    blankLines.reverse()
    blankLinePrevLineLen=None
    for bl in blankLines:
        blankLinePrevLineLen=len(excLines[excLines.index(bl)+1])
        excLines.remove(bl)
    if excLines[1].split()[0]=='File':
       errStr=excLines[0]
       errCaret=''
       errSource=excLines[1]
    else:
       errStr,errCaret,errSource=excLines[:3]
    lastFile=3
    nStr=None
    if errCaret.find('<string>')>0:
       lastFile=1
    elif errCaret.find('^')<0:
       lastFile=1 if errCaret=='' else 2
       errS=errStr.split('\'')
       if len(errS)>1:
          nStr=errS[-2]
          errCol=None
       else:
          errCol=0
    else:
       if blankLinePrevLineLen is None:
          errCol=len(errCaret)-5
       else:
          errCol=len(errCaret)+1+blankLinePrevLineLen
    for l in excLines[lastFile:]:
        if l.find('File \"')>-1:
           s=l.split('\"')
#            print>>IDE_DEV, 'SSS :',s
           errFile=s[1]
           if errFile=='<string>': # NOT IN A FILE
#               print>>IDE_DEV, 'NOT IN A FILE'
              if errCol is not None:
                 alertUser(noFileErrLine,errCol,None)
              else:
                 alertUser(noFileErrLine,0,None)
           else: # IN A FILE
              s2 = s[2].split()
              errLine = s2[2].rstrip(',')
              # look if the faulty caller is inside tasks list,
              # if so, remove it, otherwise its faulty call would be
              # executed every frame forward, causing halt
#               if 'in' in s2:
              errFuncName=s2[-1]
              brokenTaskRemoved = False
              for t in taskMgr.getTasks()+taskMgr.getDoLaters():
                  # let's evaporate this criminal for good
                  if t and hasattr(t,taskFuncNameQuery(t)) and taskFunc(t).__name__==errFuncName:
#                            print>>IDE_DEV, '###',t.__call__
#                            print>>IDE_DEV, '###',t.__call__.__name__
                     brokenTaskRemoved = True
                     t.remove()
                     break

              if 'in' in s2 and not brokenTaskRemoved:
                 # cut the extension, so it includes Task, TaskOrig, and TaskNew
                 P3DTaskPath = joinPaths('task','Task')
                 P3DMessengerPath = joinPaths('showbase','Messenger.py')
                 localBrokenObj = None
                 indirectErr = False
                 # task method common error, i.e. arguments error
                 if errFile.find(P3DTaskPath)>-1:
                    # since 1.6, all tasks run inside AsyncTaskManager.poll(),
                    # so there is no way I can get through C++ block, since
                    # the traceback chain stops at taskMgr.step.
                    if errFuncName=='step':
                       # force capture the notify output,
                       # so I know the erroneous task name and get the function
                       LOG.checkNotify(getTaskErr=True)
                       splitTaskErrMsg=LOG.taskError.split()
                       if len(splitTaskErrMsg)>4:
                          errTaskName=' '.join(splitTaskErrMsg[5:])
                          localBrokenObj='1.6task'
                          brokenObj=taskMgr.getTasksNamed(errTaskName)[0]
                          brokenObjFunc=brokenObj.getFunction()
   #                        print '\nERR TASK NAME:',errTaskName
   #                        print brokenObjFunc
                    # this is for pre-1.6
                    elif errFuncName=='__executeTask':
                       localBrokenObj='task' # key of function's local dictionary
                    localBrokenObjIsTask=True
                 # event method common error, i.e. arguments error
                 elif errFile[-len(P3DMessengerPath):]==P3DMessengerPath:# and\
   #                    errFuncName=='__dispatch' if atLeast16 else 'send':
                    localBrokenObj='method' # key of function's local dictionary
                    localBrokenObjIsTask=False
                 else:
                    TB = sys.exc_info()[2]
                    if TB is None:
                       TB = M.MAIN_MOD_TRACEBACK
                    lastTB = TB
                    while TB.tb_next is not None:
                          lastTB = TB
                          TB = TB.tb_next
                    errCodeLine = ''.join(inspect.getinnerframes(lastTB)[0][4]).strip()
                    errGlobals = lastTB.tb_frame.f_globals
                    errLocals = lastTB.tb_frame.f_locals
                    brokenFunc = None
#                     print 'errFuncName:',errFuncName
                    if errFuncName=='__init__':
#                        print 'errCodeLine:',errCodeLine
#                        print 'errLine:',errLine
                       clsRes = sum( [[errCodeLine[fi.span()[0]:fi.span()[1]].rstrip('(')] for fi in re.finditer(r'([a-zA-Z_]+[a-zA-Z0-9_]*\s*\.?\s*)+\(',errCodeLine)], [])
                       possibleBrokenClasses = []
                       if clsRes:
                          for pbc in clsRes:
                              try:
                                 pbc = eval(pbc, errGlobals, errLocals)
                                 if isinstance(pbc,type) or isinstance(pbc,type):
                                    possibleBrokenClasses.append(pbc)
                              except:
                                 pass
#                        print possibleBrokenClasses
                       if len(possibleBrokenClasses)==1:
                          brokenFunc = getattr(possibleBrokenClasses[0],errFuncName)
                       # not sure which one is erroneous, lets examine the source
                       else:
                          def fakeINIT(fake):
                              pass
                          IDE_document.o__init__ = IDE_document.__init__
                          IDE_document.__init__ = fakeINIT
                          fakeFile = IDE_document()
                          IDE_document.__init__ = IDE_document.o__init__
                          srcF = open(errFile,'rU')
                          fakeFile.File = srcF.readlines()
                          srcF.close()
                          del fakeFile.File[int(errLine.strip()):]
                          brokenClassName = None
                          defIndentLvl = None
                          isQuoted = False
                          fakeFile.quoted=[]
                          for line in fakeFile.File:
                              fakeFile.quoted.append(IDE_QUOTE2IDX[isQuoted])
   #                            print fakeFile.quoted[-1], '>>',line
                              isQuoted = fakeFile.hilightLine(line,None,isQuoted)
                          for li in reversed(list(range(len(fakeFile.File)))):
                              liSt = fakeFile.File[li].lstrip()
                              if fakeFile.quoted[li] or liSt.startswith('#'): continue
   #                            print '>>:',li,fakeFile.File[li]
                              if defIndentLvl is None:
                                 defRes = re.search(r'def\s+%s\('%errFuncName, liSt)
                                 if defRes:
                                    defIndentLvl = len(fakeFile.File[li])-len(liSt)
#                                     print 'defIndentLvl:',defIndentLvl
                              else:
                                 classRes = re.search(r'class\s+\w+\s*[\(\:]', liSt)
                                 if classRes:
                                    classIndentLvl = len(fakeFile.File[li])-len(liSt)
                                    if classIndentLvl>=defIndentLvl:
                                       continue
                                    brokenClassName = liSt[classRes.span()[0]:classRes.span()[1]-1].split()[1]
#                                     print 'brokenClassName:',brokenClassName
                                    possibleBrokenClass = [clsi for clsi in possibleBrokenClasses if clsi.__name__==brokenClassName]
                                    if possibleBrokenClass:
                                       brokenFunc = getattr(possibleBrokenClass[0],errFuncName)
                                       break
                    # not class' init
                    if brokenFunc is None:
                       reRes = re.search(r'([a-zA-Z_]+[a-zA-Z0-9_]*\s*\.?\s*)+%s\s*\('%errFuncName, errCodeLine)
#                        print 'reRes:',reRes
                       if reRes:
                          reStart,reEnd = reRes.span()
                          brokenFunc = eval(errCodeLine[reStart:reEnd].rstrip('(').rstrip(), errGlobals, errLocals)
                       else:
                          reRes = sum( [[errCodeLine[fi.span()[0]:fi.span()[1]].rstrip('(')] for fi in re.finditer(r'([a-zA-Z_]+[a-zA-Z0-9_]*\s*\.?\s*)+\(',errCodeLine)], [])
#                           print 'reRes:',reRes
                          for rr in reRes:
                              if rr:
                                 bbf = eval(rr, errGlobals, errLocals)
                                 if bbf == apply:
                                    applyRes = re.search(r'([a-zA-Z_]+\w*\.?)*%s *\('%rr, errCodeLine)
                                    ffToEnd = errCodeLine[applyRes.span()[1]:].rstrip(')')
                                    ffToEndSpl = ffToEnd.split(',')
                                    if ffToEndSpl:
                                       ffToEnd = ffToEndSpl[0]
                                       brokenFunc = eval(ffToEnd, errGlobals, errLocals)
                                       break
                                 elif hasattr(bbf,'__name__') and bbf.__name__ == errFuncName:
                                    brokenFunc = bbf
                                    break
                    if brokenFunc:
                       def fakeFunc(*a,**kw):
                           pass
                       print('BROKEN FUNC :',brokenFunc)
                       # function interval, don't replace its step func code
                       if brokenFunc.__module__ == FunctionInterval.__module__:
                          ivalInst = brokenFunc.__self__
                          if hasattr(ivalInst,'function'):
                             ivalInst.function = fakeFunc
                       else:
                          if not isinstance(brokenFunc, types.FunctionType) and hasattr(brokenFunc,'im_func'):
                             brokenFunc = brokenFunc.__func__
                          if hasattr(brokenFunc,'func_code'):
                             # this is enough to shut it up, in case it's ran every frame
                             brokenFunc.__code__ = fakeFunc.__code__

                 if localBrokenObj:
                    if localBrokenObj!='1.6task':
                       TB = sys.exc_info()[2]
                       lastTB = None
                       while TB.tb_next is not None:
                             lastTB = TB
                             TB = TB.tb_next
                       brokenObj = TB.tb_frame.f_locals[localBrokenObj]
                       brokenObjFunc = taskFunc(brokenObj) if localBrokenObjIsTask else brokenObj
                       if hasattr(brokenObjFunc,'func_code'):
                          # this is enough to shut it up, in case it's ran every frame
                          def fakeFunc(*a,**kw):
                              pass
                          brokenObjFunc.__code__ = fakeFunc.__code__
                    brokenObjFuncName = brokenObjFunc.__name__
                    brokenObjClass = brokenObjFunc.__class__
                    isInstanceMethod = brokenObjClass!=types.FunctionType
                    mod = brokenObjFunc.__module__
                    # This happens for builtin functions, i.e. C/C++ functions,
                    # whose source code is not available. Eventhough it's available,
                    # pointing the user to it is useless, since the error
                    # is somewhere else.
                    if mod is None:
                       print("\n!!!!  INDIRECT ERROR  !!!!\nCould not pinpoint error location.\nMostly it's invalid arguments count or type mismatch passed indirectly to C/C++ function.\n")
                       print(brokenObjFunc.__doc__+'\n')
                       print('<clue #1> It was triggered by this event   : '+TB.tb_frame.f_locals['event'])
                       print('<clue #2> extraArgs passed to the function :\n%s\n'%TB.tb_frame.f_locals['extraArgs'])
                       lowerLevelErr = "Could not pinpoint error location.\nVisit the log for more info."
                       msg = createMsg(lowerLevelErr)
                       putMsg(msg,'notifyLowerLevelErr',3,stat=True)
                       return
                    # Now finds the actual error location
                    actualFile = sys.modules[mod].__file__
                    if os.path.splitext(actualFile)[1][1:].upper()=='PYC':
                       actualPYFileName = glob( os.path.splitext(actualFile)[0]+'.py' )
                       if actualPYFileName:
                          actualFile=joinPaths(os.path.dirname(actualFile),actualPYFileName[0])
                    # If it really doesn't exist, mostly because the error
                    # is in the IDE, I don't need to load it.
                    if not os.path.exists(actualFile):
                       return
                    if ( (localBrokenObjIsTask and actualFile.find(RunningAPP_modDir)==0) or
                         not localBrokenObjIsTask
                       ):
                       errFile = actualFile
                       className = brokenObjFunc.__self__.__class__.__name__ if isInstanceMethod else ''
                       classFound = not isInstanceMethod
   
                       loaded=False
                       for doc in IDE_documents:
                           if errFile==doc.FullPath:
                              loaded=True
                              srcSplit=doc.File
                              break
                       if not loaded:
                          # weird, rebinding doesn't affect the return value of
                          # inspect.getsource(sys.modules[mod]), so just read it myself
                          f=open(errFile,'rU')
                          srcSplit=f.readlines()
                          f.close()
                       for l in srcSplit:
                           lSP=l.split()
                           if len(lSP)>1:
                              if classFound:
                                 if lSP[0]=='def' and lSP[1].split('(')[0]==brokenObjFuncName:
                                    errLine=srcSplit.index(l)+1
                                    errCol=l.find(brokenObjFuncName)
                                    break
                              elif lSP[0]=='class' and lSP[1].strip(':').split('(')[0]==className:
                                 classFound=True
                    # kick it out of tasks list
                    if localBrokenObjIsTask:
                       brokenObj.remove()
                    # TODO: in case user changes the class' and/or method's name,
                    # before it actually runs after rebound

              # brings user to the crime scene
              loaded=0
              for doc in IDE_documents:
                  if errFile==doc.FullPath:
                     if doc!=IDE_doc:
                        IDE_removeAnyMenuNcallTip()
                        doc.setDocActive()
                     loaded=1
                     alertUser(errLine,errCol,nStr)
                     break
              # not loaded ? Load it then
              if not loaded:
                 IDE_removeAnyMenuNcallTip()
                 if not os.path.exists(errFile) and not WIN and errFile[0]!=os.sep:
                    OSsepPos=errFile.find(os.sep)
                    if OSsepPos>-1:
                       print('\nerrFile:',errFile)
                       errFile=errFile[OSsepPos:]
                       print('errFile:',errFile)
                 print('OPENING %s...'%errFile, file=IDE_DEV)
                 IDE_newDoc(errFile)
                 # alerts user only if it's successfully loaded
                 if [d for d in IDE_documents if d.FullPath==errFile]:
                    alertUser(errLine,errCol,nStr)
           break

def IDE_getSelection():
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    if startLine==endLine: # a single line
       sel=IDE_doc.File[startLine][startCol:endCol]
    else:                  # multiple lines
       sel=IDE_doc.File[startLine][startCol:]
       for l in range(startLine+1,endLine):
           sel+=IDE_doc.File[l]
       sel+=IDE_doc.File[endLine][:endCol]
    return sel

def IDE_setSelection(isSelecting):
    if isSelecting:
       if not IDE_doc.isSelecting:
          IDE_doc.isSelecting=True
          IDE_doc.blockStartLine=IDE_doc.line
          IDE_doc.blockStartCol=IDE_doc.column
    else:
       IDE_doc.isSelecting=False

def IDE_setSelAnchor(l,c):
    IDE_doc.blockStartLine,IDE_doc.blockStartCol=l,c

def IDE_getOrderedBlock(doc=None):
    if doc is None:
       doc=IDE_doc
    if doc.blockStartLine>doc.line:
       startLine=doc.line
       startCol=doc.column
       endLine=doc.blockStartLine
       endCol=doc.blockStartCol
    elif doc.blockStartLine<doc.line:
       startLine=doc.blockStartLine
       startCol=doc.blockStartCol
       endLine=doc.line
       endCol=doc.column
    else: # same line, sort the column start-end
       startLine=doc.blockStartLine
       endLine=doc.line
       if doc.blockStartCol>doc.column:
          startCol=doc.column
          endCol=doc.blockStartCol
       else:
          startCol=doc.blockStartCol
          endCol=doc.column
    return startLine,startCol,endLine,endCol

def IDE_updateBlock():
    if IDE_doc.errHLivals:
       IDE_doc.removeErrHLivals()
    IDE_doc.blockParent.removeChildren()
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
#        print>>IDE_DEV, startLine+1,endLine+1,startCol+1,endCol+1
       if startLine==endLine:
          if endCol!=startCol:
             b=IDE_REALblock.instanceUnderNode(IDE_doc.blockParent,'')
             b.setPos(startCol*IDE_all_chars_maxWidth,0,-startLine*IDE_lineheight+IDE_chars_maxBaseline2top)
             b.setSx(endCol-startCol)
       else:
          lineLen=len( IDE_doc.File[startLine].rstrip() )
          b=IDE_REALblock.instanceUnderNode(IDE_doc.blockParent,'')
          b.setPos(startCol*IDE_all_chars_maxWidth,0,-startLine*IDE_lineheight+IDE_chars_maxBaseline2top)
          b.setSx(1000)
          if endLine-startLine-1:
             b=IDE_REALblock.instanceUnderNode(IDE_doc.blockParent,'')
             b.setPos(0,0,-(startLine+1)*IDE_lineheight+IDE_chars_maxBaseline2top)
             b.setScale(1000,1,endLine-startLine-1)
          if endCol:
             b=IDE_REALblock.instanceUnderNode(IDE_doc.blockParent,'')
             b.setPos(0,0,-endLine*IDE_lineheight+IDE_chars_maxBaseline2top)
             b.setSx(endCol)
    else:
       IDE_doc.blockStartLine=IDE_doc.line
       IDE_doc.blockStartCol=IDE_doc.column

def IDE_delayCompletion():
    # Gives a little delay, to respect user's typing speed,
    # so the completion only happen when user stops typing for at least .3 second.
    # Processing completion for every keystroke is a big waste !
    taskMgr.removeTasksMatching(IDE_CC_tasksName)
    taskMgr.doMethodLater(.3,IDE_completion,IDE_CC_tasksName,extraArgs=[False])

def IDE_completion(later=True,forced=0,isSnippet=None):
    global IDE_CC_isSnippet,IDE_CC_isImport
    if isSnippet is not None:
       IDE_CC_isSnippet=isSnippet
    if IDE_CC_isSnippet:
       IDE_CC_isImport=False
       IDE_showAvailSnippet()
    else:
       IDE_showAvailCodes(later,forced)

def splitArgs(a):
    kws=re.split('\s*,\s*',a)
    inBr=False
    validKws=[]
    for k in list(kws):
        oBr=k.find('(')
        cBr=k.find(')')
        if inBr:
           validKws[-1]+=', '+k
           if cBr>-1:
              inBr=False
        else:
           validKws.append(k.strip())
           if -1<oBr>cBr:
              inBr=True
    return validKws

def IDE_inspectDefSource(obj,wrapWidth=None):
    # don't use the source of the replacement functions defined by the IDE,
    # so the original C++ docs will be used
    if hasattr(obj,'im_class'):
       if '%s.%s'%(obj.__self__.__class__.__name__, obj.__name__) in ORIG_FUNCS:
          return ''
    if wrapWidth is None:
       wrapWidth=IDE_frameColWidth-4
    try:
       src=inspect.getsource(obj)
       if src and src.find('\x00')<0: # no null please
          defPos=src.find('def ')
          colonPos=src.find(':')
          if -1<defPos<colonPos:
             oBr=src.find('(')
             cBr=src[:colonPos].rfind(')')
             if -1<oBr<cBr:
                args=re.sub(r'\\*\s*\n\s*',' ',src[oBr+1:cBr].strip())
                argSpl=splitArgs(args)
                if 'self' in argSpl:
                   argSpl.remove('self')
                objName=obj.__name__#src[defPos+4:oBr].rstrip()
                if objName=='__init__' and hasattr(obj,'im_class'):
                   objName=obj.__self__.__class__.__name__
                wordLen=len(objName)
                argsLine=objName+'(' # 'word('
                argsLineLen=len(argsLine)
                for a in argSpl:
                    aLen=len(a)+2
                    # wrap it
                    if argsLineLen+aLen>wrapWidth:
                       argsLine+='\n'+' '*(wordLen+1)
                       argsLineLen=wordLen+1
                    argsLine+=a+', '
                    argsLineLen+=aLen
                return argsLine.rstrip(', ')+')'
    except:
       pass
    return ''

def IDE_createCallTips(column=None):
    global IDE_CC_objType
    if not IDE_doc.hilight: return
    lastLC = IDE_doc.line,IDE_doc.column
    if column is None:
       column = IDE_doc.column
    brFound,brMatch,x,z = IDE_findBracketBWD(column,')')
    while brFound:
          l = IDE_doc.File[z][:x].rstrip()
          if not l: # '(' is the first char of the line, check the prev line
             if z>0:
                z-=1
                l = IDE_doc.File[z].rstrip()
                x = len(l)
             else:
                brFound=False
                break
          if len(l) and l[-1] in myPunctuationWhitespace:
             IDE_doc.line,IDE_doc.column = z,x
             brFound,brMatch,x,z = IDE_findBracketBWD(x,')')
          else:
             break
    if brFound:
#        print brMatch,x,z
       stt=IDE_doc.File[z][:x].rstrip()
       ws=0
       for i in range(len(stt)-1,-1,-1):
           if stt[i] in myPunctuationWhitespace:
              ws=i+1
              break
       word=stt[ws:]
       wordLen=len(word)
       args=None
       cppIntf=hasKW=False
       wholeDefLines=[]
       print('<CALL TIP/DOC>%s<'%word)
       if word:
          IDE_CC_objType=None
          anyArg=False
          IDE_doc.line,IDE_doc.column=z,ws
          IDE_availCodesList.setItems([])
          IDE_showAvailCodes(later=False,forced=True,displayCC=False)
#           IDE_updateCurPos();return# debug completion
          codes=IDE_availCodesList.getItems()
          IDE_doc.line,IDE_doc.column=lastLC
          IDE_CC_cancel()
          if codes:
             attr=[c for c in codes if c==word]
             if attr:
                attr=attr[0]
                obj=None
                if IDE_CC_objType:
                   obj=getattr(IDE_CC_objType,attr)
                elif attr!='__init__':
                   try:
                      obj=getattr(IDE_CC_TEMP,attr)
                   except:
                      try:
                         obj=__builtins__[attr]
                      except:
                         pass
                if obj:
                   wrapWidth=clampScalar(0,IDE_frameColWidth-4,IDE_CFG[CFG_CTwrapWidth])
#                    print 'OBJ:',obj
                   # first priority is the definition source
                   args=IDE_inspectDefSource(obj,wrapWidth=wrapWidth)
                   if not args and hasattr(obj,'__init__'):
                      args=IDE_inspectDefSource(obj.__init__,wrapWidth=wrapWidth)
                   # inspects it
                   if not args:
                      args=IDE_CC_getArgSpec(obj,wrapWidth=wrapWidth)
                      if not args and hasattr(obj,'__init__'):
                         args=IDE_CC_getArgSpec(obj.__init__,wrapWidth=wrapWidth)
                      if args:
                         args=( '%s(%s)'%(word,args) ).replace('\n','\n'+' '*(wordLen+1))
                   if args:
                      anyArg=True
                      hasKW=True
                      wholeDefLines.append(args)
                   else:
                      args=obj.__doc__
                      if args:
                         cppIntf=args.find('C++ Interface:')>-1
                         if cppIntf:
                            slashes=args.find('//')
                            # cuts P3D C++ docs started with slashes line
                            if slashes>-1:
                               args=args[:slashes]
                            defLines=args.strip().splitlines()
                            if '' in defLines:
                               del defLines[defLines.index(''):]
                            hasKW=True
                            wrappedDefLines=[defLines[0]]
                            wholeDefLines=[]
                            # strips instance argument and wipes all not important
                            # keywords, eg. const/non-const, so
                            # only "type name,"'s are left
                            for ds in sorted(defLines[1:]):
                                oBr=ds.find('(')
                                cBr=ds.find(')')
                                argSpl=re.split('\s*,\s*',ds[oBr+1:cBr])
                                if argSpl and argSpl[0].split(' ')[-1]=='this':
                                   del argSpl[0]
                                lastType=None
                                argsLine=ds[:oBr+1] # 'word('
                                argsLineLen=len(argsLine)
                                for a in range(len(argSpl)):
                                    last2=argSpl[a].split(' ')[-2:]
                                    if last2:
                                       # remove the type if it's still the last one
                                       if lastType==last2[0]:
                                          del last2[0]
                                       else:
                                          lastType=last2[0]
                                       last2=' '.join(last2)
                                       last2Len=len(last2)+2
                                       # wrap it
                                       if argsLineLen+last2Len>wrapWidth:
                                          argsLine+='\n'+' '*(wordLen+1)
                                          argsLineLen=wordLen+1
                                       argsLine+=last2+', '
                                       argsLineLen+=last2Len
                                argsLine=argsLine.rstrip(', ')+')'
                                wrappedDefLines+=argsLine.splitlines()
                                wholeDefLines.append(argsLine)
                                anyArg=True
                            args=wrappedDefLines
                         else: # must be python builtin functions
                            for l in args.splitlines():
                                oBr=l.find(word+'(')
                                cBr=l.find(')')
                                if 0==oBr<cBr:
                                   anyArg=True
                                   args=l
#                                    args=l[:cBr+1]
#                                    print 'ARGS:',args
                                   wholeDefLines.append(l[:cBr+1])
                                   break
       if args:
#           print 'ARGS:\n%s'%args
          CT=IDE_doc.callTipParent.find('**/CT')
          if not CT.isEmpty(): CT.removeNode()
          argsLines=args if type(args)==list else args.split('\n')
          callTip=IDE_doc.callTipParent.attachNewNode('')
          callTip.setName('CT')
          callTipText=IDE_CC_createText(argsLines)
          callTipText.reparentTo(callTip)
          buttonsWidth=0
          bmin,bmax=callTip.getTightBounds()
          if anyArg:
             dbScale=IDE_lineheight
             xMul=IDE_all_chars_maxWidth/dbScale
             zMul=IDE_lineheight/dbScale
             numButtons=0
             aidx=0
             for al in range(len(argsLines)):
                 b=-(al+1)*zMul+IDE_chars_maxBaseline2top*IDE_lineheight*.5
                 t=-(al)*zMul+IDE_chars_maxBaseline2top*IDE_lineheight*.5
                 line=argsLines[al]
                 isFirstLine=line[:wordLen+1]==word+'('
                 if isFirstLine:
                    dl=wholeDefLines[aidx]
                    oBr=dl.find('(')
                    cBr=dl.rfind(')')
                    if dl and -1<oBr<cBr-1:
                       db=DirectButton(text='',parent=callTipText,
                          scale=dbScale,
                          frameColor=Vec4(0),
                          frameSize=(-zMul,0,b,t),
                          frameTexture=IDE_CTargsInsertTex,relief=DGG.FLAT,
                          command=IDE_paste,
                          extraArgs=[dl[oBr+1:cBr].replace(' '*(oBr+1),'')],
                          suppressMouse=0,rolloverSound=0,clickSound=0, enableEdit=0
                          )
                       dbCen=db.getCenter()
                       db.setZ(db,dbCen[1])
                       db.setColorOff(1)
                       db.setTag('arguments',db['extraArgs'][0])
                       numButtons+=1
                    aidx+=1
                 if hasKW: # creates button for individual argument
                    if isFirstLine:
                       oBr=line.find('(')
                       kws=line[oBr+1:]
                    else:
                       kws=line
                    searchStart=0
                    for kw in splitArgs(kws.rstrip(')')):
                        if kw=='': continue
                        if cppIntf:
                           if al==0: continue
                           kw=kw.split()[-1]
                           kwPos=line[searchStart:].rfind(kw)
                        else:
                           kwPos=line[searchStart:].find(kw)
                        oldSearchStart=searchStart
                        searchStart+=kwPos+len(kw)
                        l=(kwPos+oldSearchStart)*xMul
                        r=searchStart*xMul
                        db=DirectButton(text='',parent=callTipText, scale=dbScale,
                           frameSize=(l,r,b,t), frameColor=Vec4(0),
                           command=IDE_paste, extraArgs=[kw+', '],
                           suppressMouse=0,rolloverSound=0,clickSound=0,pressEffect=None,
                           enableEdit=0, sortOrder=-10
                           )
                        # only show it if over or pressed
                        hilit=IDE_CTargHL.instanceUnderNode(db.stateNodePath[1],'')
                        hilit.instanceTo(db.stateNodePath[2])
                        hilit.setPos(l,0,t)
                        hilit.setSx(r-l)
             if numButtons:
                callTipText.setX(dbScale)
                bmin.addX(-dbScale)
                buttonsWidth=dbScale
          scale=bmax-bmin
          Zoffset=len(argsLines)+.4
          # off top edge
          if IDE_canvas.getZ()/IDE_lineScale[2] > z-Zoffset:
             Zoffset=-1.35
          xpos=clampScalar( -IDE_canvas.getX()/IDE_textScale[0],
                            (IDE_frameWidth-IDE_canvas.getX())/IDE_textScale[0]-scale[0],
                            (x-len(word))*IDE_all_chars_maxWidth-buttonsWidth )
          callTip.setPos(xpos,0,(-z+Zoffset)*IDE_lineheight)
          callTip.setColor(IDE_COLOR_callTipsText)
          IDE_doc.callTipBG['frameSize']=Vec4(0,scale[0],-scale[2],0)
          IDE_doc.callTipBG.setPos(callTipText,Point3(bmin[0],0,bmax[2]))
          IDE_doc.callTipParent.show()
          IDE_doc.callTipParent.setPos(0,0,0)
          IDE_doc.callTipInsertIdx=0
          IDE_updateCallTipAlpha()
          return
    IDE_doc.hideCallTip()
    IDE_doc.line,IDE_doc.column = lastLC

def IDE_insertCallArgs():
    if IDE_doc.callTipParent.isHidden(): return
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    b=[b for b in asList(IDE_doc.callTipParent.findAllMatches('**/+PGButton')) if b.hasTag('arguments')]
    bLen=len(b)
    if bLen==1:
       IDE_paste(b[0].getTag('arguments'))
    elif bLen>0:
       if IDE_doc.isSelecting:
          startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
#           sel=IDE_getSelection()
#           print sel
          idx=IDE_doc.callTipInsertIdx
          IDE_doc.callTipInsertIdx=(IDE_doc.callTipInsertIdx+1)%bLen
       else:
          startLine,startCol=IDE_doc.line,IDE_doc.column
          idx=0
          IDE_doc.callTipInsertIdx=1
       IDE_paste(b[bLen-1-idx].getTag('arguments'))
       IDE_setSelAnchor(startLine,startCol)
       IDE_doc.isSelecting=True
       IDE_updateBlock()

def IDE_showAvailCodes(later=True,forced=0,displayCC=True):
    global IDE_CC_autoComplete,IDE_CC_sttBegin,IDE_CC_sttEnd,\
           IDE_CC_isSnippet,IDE_CC_isImport,IDE_CC_locs, IDE_CC_objType
    IDE_hideSGB()
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if not IDE_doc.hilight or (IDE_doc.isSelecting and displayCC) or not (IDE_CC_autoComplete or forced):
       return
    if later:
       IDE_delayCompletion()
       return

    IDE_CC_isSnippet=IDE_CC_isImport=False

    def isModule(f):
        name,ext=os.path.splitext(f)
        return (name!='__init__' and ext[:3]=='.py') or ext in DYN_LIB_EXT

    def has__init__(d):
        inits=[p for p in glob(joinPaths(d,'__init__.py?')) if not (p.endswith('.pyx') or p.endswith('.pyd'))]
        return len(inits)>0

    def tempImport(importStr,line,fromImp=None):
        commaPos=importStr.rfind(',')
        if commaPos>-1:
           importStr=importStr[:7]+importStr[commaPos+1:]
        global IDE_CC_locs, IDE_CC_isImport
        importLine_CC_TEMP.cleanup()
        try:
           importLine_CC_TEMP.doImport(importStr+('' if fromImp is None else ' as '+fromImp))
           IDE_CC_locs=(importLine_CC_TEMP if fromImp is None else getattr(importLine_CC_TEMP,fromImp),)
#            stdAttr=('__builtins__','core','fullpath')
#            keys=[k for k in IDE_CC_locs[0].__dict__ if k not in stdAttr]
#            imported=IDE_CC_locs[0].__dict__[keys[0]]
           importedName='importLine_CC_TEMP.'+ (importStr[7:] if fromImp is None else fromImp)
           imported=eval(importedName)
           if hasattr(imported,'__file__'):
              importedFile=imported.__file__
              importedPath=os.path.dirname(importedFile)
              #print 'importedPath:',importedPath
   #            isPackage=importStr.endswith(os.path.basename(importedPath))
              isPackage=os.path.basename(importedFile)[:11]=='__init__.py'
           else:
              isPackage=False
           #print 'isPackage:',isPackage
           #print 'fromImp:',fromImp
           importDict={}
#            lastCWD=os.getcwd()
#            os.chdir(os.path.dirname(importedPath))
           if isPackage:
              packages=[]
              modules=set()
              for i in glob(joinPaths(importedPath,'*')):
                  name=os.path.basename(i)
                  if os.path.isdir(i):
                     packages.append(i)
                  elif isPackage and isModule(name):
                     name,ext=os.path.splitext(name)
                     if name not in ('TaskTester',):
                        modules.add(os.path.splitext(i))
              for p in packages:
                  if has__init__(p):
                     name=os.path.basename(p)
                     try:
                         exec((importStr+'.'+name), IDE_CC_locs[0].__dict__)
                         importDict[name]=eval(importedName+'.'+name)
                     except:
                         pass
              for m,e in modules:
                  name=os.path.basename(m)
                  try:
                      impSpl=''.join(importStr.split()[1:]).split('.')
                      if impSpl[0]=='direct' and impSpl[1] in IDE_CC_excludedPackages:
                         fakeModule=types.ModuleType('')
                         fakeModule.__file__=m+e
                         importDict[name]=IDE_CC_locs[0].__dict__[name]=imported.__dict__[name]=fakeModule
                      else:
                         exec((importStr+'.'+name), IDE_CC_locs[0].__dict__)
                         importDict[name]=eval(importedName+'.'+name)
                  except:
                      pass
           else:
              if fromImp is None:
                 for k,v in list(imported.__dict__.items()):
                     if isinstance(v,types.ModuleType) and v.__name__!=k and \
                          ( ( hasattr(imported,'__all__') and k in imported.__all__) or imported==panda3d ):
                        importDict[k]=v
                 if len(importDict)==0:
                    IDE_CC_locs=()
              else:
                 if hasattr(imported,'__module__') and sys.modules[imported.__module__]==panda3d:
                    importDict = dict( ((attrInLibs,getattr(imported,attrInLibs)) for attrInLibs in imported.__all__) )
                    # an alternative, involving codes from panda3d.py,
                    # DON'T USE, in case of future changes in the module
#                     importDict = {}
#                     for libInP3DMod in imported.__libraries__:
#                         importDict.update(imported.__manager__.libimport(libInP3DMod).__dict__)
                 else: 
                    importDict = IDE_CC_locs[0].__dict__
#                  print 'importDict:',importDict.keys()
           setattr(imported,IDE_CC_IMPdictName,importDict)
           IDE_CC_isImport=True
#            os.chdir(lastCWD)
           return True if fromImp is None else imported#IDE_CC_locs[0]
        except Exception:
           IDE_CC_cancel()
           taskMgr.removeTasksMatching(IDE_CC_tasksName)
           IDE_doc.removeErrHLivals()
           # clears all errors notification
           for e in asList(IDE_doc.blockParent.findAllMatches('**/error')):
               e.removeNode()
           print(IDE_errShoutout)
           traceback.print_exc()
           IDE_processException(traceback.format_exc(),line)
           return False

    def tempModImport(impStr):
        commaPos=impStr.rfind(',')
        if commaPos>-1:
           impStr=impStr[:7]+impStr[commaPos+1:]
#         print 'impStr:',impStr
        importLine_CC_TEMP.cleanup()
        impDict={}
        setattr(importLine_CC_TEMP,IDE_CC_IMPdictName,impDict)
        impStrRst=impStr.rstrip()
        impAll=len(impStrRst.split())==1
        impWord=''
        if not impAll:
           impStrSp=impStr.split()
           impWord=impStrSp[-1]
        deprecated=IDE_CC_deprecated if IDE_CFG[CFG_excludeOldMods] else ()
        # builtin modules
        for m in set(sys.builtin_module_names).difference(deprecated):
            if impAll or ( (matchStart and m.lower().find(impWord)==0) or\
                           (matchAny and m.lower().find(impWord)>-1) ):
               try:
                   importLine_CC_TEMP.doImport('import '+m)
                   exec(('import '+m), impDict)
               except:
                   pass
        # scan paths
        scanPaths=set(sys.path) # scans file location only once, use set
        if hasattr(IDE_doc,'DirName') and IDE_doc.DirName:
           scanPaths.add(IDE_doc.DirName)
        for p in scanPaths:
            # not yet support zip files
            if os.path.isdir(p):
               if ( # excludes old main file CWD, if it's not actually the main module
                  p==OldAPP_CWD and OldAPP_CWD!=APP_CWD) or \
                  ( # excludes main file CWD, if it's not the active file
                  hasattr(IDE_doc,'DirName') and p==APP_CWD and p!=IDE_doc.DirName):
                  continue
               for d in glob(joinPaths(p,'*')):
                   name=os.path.basename(d)
                   if os.path.isdir(d):
                      if has__init__(d) and\
                         ( impAll or ( (matchStart and name.lower().find(impWord)==0) or\
                                       (matchAny and name.lower().find(impWord)>-1) )
                         ):
                         try:
                             importLine_CC_TEMP.doImport('import '+name)
                             exec(('import '+name), impDict)
                         except:
                             pass
                   elif isModule(name):
                      name=os.path.splitext(name)[0]
                      illegalName=False
                      for ni in name:
                          if ni in myPunctuationWhitespace:
                             illegalName=True
                             break
                      if illegalName or name in deprecated: continue
                      if impAll or ( (matchStart and name.lower().find(impWord)==0) or\
                         (matchAny and name.lower().find(impWord)>-1) ):
                         try:
                             # only import trusted modules, ie. under python installation
                             if d.find(PY_DIR)==0:
                                importLine_CC_TEMP.doImport('import '+name)
                                exec(('import '+name), impDict)
                             else:
                                fakeModule=types.ModuleType('')
                                fakeModule.__file__=d
                                impDict[name]=importLine_CC_TEMP.__dict__[name]=fakeModule
                         except:
                             pass
        if '__builtins__' in impDict:
           del impDict['__builtins__']
        IDE_CC_display(sorted(impDict.keys()),attr=impWord,objType=importLine_CC_TEMP,displayCC=displayCC)

    taskMgr.remove(IDE_CC_tasksName)
    matchStart=IDE_CC_MODE==IDE_CC_MODE_start
    matchAny=IDE_CC_MODE==IDE_CC_MODE_anywhere

    s=IDE_doc.File[IDE_doc.line]
    if not len(s.strip()):
       return
    col=IDE_doc.column
    left=s[:col]
    for i in range(len(left)-1,-1,-1):
        if (
           left[i] in string.whitespace or
           (left[i] in myPunctuation and left[i]!='.')
           ):
           left=left[i+1:]
           break
    right=s[col:]
    IDE_CC_sttBegin=col
    IDE_CC_sttEnd=col+len(right.rstrip()) # don't include the EoL
    if right:
       for i in range(len(right)):
           if right[i] in myPunctuationWhitespace:
              right=right[:i]
              IDE_CC_sttEnd=col+i
              break
    statement=(left+right).strip()
    if len(statement)==0:
       currL=IDE_doc.File[IDE_doc.line]
       fromPos=currL.find('from ')
       impPos=currL.find(' import ')
       impLStripPos=currL.find('import ')
       fromExists=-1<fromPos<IDE_CC_sttBegin
       impExists=-1<impPos<IDE_CC_sttBegin
       impLStripExists=-1<impLStripPos<IDE_CC_sttBegin
       # "from a import "
       if -1<fromPos<IDE_CC_sttBegin and -1<impPos<IDE_CC_sttBegin and (impPos>fromPos):
          impStr=currL[fromPos:impPos].replace('from','import')
          tmpImp=tempImport(impStr,IDE_doc.line+1,fromImp='fromimport')
          if tmpImp:
             IDE_CC_display(sorted(getattr(tmpImp,IDE_CC_IMPdictName).keys()),objType=tmpImp,displayCC=displayCC)
       # "from " or "import " only
       elif fromExists+impLStripExists==1:
          impStr=currL[fromPos if fromExists else impLStripPos:IDE_CC_sttEnd].replace('from ','import ')
          tempModImport(impStr)
       # looks for call tip (or at least documentation)
       elif displayCC:
          IDE_createCallTips(IDE_CC_sttBegin)
       return

    print('#####################', file=IDE_DEV)
    print('  ', statement, file=IDE_DEV) #,tuple(word)
    print('=====================', file=IDE_DEV)

    IDE_CC_locs=(
          __builtins__, # 1st priority : Python built-in
          IDE_CC_TEMP, # active file's imported stuff
#           sys.modules[APP.moduleName], # app's main module
          )
    words=statement.split('.')
    wLen=len(words)

    ############################################################################
    if wLen==1: # A SINGLE WORD
       word=words[0].lower()
#        # finds out the current block's 1st column,
#        # respects comma, colon, and backward slash,
#        # finds the previous line without them
#        line1stCol=-1
#        for l in range(IDE_doc.line-1,-1,-1):
#            s=IDE_doc.File[l].rstrip()
#            if len(s) and s[-1] not in '.\\:':
#               if l==IDE_doc.line-1:
#                  line1stCol=IDE_doc.File[IDE_doc.line].find(IDE_doc.File[IDE_doc.line].lstrip())
#               else:
#                  line1stCol=s.find(s.lstrip())
#               break
#        if line1stCol==-1:
#           line1stCol=IDE_doc.File[0].find(IDE_doc.File[0].lstrip())
       all=[]
       temp=set()
       print('( %s )'%word, file=IDE_DEV)
       impStr=None
       # is it import line ?
       if IDE_doc.quoted[IDE_doc.line]==0: # don't process string or docstring
          currL=IDE_doc.File[IDE_doc.line]
          fromPos=currL.find('from ')
          impPos=currL.find(' import ')
          impLStripPos=currL.find('import ')
          fromExists=-1<fromPos<IDE_CC_sttBegin
          impExists=-1<impPos<IDE_CC_sttBegin
          impLStripExists=-1<impLStripPos<IDE_CC_sttBegin
          # "from a import b"
          if fromExists and impExists and (impPos>fromPos):
             impStr=currL[fromPos:impPos].replace('from','import')
             if not tempImport(impStr,IDE_doc.line+1,fromImp='fromimport'):
                return
          # "from " or "import " only
          elif fromExists+impLStripExists==1:
             impStr=currL[fromPos if fromExists else impLStripPos:IDE_CC_sttEnd].replace('from ','import ')
             impStrSp=impStr.split()
             if len(impStrSp)==2:
                tempModImport(impStr)
                return
             else:
                impStr=None
       if not impStr:
          # LOOK IN KEYWORDS
          for i in IDE_SYNTAX_keyword:
              if ( (matchStart and i.lower().find(word)==0) or\
                   (matchAny and i.lower().find(word)>-1)
                 ) and i not in all:
                   temp.add(i)
          all+=sorted(temp)
          temp=set()
          # code's local scope, since the later definition overrides the former,
          # so scan the previous lines until out of scope
          scopeStartReached=0
          scopeStartCol=-1
          for l in range(IDE_doc.line,-1,-1):
              s=IDE_doc.File[l].rstrip()
              if len(s.strip()):
                 sl=s.lstrip()
                 sls=sl+' '
                 slsLen=len(sls)
                 # out of block
                 if not len(sl) or sls[0]=='#': # ignore comments
                    continue
                 elif scopeStartReached and s.find(sl)>scopeStartCol:
                    print('OUT OF BLOCK', file=IDE_DEV)
                    break
                 elif ( (slsLen>3 and sl[:3]=='def') or (slsLen>5 and sl[:5]=='class') ):
                    scopeStartCol=s.find(sl)
                    scopeStartReached=1
                 wBeg=0
                 pw=sls[0] in myPunctuationWhitespace # punct+whitespc start status
                 for e in range(slsLen):
                     # currently not walking on punct+whitespc, must be word's end
                     if not pw and sls[e] in myPunctuationWhitespace:
                        pw=1
                        w=sls[wBeg:e]
   #                      print>>IDE_DEV, w
                        # possibly the word user wants
                        if words[0]!=w and (
                             (matchStart and w.lower().find(word)==0) or
                             (matchAny and w.lower().find(word)>-1)
                           ) and w not in all:
                             temp.add(w)
                     # currently walking on punct+whitespc, must be word's begin
                     elif pw and sls[e] in myLettersDigits:
                        pw=0
                        wBeg=e
          all+=sorted(temp)
       for loc in IDE_CC_locs:
           temp=set()
           for i in list(getattr(loc,IDE_CC_IMPdictName).keys()) if IDE_CC_isImport else LIST_ITEMS(loc):
               if ( (matchStart and i.lower().find(word)==0) or\
                    (matchAny and i.lower().find(word)>-1)
                  ) and i not in all:
                    temp.add(i)
           all+=sorted(temp)
#        for i in all:
#            print>>IDE_DEV, i
#       print>>IDE_DEV, '====================================='
#        if len(all)==1 and all[0]==words[0]:
#           del all[0]
       IDE_CC_display(all,attr=words[0],displayCC=displayCC)
       if not all and displayCC:
          IDE_createCallTips(IDE_CC_sttBegin)
       return

    ############################################################################
    else: # NESTED ATTRIBUTES
       fullwords=statement.rstrip('.')
       print('fullwords:',fullwords, file=IDE_DEV)
       # first of all, I have to figure out what the user used to call an instance,
       isInst=0
       for l in range(IDE_doc.line-1,-1,-1):
           s=IDE_doc.File[l].lstrip()
           if len(s)>3 and s[:3]=='def':
              br1=s.find('(')
              br2=s.find(')')
              if br1>-1 and br2>br1+1:
                 inst=s[br1+1:br2].split(',')[0].strip() # get the 1st arg
                 if inst and inst[0] in myLettersScore:
                    isInst=1
                    lastDefLine=l
                 break
       isInstAttr=0
       if isInst:
          print('USER USES "%s" HERE TO REFER TO AN INSTANCE'%inst, file=IDE_DEV)
          if words[0]==inst:
             isInstAttr=1
             print('this is an instance attribute', file=IDE_DEV)

       # CLASS INSTANCE ATTRIBUTE
       if isInstAttr:
          # look upward to find class definition
          className=''
          classDefLine=0
          for l in range(lastDefLine-1,-1,-1):
              s=IDE_doc.File[l].strip()
              sLen=len(s)
              classDefCol=s.find('class')
              if not sLen or (sLen and (s[0]=='#' or classDefCol<0)): # ignore comments
                 continue
              colonPos=s.find(':')
              if colonPos<0:
                 className=s[classDefCol+5:].strip()
              else:
                 className=s[classDefCol+5:colonPos].strip()
              classDefLine=l
              break
          print('className:',className, file=IDE_DEV)

          lineBreak='\\,('
          inst=None
          instAttrs=[]
          instAttrTypes=[]
          # STORES ALL CLASS INSTANCE ATTRIBUTES
          # NOTE: for now, let's put aside class' static attributes
          ignoredUntilLine=-1
          for l in range(classDefLine+1,IDE_doc.numLines):
              if ignoredUntilLine>l:
                 continue
              s=IDE_doc.File[l].strip()
              sLen=len(s)
              if not sLen or (sLen and s[0]=='#'): # ignore comments
                 continue
              elif sLen and IDE_doc.File[l].find(s)<=classDefCol: # out of scope
#                  print>>IDE_DEV, '######',s
                 break
              elif sLen>3 and s[:3]=='def':
                 br1=s.find('(')
                 br2=s.find(')')
                 if br1 and br2 and br2>br1:
                    methodName=s[3:br1].strip()
                    if (matchStart and methodName.lower().find(words[1])==0) or\
                       (matchAny and methodName.lower().find(words[1])>-1):
                       # adds the method to the list too
                       instAttrs.append(methodName)
                    # gets the passed in instance ref
                    args=s[br1+1:br2].strip().split(',')
                    if args:
                       inst=args[0] # get the 1st arg
                       instLen=len(inst)
                       print('III:',inst, file=IDE_DEV)
              elif inst is not None:
                 instPos=s.find(inst)
                 equalPos=s.find('=')
                 if instPos<0 or equalPos<0:
                    continue
                 attr=''.join( s[instPos:equalPos].split() )[instLen+1:]
                 attr=attr.split('.')[0]
                 if attr in instAttrs:
                    continue
                 if (matchStart and attr.lower().find(words[1])==0) or\
                    (matchAny and attr.lower().find(words[1])>-1):
                    instAttrs.append( attr )
                    # try to find out what its value type is
                    semiColonPos=s.find(';')
                    if semiColonPos<0:
                       valEnd=sLen
                    else:
                       valEnd=semiColonPos
                    valS=s[equalPos+1:valEnd].strip()
                    # line break
                    if s[valEnd-1] in lineBreak:
                       LB_1_isBR=valS[-1]=='('
                       print('LB_1_isBR :',LB_1_isBR, file=IDE_DEV)
                       for nl in range(l+1,IDE_doc.numLines):
                           s=IDE_doc.File[nl].strip()
                           sLen=len(s)
                           if not sLen or (sLen and s[0]=='#'): # ignore comments
                              continue
                           if valS[-1]=='\\':
                              valS=valS[:-1]+s
                           else:
                              valS+=s
                           if LB_1_isBR:
                              if valS.count('(')==valS.count(')'):
                                 LB_1_isBR=0
                           if s[-1] not in lineBreak and not LB_1_isBR:
                              ignoredUntilLine=nl
                              break
                    print('_________________________________________________', file=IDE_DEV)
                    print('valS:',valS, file=IDE_DEV)

   #                  sqBr1=valS.find('[')
   #                  rndBr1=valS.find('(')
   #                  comma1=valS.find(',')
   #                  if sqBr1==0:
   #                     val=[]
   #                  elif rndBr1==0 and comma1>0:
   #                     val=()
   #                  elif rndBr1==0 and comma1>0:
   #
   #
   #                  br1=valS.find('(')
   #                  mayBeAClass=valS[:br1]

                    # this is crazy, done by actually running the assignment
                    print('>>',attr, file=IDE_DEV)
                    br1=valS.find('(')
                    try:
                       val=IDE_CC_TEMP.doExec(attr+'='+valS)
                       print('val:',val, file=IDE_DEV)
                       print(type(val), file=IDE_DEV)
                       valType=val.__class__
                       print('valType:',valType, file=IDE_DEV)
   #                     print>>IDE_DEV, vars(valType).keys()
                       instAttrTypes.append(valType)
                    except NameError:
                       print(file=IDE_DEV)
                       traceback.print_exc()
                       IDE_CC_TEMP.__dict__[attr]=myFinder.getBrokenInst(valS[:br1],noModuleName=1)
                       excLines=traceback.format_exc().splitlines()
                       nameErr=excLines[-1].split('\'')[-2]
                       print('XXX',nameErr, file=IDE_DEV)
                       instAttrTypes.append(None)
                       print('valType: hard to say', file=IDE_DEV)
                    except:
                       print(file=IDE_DEV)
                       traceback.print_exc()
                       IDE_CC_TEMP.__dict__[attr]=myFinder.getBrokenInst(valS[:br1],noModuleName=1)
                       instAttrTypes.append(None)
                       print('valType: hard to say', file=IDE_DEV)
          # and finally rolls back the instantiation process
          myFinder.clearVisitedInstances()
          myFinder.crushInstance(CC_TEMP,IDE_CC_TEMP)
          print('\nCRUSHED:\n',list(IDE_CC_TEMP.__dict__.keys()), file=IDE_DEV)

          instAttrs.sort()
#           print>>IDE_DEV, '\nINST ATTRS:\n',instAttrs
          IDE_CC_display(instAttrs,attr=words[-1],displayCC=displayCC)
          if not instAttrs and displayCC:
             IDE_createCallTips(IDE_CC_sttBegin)
          return


       else: # NOT THE CLASS' INSTANCE ATTRIBUTE
          print("NOT THE CLASS' INSTANCE ATTRIBUTE", file=IDE_DEV)
          print('[ %s ]'%words[0], file=IDE_DEV)
          impStr=None
          # is it an import line ?
          if IDE_doc.quoted[IDE_doc.line]==0: # don't process string or docstring
             currL=IDE_doc.File[IDE_doc.line]
             fromPos=currL.find('from ')
             impPos=currL.find('import')
             # "import a.b"
             if -1<impPos<IDE_CC_sttBegin:
                # "from a import b.c" is a SYNTAX ERROR
                if -1<fromPos and fromPos<impPos:
                   msg=createMsg('Python does NOT support "from a import b.OBJECT"',bg=(1,0,0,.85))
                   putMsg(msg,'imp err',3,stat=True)
                   IDE_CC_cancel()
                   return
                else:
                   impStr=currL[impPos:IDE_CC_sttBegin]
                   impStr=impStr[:impStr.rfind('.')]
                   if not tempImport(impStr,IDE_doc.line+1):
                      return
             else:
                fromStr=currL[fromPos:IDE_CC_sttBegin]
                # "from a.b"
                if -1<fromPos<IDE_CC_sttBegin and len(fromStr.split())==2:
                   rightMostDot=currL[:IDE_CC_sttBegin].rfind('.')
                   impStr=currL[fromPos:rightMostDot].replace('from','import')
                   if not tempImport(impStr,IDE_doc.line+1):
                      return
          if not impStr:
             # looks for assignment line
             assignment=None
             REptr_ass=re.compile(r'\b%s\s*='%words[0])
             # includes current line, who knows the assignment is also in this line
             for l in range(IDE_doc.line,-1,-1):
                 if IDE_doc.quoted[l]>0: # don't process string or docstring
                    continue
                 s=IDE_doc.File[l]
                 if l==IDE_doc.line:
                    s=s[:IDE_CC_sttBegin]
                 res=REptr_ass.search(s)
                 if res:
                    assStart=res.start(0)
                    if IDE_doc.hilight:
                       isQuoted,color=IDE_doc.getLineQuotedNColor(l)
                       charsColor=IDE_doc.hilightLine(s[:assStart+1],color,isQuoted)[-1]
                       if charsColor and charsColor[-1] in COLORIDX_notCode:
                          continue
                    assignment=s[assStart:]
                    assLen=len(assignment)
                    semiCol=assignment.find(';')
                    comment=assignment.find('#')
                    crap=0
                    if semiCol>-1:
                       crap=semiCol
                    if comment>-1:
                       crap=min(crap,comment) if crap else comment
                    if crap:
                       assignment=assignment[:crap] # cuts comment and new statement
                    else: # multilines assignment
                       pass
                    if assignment:
                       print('ASS:',assignment, file=IDE_DEV)
                       Obr=assignment.find('(')
                       if Obr==-1: Obr=None
                       words[0]=assignment[assignment.find('=')+1:Obr].strip()
                       break

          numFound=0
          lastItem=None
          locs=IDE_CC_locs
          for word in words[:-1]:
              print('[ %s ]'%word, file=IDE_DEV)
              wordLen=len(word)
              gotoNext=0
              for loc in locs:
                  found=0
                  item=None
                  for i in LIST_ITEMS(loc):
                      # MUST MATCH ENTIRELY, INCLUDING THE CASE
                      if i==word:
                         lastItem=GET_ITEM(loc,i)
                         try:
                             print('found :',lastItem, file=IDE_DEV)
                         except:
                             pass
                         found=1
                         break
                  if found:
                     if lastItem is not None:
                        gotoNext=1
                     break
              if gotoNext:
                 locs=[lastItem] # define search location for the next attr
                 numFound+=1
                 continue
              else:
                 print('LAST FOUND :',lastItem, file=IDE_DEV)
                 break

          if numFound==wLen-1:
             word=words[-1].lower()
             all=[]
             temp=[]
             print('--> ( %s )'%word, file=IDE_DEV)
             for i in getattr(lastItem,IDE_CC_IMPdictName) if IDE_CC_isImport else LIST_ITEMS(lastItem):
                 if (matchStart and i.lower().find(word)==0) or\
                    (matchAny and i.lower().find(word)>-1):
                      temp.append(i)
             all+=sorted(temp)
   #           for i in all:
   #               print>>IDE_DEV, i
      #            print>>IDE_DEV, getattr(lastItem,i).__doc__
#             print>>IDE_DEV, '====================================='
#              if len(all)==1 and all[0]==words[-1]:
#                 del all[0]
             IDE_CC_display(all,attr=words[-1],objType=lastItem,displayCC=displayCC)
             return
          elif displayCC:
             IDE_createCallTips(IDE_CC_sttBegin)
             return
    IDE_CC_cancel()

def IDE_showAvailSnippet():
    global IDE_CC_sttBegin, IDE_CC_sttEnd, IDE_CC_isSnippet, IDE_CC_locs
    IDE_hideSGB()
    if IDE_doc.readonly:
       warnReadonlyDoc()
       return
    if IDE_doc.isSelecting: return
    word=''
    s=IDE_doc.File[IDE_doc.line]
    col=IDE_doc.column
    if len(s.strip()):
       IDE_CC_sttBegin=col
       left=s[:col]
       for i in range(len(left)-1,-1,-1):
           if left[i] in myPunctuationWhitespace:
              left=left[i+1:]
              IDE_CC_sttBegin=i+1
              break
           if i==0:
              IDE_CC_sttBegin=0
       right=s[col:]
       IDE_CC_sttEnd=col+len(right.rstrip()) # don't include the EoL
       if right:
          for i in range(len(right)):
              if right[i] in myPunctuationWhitespace:
                 right=right[:i]
                 IDE_CC_sttEnd=col+i
                 break
       word=(left+right).strip()
    else:
       IDE_CC_sttBegin=IDE_CC_sttEnd=col

    wordLow=word.lower()
    snippetKeys=list(SNIPPETS.keys())
    if wordLow:
       matchStart=IDE_CC_MODE==IDE_CC_MODE_start
       matchAny=IDE_CC_MODE==IDE_CC_MODE_anywhere
       snippetKeys=[ k for k in snippetKeys
         if (matchStart and k.lower().find(wordLow)==0) or\
            (matchAny and k.lower().find(wordLow)>-1) ]
    # if no match at all, display the whole snippets instead of nothing
    if not snippetKeys:
       IDE_CC_sttBegin=IDE_CC_sttEnd=col
       snippetKeys=list(SNIPPETS.keys())
       word=''

    SnipType=lambda:0
    for k in snippetKeys:
        setattr(SnipType,k,SNIPPETS[k][0])
    IDE_CC_isSnippet=True
    IDE_CC_locs=[SnipType]
    IDE_CC_display(sorted(snippetKeys),attr=word,objType=SnipType)
    if IDE_objDescHidden:
       IDE_CC_toggleDesc(True)

def IDE_saveToSnippets():
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       if startLine==endLine: # a single line
          snip=IDE_doc.File[startLine][startCol:endCol]
       else:                  # multiple lines
          snip=IDE_doc.File[startLine][startCol:]
          for l in range(startLine+1,endLine):
              snip+=IDE_doc.File[l]
          snip+=IDE_doc.File[endLine][:endCol]
    else:
       snip=IDE_doc.File[IDE_doc.line]
    IDESnipMgr.openSnippetsManager(snip)

def IDE_saveSnippetsToDisk():
    dumpToFile(SNIPPETS, IDE_snippetsPath)

def IDE_CC_cancel():
    global IDE_CC_isSnippet
    if IDE_isInMode(MODE_completing):
       oldSelQuad=IDE_objDesc.canvas.find('**/selQuad')
       if not oldSelQuad.isEmpty(): oldSelQuad.removeNode()
       IDE_CC_root.hide()
       IDE_CC_isSnippet=False
       IDE_safeStep()
       IDE_setMode(MODE_active)

def IDE_CC_gotoNext(inc=1):
    if IDE_availCodesList.highlightNextItem(inc):
       last=IDE_availCodesList.getSelectionIndex()==IDE_availCodesList.getNumItems()-1
       IDE_CC_displayDesc(later=not last)

def IDE_CC_gotoPrev(inc=1):
    if IDE_availCodesList.highlightPrevItem(inc):
       IDE_CC_displayDesc(later=IDE_availCodesList.getSelectionIndex())

def IDE_CC_gotoFirst():
    if IDE_availCodesList.highlightItem(0):
       IDE_CC_displayDesc(later=False)

def IDE_CC_gotoLast():
    if IDE_availCodesList.highlightItem(IDE_availCodesList.getNumItems()-1):
       IDE_CC_displayDesc(later=False)

def IDE_CC_toggleDesc(status=None):
    global IDE_objDescHidden
    if status is not None:
       IDE_objDescHidden=status
    if IDE_objDescHidden:
       IDE_objDesc.show()
       IDE_objDescHidden=False
    else:
       IDE_objDesc.hide()
       IDE_objDescHidden=True
    IDE_CC_displayDesc(later=False)

def IDE_CC_cycleMode():
    global IDE_CC_MODE
    IDE_CC_MODE=(IDE_CC_MODE+1)%(IDE_CC_MODE_anywhere+1)
    IDE_CC_modeText['text']=IDE_CC_MODE_desc[IDE_CC_MODE]
    IDE_completion()

def IDE_CC_createText(codes,bold=False):
    codesLen=len(codes)
#     print>>IDE_DEV, '>>>>>>>>'
#     start=globalClock.getRealTime()
    dum=NodePath('')
    dum.setTexture(IDE_normal_chars_tex)
    Range=list(range(codesLen))
    display = [ dum.attachNewNode('') for i in Range ]
    chars=IDE_bold_chars if bold else IDE_normal_chars
    color=[COLORIDX_identifier if IDE_TDExtensionAvail else IDE_TEXT_COLORS[COLORIDX_identifier]]
    z=0
    for z in Range:
        lineParent=display[z]
        lineParent.setZ(-z*IDE_lineheight)
        line=codes[z]
        IDE_drawText(line,lineParent,color*len(line))
#     print>>IDE_DEV, codesLen,globalClock.getRealTime()-start
#     print>>IDE_DEV, '<<<<<<'
    return dum

def IDE_CC_toggleAutoComplete():
    global IDE_CC_autoComplete
    # if I want to switch it off, close the codes list too
    if IDE_CC_autoComplete:
       IDE_CC_cancel()
    IDE_CC_autoComplete=not IDE_CC_autoComplete
    msg=createMsg( 'Auto-Complete is %s'%['OFF','ON'][IDE_CC_autoComplete],
                       bg=(0, 1, 0, .85))
    msg.setBin('dialogsBin',0)
    putMsg(msg,'autoCMPL',1,stat=True)

def IDE_drawText(line,lineParent,charsColor):
    if IDE_TDExtensionAvail:
       IDE_TextDrawer.drawText(line,lineParent,charsColor)
    else:
       vdata = GeomVertexData('textline', GeomVertexFormat.getV3c4t2(), Geom.UHStatic)
       prim = GeomTriangles(Geom.UHStatic)
       vW = GeomVertexWriter(vdata, 'vertex')
       cW = GeomVertexWriter(vdata, 'color')
       tW = GeomVertexWriter(vdata, 'texcoord')

       Xoffset=Point3(-IDE_chars_offset,0,0)
       for char in line:
           if IDE_CHARS_lettersProps[char]:
              for p in IDE_CHARS_lettersProps[char][0]:
                  vW.addData3f(Xoffset+p)
           Xoffset.addX(IDE_all_chars_maxWidth)
       idx=0
       for char in line:
           if IDE_CHARS_lettersProps[char]:
              color4=charsColor[idx]
              cW.addData4f(color4)
              cW.addData4f(color4)
              cW.addData4f(color4)
              cW.addData4f(color4)
           idx+=1
       idx4=0
       for char in line:
           if IDE_CHARS_lettersProps[char]:
              for uv in IDE_CHARS_lettersProps[char][1]:
                  tW.addData2f(uv)
              prim.addConsecutiveVertices(idx4,3)
              prim.addVertices(idx4+3,idx4+2,idx4+1)
              idx4+=4
       prim.closePrimitive()
       geom = Geom(vdata)
       geom.addPrimitive(prim)
       geomNode = GeomNode('quads')
       geomNode.addGeom(geom)
       lineParent.attachNewNode(geomNode).setTransparency(1)

def IDE_cycleDoc(direction):
    if mustBeHalted(): return
    numDocs=len(IDE_documents)
    if numDocs==1: return
    IDE_hideSGB()
    docIdx=(IDE_documents.index(IDE_doc)+direction)%numDocs
    IDE_documents[docIdx].setDocActive()
    IDE_finishIndentCloseUpViewIval()

def IDE_WxBrowseFiles(openOrSave,callback,defaultDir='',doc=None):
    global IDE_lastBrowsePath
    if doc is None:
       doc=IDE_doc
    if openOrSave:
       defaultFile=''
    else:
       defaultFile=doc.FileName
    Fdlg = wx.FileDialog(None, 'Open files' if openOrSave else ('Save file as...' if openOrSave==0 else 'Save duplicate as...'),
        defaultFile=defaultFile,
        defaultDir=IDE_lastBrowsePath if openOrSave else (defaultDir if defaultDir else os.path.dirname(doc.FullPath)),
        style=(wx.OPEN|wx.MULTIPLE) if openOrSave else wx.SAVE|wx.FD_OVERWRITE_PROMPT)
    if Fdlg.ShowModal() == wx.ID_OK:
       sel=Fdlg.GetPaths() if openOrSave else Fdlg.GetPath()
       if openOrSave: # only save the browse path upon opening files, not upon saving
          IDE_lastBrowsePath=os.path.dirname(sel[0])
    else:
       sel=[]
       print('No file was selected.', file=IDE_DEV)
    Fdlg.Destroy()
    IDE_setWindowForeground()
    Sequence(
       Wait(.1),
       Func(callback,sel),
       name=IDE_ivalsName+'go process files'
       ).start()

def IDE_pickFiles(mode):
    global IDE_lastMode
    if IDE_isInMode(MODE_completing):
       IDE_CC_cancel()
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_pickFiles)
    if mode=='open':
       IDE_spawnWxModal(IDE_WxBrowseFiles,(True,IDE_openFiles))
    elif mode=='saveas':
       if IDE_doc.FullPath:
          IDE_spawnWxModal(IDE_WxBrowseFiles,(False,IDE_saveFileAs))
       else:
          IDE_doc.saveFile()

def IDE_newDoc(fullpath=None):
    if fullpath:
       IDE_openFiles(fullpath)
    else:
       IDE_hideSGB()
       IDE_documents.append(IDE_document(fullpath))
       IDE_documents[-1].setDocActive(arrangeTabs=1)
       if IDE_isInMode(MODE_noFile):
          IDE_setMode(MODE_active)

def IDE_saveDocDuplicateAs():
    IDE_spawnWxModal(IDE_WxBrowseFiles,(None,IDE_doc.saveDuplicateAs,IDE_doc.DirName if IDE_doc.FullPath else os.path.dirname(APP_mainFile)))

def IDE_closeDoc(doc=None):
    if doc is None:
       doc = IDE_doc
    IDE_hideSGB()
    if doc.isChanged:
       M.IDE_lastMode=IDE_getMode()
       IDE_setMode(MODE_exiting)
       IDE_openYesNoCancelDialog('%s\n has changed, but not saved yet.\nDo you want to save it ?%s'%(doc.FileName,"\n\nnote: you're currently recording macro"*doc.recordMacro),IDE_closeDocConfirmed,doc)
    else:
       IDE_doCloseDoc(doc)

def IDE_closeDocConfirmed(doc,result,task=None):
    if result is None:
       IDE_setMode(IDE_lastMode)
    elif result:
       IDE_DO.acceptOnce(IDE_EVT_fileSaved,Functor(IDE_doCloseDoc,doc))
       doc.saveFile()
    else:
       IDE_doCloseDoc(doc)

def IDE_doCloseDoc(doc):
    global IDE_doc, IDE_log, IDE_recentFiles, IDE_lastDocB4Log
    IDE_setMode(IDE_lastMode)
    if doc.FullPath:
       if doc.FullPath in IDE_recentFiles:
          IDE_recentFiles.remove(doc.FullPath)
       if doc.valid:
          # brings the closed file to the top of recent files list
          IDE_recentFiles=([doc.FullPath]+IDE_recentFiles)[:IDE_CFG[CFG_recentFilesLimit]]
    # if this is the active doc, rescue the cursor
    isActiveDoc=IDE_doc==doc
    if isActiveDoc:
       IDE_textCursor.reparentTo(IDE_textCursorTmpParent)
    # If it's the log file, don't remove any part of it.
    # Instead, just "hide" it, so I can revive it later easily.
    if doc==IDE_log:
       doc.setInactive()
       doc.tab.stash()
       IDE_hiddenDocs.append(doc)
       LOG.setUpdateCallback(None)
       IDE_log=None
    else:
       IDE_setMessage('File \"%s\" closed.'%doc.FileName)
       IDE_saveFilesList() # always saves files list upon closing a file
       doc.tabBlink.pause()
       del doc.tabBlink
       doc.removeErrHLivals()
       doc.lineMarkParent.removeNode()
       doc.blockParent.removeNode()
       doc.textParent.removeNode()
       doc.tab.ignoreAll()
       doc.tab.destroy()
       doc.Files=None
       doc.Display=None
       doc.markedLines=None
       doc.markedColumns=None
       doc.errHLivals=None
       doc.errors=None
       IDE_docLocation.removeChildren()
    if IDE_doc.recordMacro:
       IDE_addMessage(' Macro recording aborted')
    IDE_doc.recordMacro=False
    idx=IDE_documents.index(doc) # get its index before removing it
    IDE_documents.remove(doc)
    if len(IDE_documents):
       if isActiveDoc:
          if IDE_lastDocB4Log in IDE_documents:
             idx=IDE_documents.index(IDE_lastDocB4Log)
             IDE_lastDocB4Log=None
          else:
             idx=max(0,idx-1)
          IDE_doc = None
          IDE_documents[idx].setDocActive(arrangeTabs=True)
       else:
          IDE_arrangeDocsTabs()
          IDE_exposeTab()
    else:
       IDE_setMode(MODE_noFile)
       IDE_doc=None
       adjustCanvasLength(0)
       for text in (IDE_curPosText,IDE_marksStatusText,IDE_macroNotif,IDE_errNotif):
           text['text']=''
       IDE_updateCurPos()
       IDE_updateMacroNotif()
       IDE_updateErrNotif()

def IDE_switchToMainFile():
    if IDE_doc is None: return
    mainMod=[d for d in IDE_documents if d.FullPath==APP_mainFile]
    if mainMod and mainMod[0]!=IDE_doc:
       mainMod[0].setDocActive()

def IDE_reloadFiles(docs):
    lastDoc=IDE_doc
    paths=[d.FullPath for d in docs]
    names=[d.FileName for d in docs]
    idx=[IDE_documents.index(d) for d in docs]
    numFiles=len(names)
    numOpenFiles=len(IDE_documents)
    for d in docs:
        IDE_doCloseDoc(d)
    IDE_openFiles(paths)
    if len(IDE_documents)==numOpenFiles:
       for i in reversed(list(range(1,numFiles+1))):
           IDE_documents.insert(idx[numFiles-i],IDE_documents.pop(-i))
       IDE_arrangeDocsTabs()
    if lastDoc and lastDoc in IDE_documents:
       lastDoc.setDocActive()
    # rebinds reloaded modules, but excludes the main module
    for mm in (APP_mainFile,RunningAPP_mainFile):
        if mm in paths:
           paths.remove(mm)
    if paths:
       mods=list(sys.modules.values())
       for p in paths:
           doc=IDE_getDocByPath(p)
           if not doc:
              continue
           name=joinPaths(doc.DirName,os.path.splitext(doc.FileName)[0])
           for m in mods:
               if m and hasattr(m,'__file__'):
                  if name==os.path.splitext(m.__file__)[0]:
                     doc.rebind()
                     globalClock.setMode(ClockObject.MNormal)
                     break
    IDE_setMessage('RELOADED : ' + ', '.join(['"%s"'%n for n in names]))

def IDE_getDocByPath(path):
    for d in IDE_documents:
        if d.FullPath==path:
           return d

def IDE_finishIndentCloseUpViewIval():
    i=ivalMgr.getInterval(IDE_ivalsName+'closeup hide')
    if i: i.finish()

def IDE_openLog():
    global IDE_log, IDE_lastDocB4Log, IDE_lastMode
    if IDE_log is None:
       # already created but hidden
       if IDE_hiddenDocs and IDE_hiddenDocs[0].FileName==IDE_LOG_NAME:
          IDE_finishIndentCloseUpViewIval()
          IDE_lastDocB4Log=IDE_doc
          IDE_log=IDE_hiddenDocs.pop()
          IDE_documents.append(IDE_log)
          IDE_documents[-1].setDocActive(arrangeTabs=1)
          IDE_doc.tab.unstash() # restores the file tab
          IDE_setMode(MODE_active)
          __updateCanvasZpos(-1) # scrolls to doc end
          LOG.setUpdateCallback(IDE_updateLog)
       else: # not yet created
          logSize=len(LOG.log)
          # if it's large enough, ask for user permission
          if logSize>IDE_CFG[CFG_minLargeLogSize]:
             IDE_lastMode=IDE_getMode()
             IDE_setMode(MODE_noInput)
             IDE_openYesNoCancelDialog('Log size is %.2f KB.\nIt takes awhile to display the log.\nDo you really need log since the IDE started ?'%(logSize/1024),IDE_createLog,True)
          else:
             IDE_createLog()
    else: # already created and opened
       # if the active doc is the log, switch to the last active one
       if IDE_log==IDE_doc:
          if IDE_lastDocB4Log in IDE_documents:
             IDE_lastDocB4Log.setDocActive()
       else:
          IDE_finishIndentCloseUpViewIval()
          IDE_lastDocB4Log=IDE_doc
          IDE_log.setDocActive()

def IDE_createLog(fullLog=True,result=True):
    global IDE_log, IDE_lastDocB4Log
    if result is None:
       IDE_setMode(IDE_lastMode)
       return
    fullLog=result==True
    IDE_finishIndentCloseUpViewIval()
    IDE_setMode(MODE_pickFiles)
    IDE_documents.append(IDE_document(IDE_LOG_NAME))
    IDE_gauge.setText(IDE_LOG_NAME)
    IDE_gauge.show()
    IDE_documents[-1].loadFile(fullLog=fullLog)
    IDE_gauge.set(1)
    IDE_step()
    IDE_gauge.hide()
    IDE_lastDocB4Log=IDE_doc
    # must be done before setDocActive(), to avoid processImports() there
    IDE_log=IDE_documents[-1]
    IDE_log.canvasXpos=0
    IDE_log.canvasZpos=0
    IDE_documents[-1].setDocActive(arrangeTabs=1)
    IDE_setMode(MODE_active)
    __updateCanvasZpos(-1)
    LOG.setUpdateCallback(IDE_updateLog)

def IDE_updateLog(s):
    if IDE_doc==IDE_log:
       oldDoc=None
    else:
       oldDoc=IDE_doc
       IDE_log.setDocActive(tempSwitch=1)
    # keeps old values
    oldLMC=IDE_doc.lastMaxColumn
    oldLC=(IDE_doc.line,IDE_doc.column)
    oldSelLC=(IDE_doc.blockStartLine,IDE_doc.blockStartCol)
    oldSel=IDE_doc.isSelecting
    oldZ=IDE_canvas.getZ()
    userScrolledUp=abs(oldZ-(IDE_canvasLen-IDE_frameHeight+.015))>1e-3
    IDE_doc.isSelecting=False
    IDE_doc.line=IDE_doc.numLines-1
    # put it at soft-end, so upon gotoBack, it will be put at real-end
    IDE_doc.column=len(IDE_doc.File[IDE_doc.line].rstrip())
    IDE_gotoBack()
    sL=s.splitlines(True)
    for i in range(len(sL)):
        filled=LOG_TW.fill(sL[i]).replace('\n','\n   ')
        sL[i]=filled+('\n' if sL[i] and sL[i][-1]=='\n' else '')
    IDE_paste(''.join(sL))
    adjustCanvasLength(IDE_doc.numLines)
    __exposeCurrentLine()
    # restores old values
    IDE_doc.lastMaxColumn=oldLMC
    IDE_doc.line,IDE_doc.column=oldLC
    IDE_doc.blockStartLine,IDE_doc.blockStartCol=oldSelLC
    IDE_doc.isSelecting=oldSel
#     IDE_setSelection(oldSel)
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeColumn()
    # if user scrolled the canvas so it's not at page end,
    # discard the auto-scroll to end, restore the last Z
    if userScrolledUp:
       __updateCanvasZpos(oldZ)
    if oldDoc:
       oldDoc.setDocActive(tempSwitch=1)

def IDE_clearLog():
    IDE_adjustLineMarks(0,IDE_log.numLines-1,-1)
    IDE_log.File=['']
    IDE_log.numLines=1
    adjustCanvasLength(IDE_log.numLines)
    IDE_setHilighter(IDE_log.hilight)
    IDE_log.quoted=[False]
    IDE_log.line=IDE_log.column=IDE_log.lastMaxColumn=0
    IDE_log.isSelecting=False
    IDE_updateCurPos()
    IDE_updateBlock()

def getParentDirs(f):
    pardirs=[]
    dir=os.path.dirname(f)
    while not os.path.ismount(dir):
        pardirs.append(dir)
        dir=os.path.dirname(dir)
    if dir!=os.sep:
       pardirs.append(dir)
    return pardirs

def args2Str(args):
    newArgs=[a if a.find(' ')==-1 else '"%s"'%a for a in args]
    return ' '.join(newArgs)

def str2Args(s):
    args=[]
    i=0
    for a in s.split('"'):
        args+=[a] if i%2 else a.split()
        i+=1
    return args

def IDE_openSetMainFileInterface(doc=None,askCWD=False):
    if doc is None:
       doc=IDE_doc
    if doc.FullPath:
       global IDE_lastMode
       if askCWD:
          IDE_lastMode=IDE_getMode()
          IDE_setMode(MODE_chooseCWD)
          note="\n\nNOTE: it's already the main module.\nHowever, you can change its properties as needed."*(APP_mainFile==doc.FullPath)

          frame = wx.Frame(None, -1, 'Set File As Main Module')
          frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
          panel = wx.Panel(frame)

          setCWDSizer = wx.BoxSizer(wx.VERTICAL)

          infoText = wx.StaticText(panel, -1, "You're about to set \"%s\" as the main module.%s\n"%(doc.FileName,note))
          setCWDText = wx.StaticText(panel, -1, 'Working directory :')
          CWDchoice = wx.Choice(panel, size=(415,-1))
          CWDchoice.SetItems(getParentDirs(doc.FullPath))
          CWDchoice.SetStringSelection(os.path.dirname(doc.FullPath) if doc.preferedCWD=='.' else doc.preferedCWD)

          setArgsText = wx.StaticText(panel, -1, 'Arguments :')
          ARGtext = wx.TextCtrl(panel, value=args2Str(doc.preferedArgs))

          setCWDBtn = wx.Button(panel, -1, 'Set')
          setCWDBtn.SetFont(wxBigFont)
          setCWDBtn.Bind(wx.EVT_BUTTON,Functor(IDE_setAsMainFile,doc,CWDchoice,ARGtext))

          setCWDSizer.Add(infoText, 0, wx.TOP|wx.BOTTOM|wx.LEFT|wx.ALIGN_LEFT, 5)
          setCWDSizer.Add(setCWDText, 0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT, 5)
          setCWDSizer.Add(CWDchoice, 0, wx.ALL|wx.ALIGN_LEFT|wx.EXPAND, 5)
          setCWDSizer.Add(setArgsText, 0, wx.TOP|wx.LEFT|wx.ALIGN_LEFT, 5)
          setCWDSizer.Add(ARGtext, 0, wx.ALL|wx.ALIGN_LEFT|wx.EXPAND, 5)
          setCWDSizer.Add(setCWDBtn, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5)

          panel.SetSizer(setCWDSizer)
          setCWDSizer.Fit(frame)
          setCWDSizer.SetSizeHints(frame)
          frame.Center()
          frame.Show()
          setCWDBtn.SetFocus()
       else:
          IDE_setAsMainFile(doc)
    else:
       IDE_SOUND_oops.play()
       if doc==IDE_log: return
       msg=createMsg('Please save this new file before proceed',bg=(1,0,0,.85))
       putMsg(msg,'save new file as main module',2)

def IDE_setAsMainFile(doc,CWDchoice=None,ARGtext=None,ce=None):
    global APP_mainFile, APP_CWD, APP_args, RunningAPP_CWD, OldAPP_CWD
    oldMain=[d for d in IDE_documents if d.FullPath==APP_mainFile]
    if CWDchoice:
       doc.preferedCWD=preferedCWD=CWDchoice.GetStringSelection()
       doc.preferedArgs=preferedArgs=str2Args(ARGtext.Value)
       # closes the window
       IDE_closeWxInterface(ce.GetEventObject().GetGrandParent())
    else:
       preferedCWD=doc.DirName if doc.preferedCWD=='.' else doc.preferedCWD
       preferedArgs=doc.preferedArgs
    OldAPP_CWD=APP_CWD
    APP_CWD=preferedCWD
    APP_args=preferedArgs
    APP_mainFile=doc.FullPath
    # removes .PYC before user run this module
    removePYC(os.path.dirname(APP_mainFile))
    if APP_CWD in sys.path:
       sys.path.remove(APP_CWD)
    sys.path.insert(0,APP_CWD)
    if oldMain and oldMain[0]!=IDE_doc:
       oldMain[0].setInactive()
    if IDE_doc==doc:
       doc.setActive()
    else:
       lastDoc=IDE_doc
       doc.setDocActive(tempSwitch=1)
       lastDoc.setDocActive(tempSwitch=1)
    IDE_saveFilesList()
    msg=createMsg('%s\nis the main module now'%doc.FileName,bg=(0,1,0,.85))
    putMsg(msg,'set as main module',2,stat=True)


def IDE_createTabGeoms():
    global IDE_REALtabLcorner,IDE_REALtabMid,IDE_REALtabRcorner,\
           IDE_REALtabLabelL,IDE_REALtabLabelMid,IDE_REALtabLabelR
    tabLcornerTex=IDE_loadTabTexture('Lcorner')
    tabRcornerTex=IDE_loadTabTexture('Rcorner')
    tabMidTex=IDE_loadTabTexture('mid')
    tabLabelLTex=IDE_loadTabTexture('labelL')
    tabLabelRTex=IDE_loadTabTexture('labelR')
    for t in (IDE_REALtabLcorner,IDE_REALtabMid,IDE_REALtabRcorner,IDE_REALtabLabelL,IDE_REALtabLabelMid,IDE_REALtabLabelR):
        t.removeChildren()
    IDE_REALtabLabelL.attachNewNode(DU.createUVRect(align=1))
    IDE_REALtabLabelR.attachNewNode(DU.createUVRect(align=0,flipU=tabLabelRTex is None))
    IDE_REALtabLabelMid.attachNewNode(DU.createUVRect(align=0,Uflood=1))
    IDE_REALtabLcorner.attachNewNode(DU.createUVRect(x=100,align=1))
    IDE_REALtabRcorner.attachNewNode(DU.createUVRect(x=100,align=0,flipU=tabRcornerTex is None))
    if tabMidTex is None:
       IDE_REALtabMid.attachNewNode(DU.createUVRect(align=0,Uflood=1))
       tabMidTex=tabLcornerTex
    else:
       midBorder=IDE_REALtabMid.attachNewNode(DU.createUVRect(align=.5))
       midBorder.setX(midBorder.getTightBounds()[1][0])
       midBorder.flattenLight()

    if tabRcornerTex is None:
       tabRcornerTex=tabLcornerTex
    if tabLabelRTex is None:
       tabLabelRTex=tabLabelLTex
    for t in (tabLcornerTex,tabRcornerTex,tabMidTex,tabLabelLTex,tabLabelRTex):
        t.setMinfilter(Texture.FTLinearMipmapLinear)
        t.setMagfilter(Texture.FTLinearMipmapLinear)
        t.setWrapU(Texture.WMClamp)
        t.setWrapV(Texture.WMClamp)
    IDE_REALtabLcorner.setTexture(tabLcornerTex)
    IDE_REALtabMid.setTexture(tabMidTex)
    IDE_REALtabRcorner.setTexture(tabRcornerTex)
    IDE_REALtabLabelL.setTexture(tabLabelLTex)
    IDE_REALtabLabelMid.setTexture(tabLabelLTex)
    IDE_REALtabLabelR.setTexture(tabLabelRTex)

def IDE_getAvailTabSkins():
    availSkins=[f for f in os.listdir(IDE_tabSkinsPath) if os.path.isdir(joinPaths(IDE_tabSkinsPath,f))]
    availSkins.sort()
    return availSkins

def IDE_cycleTabSkin(adv):
    availSkins=IDE_getAvailTabSkins()
    idx=availSkins.index(IDE_CFG[CFG_fileTabSkin])
    newSkin=(idx+adv)%len(availSkins)
    IDE_CFG[CFG_fileTabSkin]=availSkins[newSkin]
    IDE_createTabGeoms()

def IDE_getAvailSliderSkins():
    availSkins=[f for f in os.listdir(IDE_sliderSkinsPath) if os.path.isdir(joinPaths(IDE_sliderSkinsPath,f))]
    availSkins.sort()
    return availSkins

def IDE_cycleSliderSkin(adv):
    availSkins=IDE_getAvailSliderSkins()
    idx=availSkins.index(IDE_CFG[CFG_sliderSkin])
    newSkin=(idx+adv)%len(availSkins)
    IDE_CFG[CFG_sliderSkin]=availSkins[newSkin]
    IDE_loadSliderTextures(IDE_CFG[CFG_sliderSkin])
    vsliderTopEnd.setTexture(sliderEndTex,1)
    vsliderBottomEnd.setTexture(sliderEndTex,1)
    vsliderBarSkin.setTexture(sliderBarTex,1)
    vsliderBarSkin2.setTexture(sliderBarTex,1)

def IDE_resetModifierButtons(win=None):
    global IDE_isCtrlDown
    if win is not None and not win.getProperties().getForeground():
       return
    IDE_isCtrlDown=False
    IDE_BTnode.setModifierButtons(IDE_MB)

def IDE_chooseColor(mode):
    global IDE_lastMode, IDE_lastChosenColor
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_noInput)
    colorFromText=None
    if IDE_doc.isSelecting:
       startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
       if startLine==endLine and startCol!=endCol:
          text=IDE_doc.File[startLine][startCol:endCol]
          numbers=text.split(',')
          if len(numbers)==3:
             try:
                 colorFromText=[clampScalar(0,255,float(n)) for n in numbers]
                 if max(colorFromText)<=1.: # 0..1, must be scaled to 0..255
                    colorFromText=[c*255 for c in colorFromText]
             except:
                 pass
    colorDlg=wx.ColourDialog(None)
    colorDlg.GetColourData().SetChooseFull(1)
    colorDlg.GetColourData().SetColour(colorFromText if colorFromText else IDE_lastChosenColor)
    colorDlg.Center()
    res=colorDlg.ShowModal()
    col=list(colorDlg.GetColourData().GetColour()[:3])
    colorDlg.Destroy()
    IDE_setMode(IDE_lastMode)
    IDE_resetModifierButtons()
    if res==wx.ID_CANCEL: return
    IDE_lastChosenColor=col
    if mode==0: # 0..1
       col=[c/255. for c in col]
    # mode==1 --> 0..255
    elif mode==2: # both
       col=[c/255. for c in col]+['|']+col
    colStr=[str(c) for c in col]
    s=', '.join(colStr).replace(', |,',' |').replace('0.','.')
    IDE_injectChar(s,completion=False)

def IDE_packHistoryEntriesSince(lastIdx):
    if lastIdx==IDE_doc.historyIdx:
       return
    remaining=IDE_doc.history[lastIdx+1:]
    del IDE_doc.history[lastIdx+1:]
    IDE_doc.history.append(deque(remaining))
    IDE_doc.historyIdx-=len(remaining)-1

def IDE_truncateHistory():
    if IDE_doc.historyIdx<IDE_doc.historyIdxOnSave:
       IDE_doc.changedSinceSaved=True
    Hlen=len(IDE_doc.history)
    if IDE_doc.historyIdx<Hlen-1:
       del IDE_doc.history[IDE_doc.historyIdx+1:]
       IDE_doc.groupHistoryOn=False
       return len(IDE_doc.history)
    return Hlen

def IDE_undo(update=True):
    if mustBeHalted(): return
    if IDE_doc.historyIdx<0:
       if IDE_SOUND_depleted.status()==AudioSound.READY:
          IDE_SOUND_depleted.play()
       IDE_setMessage('UNDO: no more')
       return
    global HISTORY_ON,UNDO,UNDO_REPLACE,UPDATE_DISPLAY,REPLACING
    IDE_CC_cancel()
    HISTORY_ON=False
    UNDO=True
    undoItem=IDE_doc.history[IDE_doc.historyIdx]
    IDE_doc.historyIdx-=1
    # shifts commands end index
    if IDE_doc.recordMacro and len(IDE_doc.macro):
       if IDE_doc.historyIdx in IDE_doc.macro_undoIdx:
          IDE_doc.macro_idx=IDE_doc.macro_undoIdx[IDE_doc.historyIdx]
       else:
          print('historyIdx NOT IN undoIdx', file=IDE_DEV)
          IDE_doc.macro_idx=0
#        for m in IDE_doc.macro[:IDE_doc.macro_idx]:
#            print>>IDE_DEV, 'M:',m
    isRecordingMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False
    lastUPDATE_DISPLAY=UPDATE_DISPLAY

    isReplacementActions=type(undoItem)==deque
    # a single action is stored in a list, tuple is used to pack multiple actions
    if type(undoItem)==list:
       undoItem=(undoItem,)
    elif isReplacementActions:
       UPDATE_DISPLAY=False
       UNDO_REPLACE=True
       IDE_setMessage('UNDOing text replacement action(s).....')
       renderFrame(2)
    for action,props in reversed(undoItem):
#         print>>IDE_DEV, 'UNDO:',action
        IDE_doc.isSelecting=False
        if action==EDIT_type:
           IDE_doc.line,IDE_doc.column,char=props
           IDE_delChar(len(char),completion=False)
        elif action==EDIT_typeOvr:
           IDE_doc.line,IDE_doc.column,ovrChar,char=props
           IDE_injectChar(ovrChar,completion=False,insert=False)
           charsLenDiff=len(char)-len(ovrChar)
           if charsLenDiff:
              IDE_delChar(charsLenDiff,completion=False)
           IDE_doc.column-=len(ovrChar)
        elif action==EDIT_del or action==EDIT_backsp:
           IDE_doc.line,IDE_doc.column,char=props
           if char=='\n':
              IDE_breakLine()
           else:
              if char.find('\n')>-1:
                 IDE_paste(char,smartPaste=False,stickCursor=action==EDIT_del)
              else:
                 lastCol=IDE_doc.column
                 IDE_injectChar(char,completion=False)
                 if action==EDIT_del:
                    IDE_doc.column=lastCol
        elif action==EDIT_delLine:
           IDE_doc.line,origCol,chars=props
           IDE_doc.column=0
           IDE_paste(chars,smartPaste=False,stickCursor=True)
           IDE_doc.column=origCol
        elif action==EDIT_delLineTail:
           IDE_doc.line,IDE_doc.column,chars=props
           IDE_paste(chars,smartPaste=False,stickCursor=True)
        elif action==EDIT_delLineHead:
           IDE_doc.line,col,chars=props
           IDE_doc.column=col-len(chars)
           IDE_paste(chars,smartPaste=False)
        elif action==EDIT_joinLines:
           line,col,IDE_doc.blockStartLine, \
              IDE_doc.blockStartCol,IDE_doc.line,chars=props[:6]
           IDE_doc.column=0
           IDE_delLine()
           IDE_paste(chars,smartPaste=False)
           IDE_doc.line=line
           IDE_doc.column=col
           IDE_doc.blockStartLine,IDE_doc.blockStartCol=props[2:4]
           IDE_doc.isSelecting=True
        elif action==EDIT_delSel:
           line,col,IDE_doc.blockStartLine,IDE_doc.blockStartCol, \
              startLine,startCol,chars=props
           IDE_doc.line=startLine
           IDE_doc.column=startCol
           IDE_paste(chars,smartPaste=False)
           IDE_doc.line=line
           IDE_doc.column=col
           IDE_doc.isSelecting=True
        elif action==EDIT_breakLine:
           IDE_doc.line,IDE_doc.column,endCol,num=props
           IDE_doc.isSelecting=True
           IDE_doc.blockStartLine=IDE_doc.line+num
           IDE_doc.blockStartCol=endCol
           IDE_delChar(completion=False)
           # SLOW SOLUTION
#            for l in range(num):
#                IDE_delChar(completion=False)
#                s=IDE_doc.File[IDE_doc.line][IDE_doc.column:]
#                tailCol=s.find(tail)
#                if tailCol>-1 and tail:
#                   IDE_delChar(tailCol,completion=False)
#                elif s!='\n':
#                   IDE_delWordTail()
        elif action==EDIT_changeCase:
           IDE_doc.line,IDE_doc.column,case,chars=props
           IDE_injectChar(chars,completion=False)
           IDE_delChar(len(chars),completion=False)
           IDE_doc.line,IDE_doc.column=props[:2]
        elif action==EDIT_changeCaseSel:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,chars,case=props
           IDE_doc.isSelecting=True
           IDE_paste(chars,smartPaste=False)
           IDE_doc.isSelecting=True
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol=props[:4]
        elif action==EDIT_comment:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,\
              IDE_doc.isSelecting=props
           IDE_toggleComment()
        elif action==EDIT_copyLine:
           IDE_doc.line,origCol,direction,num=props
           IDE_doc.blockStartCol=IDE_doc.column=0
           IDE_doc.blockStartLine= IDE_doc.line + num
           IDE_doc.isSelecting=True
           IDE_delSelection()
           IDE_doc.column=origCol
           # SLOW SOLUTION
           #  for l in range(num):
               #  IDE_delLine()
        elif action==EDIT_indentSel:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,num=props
           IDE_doc.isSelecting=True
           IDE_doc.column+=num
           IDE_doc.blockStartCol+=num
           if num>0:
              IDE_unindentSelection(num)
           elif num<0:
              IDE_indentSelection(-num)
           IDE_doc.setChangedStatus(1) # update isChanged attr
        elif action==EDIT_moveLines:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,\
              IDE_doc.isSelecting,direction,num=props
           IDE_doc.line+=num*direction
           IDE_doc.blockStartLine+=num*direction
           IDE_moveLines(-num*direction)
           IDE_doc.setChangedStatus(1) # update isChanged attr
        elif action==EDIT_paste:
           IDE_doc.line,IDE_doc.column,smartPaste,crap,chars,num=props
           linebreakEnd=chars[-1]=='\n'
           numLines=len((chars*num).splitlines(1))+linebreakEnd
#            print>>IDE_DEV, 'numLines:',numLines
           if numLines==1: # a single line
              IDE_delChar(len(chars)*num,completion=False)
           else:           # multiple lines
              lastLine=chars.splitlines(1)[-1]
              IDE_doc.blockStartLine=IDE_doc.line+numLines-1
              IDE_doc.blockStartCol=0 if linebreakEnd else len(lastLine)
              if smartPaste:
                 IDE_doc.blockStartCol+=max(0,IDE_doc.File[IDE_doc.blockStartLine-linebreakEnd].find(lastLine))
              IDE_doc.isSelecting=True
              IDE_delSelection()
        if UPDATE_DISPLAY:
           IDE_updateBlock()
    IDE_updateCurPos()
    __exposeCurrentLine()
    UNDO=False # must be cleared before update
    if isReplacementActions:
       UPDATE_DISPLAY=True
       UNDO_REPLACE=False
       IDE_setHilighter(IDE_doc.hilight) # force recollect quotes
       adjustCanvasLength(IDE_doc.numLines,forced=True)
       IDE_updateBlock()
       # update isChanged attr, since it's not updated when undoing replace (to save time)
       IDE_doc.setChangedStatus(1)
       IDE_addMessage(' done')
    else:
       # populatePage()#forced=True
       if update:
          IDE_forceRender(forced=True)
    HISTORY_ON=True
    IDE_doc.groupHistoryOn=False
    IDE_doc.recordMacro=isRecordingMacro
    if IDE_doc.recordMacro:
       IDE_updateMacroNotif(IDE_COMMANDSdescription[IDE_doc.macro[IDE_doc.macro_idx-1][0]] if IDE_doc.macro_idx else '')

def IDE_redo(update=True):
    if mustBeHalted(): return
    if IDE_doc.historyIdx==len(IDE_doc.history)-1:
       if IDE_SOUND_depleted.status()==AudioSound.READY:
          IDE_SOUND_depleted.play()
       IDE_setMessage('REDO: no more')
       return
    global HISTORY_ON,REDO,UPDATE_DISPLAY
    IDE_CC_cancel()
    HISTORY_ON=False
    REDO=True
    IDE_doc.historyIdx+=1
    # shifts commands end index
    if IDE_doc.recordMacro:
       if IDE_doc.historyIdx in IDE_doc.macro_redoIdx:
          IDE_doc.macro_idx=IDE_doc.macro_redoIdx[IDE_doc.historyIdx]
       else:
          print('historyIdx NOT IN redoIdx', file=IDE_DEV)
#        for m in IDE_doc.macro[:IDE_doc.macro_idx]:
#            print>>IDE_DEV, 'M:',m
    isRecordingMacro=IDE_doc.recordMacro
    IDE_doc.recordMacro=False

    redoItem=IDE_doc.history[IDE_doc.historyIdx]
    isReplacementActions=type(redoItem)==deque
    # a single action is stored in a list, tuple is used to pack multiple actions
    if type(redoItem)==list:
       redoItem=(redoItem,)
    elif isReplacementActions:
       UPDATE_DISPLAY=False
       IDE_setMessage('REDOing text replacement action(s).....')
       renderFrame(2)
    for action,props in redoItem:
        #  print>>IDE_DEV, 'REDO:',action
        IDE_doc.isSelecting=False
        if action==EDIT_type:
           IDE_doc.line,IDE_doc.column,char=props
           IDE_injectChar(char,completion=False)
        elif action==EDIT_typeOvr:
           IDE_doc.line,IDE_doc.column,ovrChar,char=props
           IDE_injectChar(char,completion=False,insert=False)
        elif action==EDIT_del or action==EDIT_backsp:
           IDE_doc.line,IDE_doc.column,char=props
           LFpos=char.find('\n')
           if LFpos>-1:
              IDE_doc.blockStartLine=IDE_doc.line+char.count('\n')
              IDE_doc.blockStartCol=len(char)-1-char.rfind('\n')
              IDE_doc.isSelecting=True
              IDE_delSelection()
              # SLOW SOLUTION
              #  while LFpos>-1:
                    #  if LFpos:
                       #  IDE_delChar(LFpos,completion=False)
                    #  IDE_delChar(completion=False) # deletes the LF
                    #  char=char[LFpos+1:]
                    #  LFpos=char.find('\n')
              #  charsLen=len(char)
              #  if charsLen:
                 #  IDE_delChar(charsLen)
           else:
              IDE_delChar(1 if char=='\n' else len(char.rstrip('\n')),completion=False)
        elif action==EDIT_delLine:
           IDE_doc.line,crap,chars=props
           IDE_doc.blockStartCol=IDE_doc.column=0
           IDE_doc.blockStartLine= IDE_doc.line + len(chars.splitlines(1))
           IDE_doc.isSelecting=True
           IDE_delSelection()
           # SLOW SOLUTION
           #  for l in range(len(chars.splitlines(1))):
               #  IDE_delLine()
        elif action==EDIT_delLineTail:
           IDE_doc.line,IDE_doc.column,chars=props
           IDE_delLineTail()
        elif action==EDIT_delLineHead:
           IDE_doc.line,IDE_doc.column,chars=props
           IDE_delLineHead()
        elif action==EDIT_joinLines:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,crap,crap,conn,stripSpaces=props
           IDE_doc.isSelecting=True
           IDE_joinLines(conn,stripSpaces)
        elif action==EDIT_delSel:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,crap,crap,chars=props
           IDE_doc.isSelecting=True
           IDE_delSelection()
        elif action==EDIT_breakLine:
           IDE_doc.line,IDE_doc.column,endCol,num=props
           IDE_paste(('\n'+' '*endCol)*num,smartPaste=False)
           # SLOW SOLUTION
#            l=IDE_doc.File[IDE_doc.line][IDE_doc.column:].rstrip('\n')
#            if len(l) and l.isspace():
#               IDE_delWordTail()
#            for l in range(num):
#                IDE_breakLine()
        elif action==EDIT_changeCase:
           IDE_doc.line,IDE_doc.column,case,chars=props
           for l in range(len(chars)):
               IDE_changeCase(case)
        elif action==EDIT_changeCaseSel:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,chars,case=props
           IDE_doc.isSelecting=True
           IDE_changeCase(case)
        elif action==EDIT_comment:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,\
              IDE_doc.isSelecting=props
           IDE_toggleComment()
        elif action==EDIT_copyLine:
           IDE_doc.line,origCol,direction,num=props
           IDE_doc.column=0
           IDE_paste(IDE_doc.File[IDE_doc.line]*num,smartPaste=False,stickCursor=not direction>0)
           IDE_doc.column=origCol
           # SLOW SOLUTION
           #  for l in range(num):
               #  IDE_duplicateLine(direction)
        elif action==EDIT_indentSel:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,num=props
           IDE_doc.isSelecting=True
           if num>0:
              IDE_indentSelection(num)
           elif num<0:
              IDE_unindentSelection(-num)
           IDE_doc.setChangedStatus(1) # update isChanged attr
        elif action==EDIT_moveLines:
           IDE_doc.line,IDE_doc.column,\
              IDE_doc.blockStartLine,IDE_doc.blockStartCol,\
              IDE_doc.isSelecting,direction,num=props
           IDE_moveLines(num*direction)
           IDE_doc.setChangedStatus(1) # update isChanged attr
           __updateCanvasZpos(IDE_canvas.getZ(),forced=True)
        elif action==EDIT_paste:
           IDE_doc.line,IDE_doc.column,smartPaste,stickCursor,chars,num=props
           for i in range(num):
               IDE_paste(chars,smartPaste=smartPaste,stickCursor=stickCursor)
        if UPDATE_DISPLAY:
           IDE_updateBlock()
    IDE_updateCurPos()
    __exposeCurrentLine()
    REDO=False # must be cleared before update
    if isReplacementActions:
       UPDATE_DISPLAY=True
       IDE_setHilighter(IDE_doc.hilight) # force recollect quotes
       adjustCanvasLength(IDE_doc.numLines,forced=True)
       IDE_updateBlock()
       IDE_addMessage(' done')
    else:
       # populatePage()#forced=True
       if update:
          IDE_forceRender(forced=True)
    HISTORY_ON=True
    IDE_doc.groupHistoryOn=False
    IDE_doc.recordMacro=isRecordingMacro
    if IDE_doc.recordMacro:
       IDE_updateMacroNotif(IDE_COMMANDSdescription[IDE_doc.macro[IDE_doc.macro_idx-1][0]] if IDE_doc.macro_idx else '')

def IDE_recordMacro():
    IDE_doc.recordMacro=not IDE_doc.recordMacro
    if IDE_doc.recordMacro:
       IDE_doc.macro=[]
       IDE_doc.macro_idx=0
       IDE_doc.macro_undoIdx.clear()
       IDE_doc.macro_redoIdx.clear()
       tempParent=statusBar.attachNewNode('')
       recSymCopy=SB_Macro_parent.find('@@recordSymbol').copyTo(SB_Macro_parent)
       recSymCopy.setAlphaScale(.8)
       tempParent.setPos(SB_Macro_parent,recSymCopy.getBounds().getCenter())
       recSymCopy.wrtReparentTo(tempParent)
       recSymCopy.flattenStrong()
       Sequence( recSymCopy.scaleInterval(.3,Vec3(1),Vec3(40),blendType='easeIn'),
                 Func(tempParent.removeNode),
                 name=IDE_ivalsName+'start recording macro'
                 ).start()
       IDE_setMessage('Macro recording started')
    else:
       if IDE_doc.macro_idx:
          IDE_setMessage('Macro recorded successfully')
          IDE_nameNewMacro()
       else:
          IDE_setMessage('Macro is empty')
          IDE_SOUND_depleted.play()
    IDE_updateMacroNotif()

def IDE_playMacro(idx=0):
    if mustBeHalted(): return
    global PLAYING_MACRO
    if len(MACROS):
       PLAYING_MACRO=True
       for m in MACROS[idx][1]:
           com=IDE_COMMANDS[m[0]][0]
           com(*m[1:]) if len(m) else com()
       PLAYING_MACRO=False
       IDE_forceRender()

def IDE_addCommandToMacro(command,recordHistory=True,historyIdx=None):
    if historyIdx is None:
       historyIdx=IDE_doc.historyIdx
    # truncates unused recorded commands
    if historyIdx<len(IDE_doc.history)-1:
       del IDE_doc.macro[IDE_doc.macro_idx:]
    if recordHistory:
       IDE_doc.macro_undoIdx[historyIdx]=len(IDE_doc.macro)
    IDE_doc.macro.append(command)
    IDE_doc.macro_idx+=1
    if IDE_doc.macro_idx:
       IDE_updateMacroNotif(IDE_COMMANDSdescription[IDE_doc.macro[IDE_doc.macro_idx-1][0]])

def IDE_nameNewMacroProcessWxChar(ce):
    KC=ce.GetKeyCode()
    EO=ce.GetEventObject()
    if KC==wx.WXK_ESCAPE:
       # closes the window
       IDE_closeWxInterface(ce.GetEventObject().GetGrandParent())
       IDE_setMessage('Macro NOT saved')
    elif KC in (wx.WXK_NUMPAD_ENTER,wx.WXK_RETURN):
       IDE_saveNewMacro(EO,ce)
    else:
       ce.Skip()

def IDE_nameNewMacro():
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_nameNewMacro)
    frame = wx.Frame(None, -1, 'Name the newly born macro')
    frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
    panel = wx.Panel(frame)

    optSizer = wx.BoxSizer(wx.HORIZONTAL)
    nameText = wx.StaticText(panel, -1, 'Name :')
    nameInput = wx.TextCtrl(panel,-1, size=(240,-1))
    nameInput.Bind(wx.EVT_CHAR,IDE_nameNewMacroProcessWxChar)

    optSizer.Add(nameText, 0, wx.ALL|wx.ALIGN_CENTER, 5)
    optSizer.Add(nameInput, 0, wx.ALL|wx.ALIGN_CENTER, 5)

    panel.SetSizer(optSizer)
    optSizer.Fit(frame)
    optSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    nameInput.SetFocus()

def IDE_saveNewMacro(EO,ce):
    name=EO.GetValue()
    if not name:
       if IDE_SOUND_depleted.status()==AudioSound.READY:
          IDE_SOUND_depleted.play()
       return
    # closes the window
    IDE_closeWxInterface(ce.GetEventObject().GetGrandParent())
    del IDE_doc.macro[IDE_doc.macro_idx:]
    MACROS.insert(0,[name,list(IDE_doc.macro)])
    IDE_saveMacrosToDisk()
#     for m in IDE_doc.macro:
#         print>>IDE_DEV, 'M:',m

def IDE_saveMacrosToDisk():
    dumpToFile(MACROS, IDE_macrosPath)

def IDE_openMacroManager():
    global IDE_lastMode
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_openMacroManager)
    frame = wx.Frame(None, -1, 'Macro Manager')
    panel = wx.Panel(frame)

    mgrSizer = wx.BoxSizer(wx.HORIZONTAL)
    namesSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Macros : '),wx.VERTICAL)
    playMacroSizer = wx.BoxSizer(wx.HORIZONTAL)
    renameMacroSizer = wx.BoxSizer(wx.HORIZONTAL)
    moveUpDnCommandSizer = wx.BoxSizer(wx.HORIZONTAL)
    delNcopyCommandSizer = wx.BoxSizer(wx.HORIZONTAL)
    insertCommandSizer = wx.BoxSizer(wx.HORIZONTAL)
    commandsSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Commands sequence : '),wx.VERTICAL)
    comOptSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Command options : '),wx.VERTICAL)

    macrosNames=[m[0] for m in MACROS]
    macrosList=wx.ListBox(panel, -1, wx.DefaultPosition, (140, 180), macrosNames, wx.LB_SINGLE)
    commandsList=wx.ListBox(panel, -1, wx.DefaultPosition, (170, 180), [''], wx.LB_SINGLE)
    commandsList.Bind(wx.EVT_LISTBOX,Functor(IDE_macroCommandSelected,\
        macrosList,commandsList,mgrSizer,comOptSizer,frame,panel))

    newNameText=wx.TextCtrl(panel)
    renameButton=wx.Button(panel,-1,'&Rename',style=wx.BU_EXACTFIT)
    renameButton.Bind(wx.EVT_BUTTON,Functor(IDE_renameMacro,macrosList,newNameText))
    setDefaultButton=wx.Button(panel,-1,'Set default')
    setDefaultButton.Bind(wx.EVT_BUTTON,Functor(IDE_setMacroAsDefault,macrosList))
    setDefaultButton.Disable()
    playCountText=wx.TextCtrl(panel,-1,'1',size=(40,-1),style=wx.TE_CENTER)
    playButton=wx.Button(panel,-1,'Play',style=wx.BU_EXACTFIT)
    playButton.Bind(wx.EVT_BUTTON,Functor(IDE_prepareToPlayMacro,macrosList,playCountText))
    delButton=wx.Button(panel,wx.ID_DELETE)
    copyButton=wx.Button(panel,-1,'Duplicate')
    copyButton.Bind(wx.EVT_BUTTON,Functor(IDE_copyMacro,macrosList,newNameText))
    delButton.Bind(wx.EVT_BUTTON,Functor(IDE_delMacro,[macrosList,commandsList,namesSizer,commandsSizer,comOptSizer]))

    playMacroSizer.Add(playCountText, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 2)
    playMacroSizer.Add(wx.StaticText(panel,-1,'x'), 0, wx.ALIGN_CENTER_VERTICAL)
    playMacroSizer.Add(playButton, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 2)

    renameMacroSizer.Add(newNameText, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
    renameMacroSizer.Add(renameButton, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)

    namesSizer.Add(macrosList, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER, 5)
    namesSizer.Add(renameMacroSizer, 0, wx.TOP|wx.BOTTOM|wx.ALIGN_CENTER, 5)
    namesSizer.Add(wx.StaticLine(panel,-1), 0, wx.TOP|wx.EXPAND)
    namesSizer.Add(setDefaultButton, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    namesSizer.Add(playMacroSizer, 0, wx.ALIGN_CENTER, 5)
    namesSizer.Add(delButton, 0, wx.ALIGN_CENTER, 5)
    namesSizer.Add(copyButton, 0, wx.ALIGN_CENTER, 5)

    delComButton=wx.Button(panel,wx.ID_DELETE)
    copyComButton=wx.Button(panel,-1,'Duplicate')
    moveUpPic = wx.Bitmap(joinPaths(IDE_imagesPath,'listUpArrow.png'))
    moveUpButton = wx.BitmapButton(panel, -1, moveUpPic,size=(50,25))
    moveDnPic = wx.Bitmap(joinPaths(IDE_imagesPath,'listDownArrow.png'))
    moveDnButton = wx.BitmapButton(panel, -1, moveDnPic,size=(50,25))
    comsChoices=list(IDE_COMMANDSdescription.values())
    comsChoices.sort()
    commandsChoice=wx.Choice(panel,-1,choices=comsChoices)
    commandsChoice.SetSelection(0)
    insAboveComButton=wx.Button(panel,-1,'Above')
    insBelowComButton=wx.Button(panel,-1,'Below')
    moveUpButton.Bind(wx.EVT_BUTTON,Functor(IDE_moveMacroCommand,-1,macrosList,commandsList))
    moveDnButton.Bind(wx.EVT_BUTTON,Functor(IDE_moveMacroCommand,1,macrosList,commandsList))
    delComButton.Bind(wx.EVT_BUTTON,Functor(IDE_delMacroCommand,[macrosList,commandsList,delComButton,copyComButton,comOptSizer]))
    copyComButton.Bind(wx.EVT_BUTTON,Functor(IDE_copyMacroCommand,macrosList,commandsList))
    insAboveComButton.Bind(wx.EVT_BUTTON,Functor(IDE_insertMacroCommand,0,[commandsChoice,macrosList,commandsList,delComButton,copyComButton,comOptSizer]))
    insBelowComButton.Bind(wx.EVT_BUTTON,Functor(IDE_insertMacroCommand,1,[commandsChoice,macrosList,commandsList,delComButton,copyComButton,comOptSizer]))

    delNcopyCommandSizer.Add(delComButton)
    delNcopyCommandSizer.Add(copyComButton)

    moveUpDnCommandSizer.Add(moveUpButton)
    moveUpDnCommandSizer.Add(moveDnButton)

    insertCommandSizer.Add(insAboveComButton)
    insertCommandSizer.Add(insBelowComButton)

    commandsSizer.Add(commandsList, 0, wx.ALIGN_CENTER, 5)
    commandsSizer.Add(delNcopyCommandSizer, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    commandsSizer.Add(moveUpDnCommandSizer, 0, wx.ALIGN_CENTER, 5)
    commandsSizer.Add(wx.StaticLine(panel,-1), 0, wx.TOP|wx.EXPAND, 5)
    commandsSizer.Add(wx.StaticText(panel,-1,'Insert command :'), 0, wx.TOP|wx.LEFT, 5)
    commandsSizer.Add(commandsChoice, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER, 5)
    commandsSizer.Add(insertCommandSizer, 0, wx.ALIGN_CENTER, 5)

    comOptSizer.Add(wx.StaticText(panel,-1,'< no available options >'), 0, wx.TOP|wx.ALIGN_CENTER, 5)

    mgrSizer.Add(namesSizer, 0, wx.ALL|wx.EXPAND, 5)
    mgrSizer.Add(commandsSizer, 0, wx.TOP|wx.BOTTOM|wx.EXPAND, 5)
    mgrSizer.Add(comOptSizer, 0, wx.ALL|wx.EXPAND, 5)

    frame.Bind(wx.EVT_CLOSE,Functor(IDE_closeMacroManager,commandsList,comOptSizer))
    macrosList.Bind(wx.EVT_LISTBOX,Functor(IDE_macroSelected,macrosList,commandsList,setDefaultButton,newNameText,comOptSizer))
    if macrosNames:
       macrosList.SetSelection(0)
       macrosList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
       macrosList.SetFocus()
    else:
       for w in getWxSizerWidgets([namesSizer,commandsSizer]):
           w.Disable()
    panel.SetSizer(mgrSizer)
    mgrSizer.Fit(frame)
    mgrSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    if WIN:
       size=frame.GetSize()
       frame.SetSize((size[0]+1,size[1]))
    # handles navigational wx events
    if WIN:
       for c in getWxSizerWidgets(mgrSizer):
           c.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)

def IDE_moveMacroCommand(direction,macrosList,commandsList,ce):
    midx=macrosList.GetSelection()
    numComs=len(MACROS[midx][1])
    if numComs<2: return
    cidx=commandsList.GetSelection()
    if 0<=cidx+direction<numComs:
       com=MACROS[midx][1].pop(cidx)
       MACROS[midx][1].insert(cidx+direction,com)
       poppedStr=commandsList.GetStringSelection()
       commandsList.SetString(cidx,commandsList.GetString(cidx+direction))
       commandsList.SetString(cidx+direction,poppedStr)
       commandsList.SetSelection(cidx+direction)

def IDE_insertMacroCommand(direction,args,ce):
    commandsChoice,macrosList,commandsList,delComButton,copyComButton,comOptSizer=args
    midx=macrosList.GetSelection()
    cidx=max(0,commandsList.GetSelection()+direction)
    comDesc=commandsChoice.GetStringSelection()
    comType=[c for c in IDE_COMMANDSdescription if comDesc==IDE_COMMANDSdescription[c]][0]
    defaultArgs=IDE_COMMANDSdefaultArgs[comType]
    MACROS[midx][1].insert(cidx,[comType]+defaultArgs)
    newCommandText=comType+' '+' '.join([i for i in defaultArgs if type(i) in STRINGTYPE])
    commandsList.Insert(newCommandText,cidx)
    commandsList.SetSelection(cidx)
    commandsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    delComButton.Enable()
    copyComButton.Enable()

def IDE_prepareToPlayMacro(macrosList,playCountText,ce):
    val=playCountText.GetValue()
    try:
        num=int(val)
        if num<1:
           IDE_spawnWxModal(IDE_spawnWxInfoDialog, ('Please enter a positive non-zero number !',))
           playCountText.SetFocus()
           return
    except:
       IDE_spawnWxModal(IDE_spawnWxInfoDialog, ('Please enter a number !',))
       playCountText.SetFocus()
       return
    idx=macrosList.GetSelection()
    for i in range(num):
        IDE_playMacro(idx)

def IDE_copyMacroCommand(macrosList,commandsList,ce):
    midx=macrosList.GetSelection()
    cidx=commandsList.GetSelection()
    MACROS[midx][1].insert(cidx+1,deepcopy(MACROS[midx][1][cidx]))
    cidx+=1
    commandsList.Insert(commandsList.GetStringSelection(),cidx)
    commandsList.SetSelection(cidx)
    commandsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))

def IDE_copyMacro(macrosList,newNameText,ce):
    idx=macrosList.GetSelection()
    MACROS.insert(idx+1,deepcopy(MACROS[idx]))
    idx+=1
    macrosList.Insert(MACROS[idx][0],idx)
    macrosList.SetSelection(idx)
    macrosList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    newNameText.SetFocus()
    newNameText.SetInsertionPointEnd()

def IDE_renameMacro(macrosList,newNameText,ce):
    idx=macrosList.GetSelection()
    newName=newNameText.GetValue()
    if newName.strip()=='':
       IDE_spawnWxInfoDialog('You need to fill its new name')
       newNameText.SetValue(MACROS[idx][0])
       newNameText.SetFocus()
    else:
       MACROS[idx][0]=newName
       macrosList.SetString(idx,newName)

def IDE_macroCommandSelected(*args):
    macrosList,commandsList,mgrSizer,comOptSizer,frame,panel=args[:-1]
    idx=commandsList.GetSelection()
    if idx<0: return
    com=commandsList.GetStringSelection().split()[0]
    func=IDE_COMMANDS[com][0]
    comOptSizer.DeleteWindows()
    comOptSizer.Add(wx.StaticText(panel,-1,'command : '+IDE_COMMANDSdescription[com]), 0, wx.TOP|wx.LEFT|wx.RIGHT, 5)
    comOptSizer.Add(wx.StaticLine(panel,-1), 0, wx.EXPAND|wx.TOP, 5)
    if len(IDE_COMMANDS[com])>1:
       IDE_createMacroCommandOptionsWidget(args[:-1],IDE_COMMANDS[com][1])
    else:
       comOptSizer.Add(wx.StaticText(panel,-1,'< no available options >'), 0, wx.TOP|wx.ALIGN_CENTER, 5)
       IDE_refitMacroManagerWindow(frame,comOptSizer,mgrSizer)

def IDE_createMacroCommandOptionsWidget(args,widgetsNidx):
    macrosList,commandsList,mgrSizer,comOptSizer,frame,panel=args
    panel.Freeze() # accumulates widgets update for later
    midx=macrosList.GetSelection()
    cidx=commandsList.GetSelection()
    macro=MACROS[midx][1]
    command=macro[cidx][1:]
    widgetsList={}
#     print command
    for dataidx,widgets in list(widgetsNidx.items()):
        widgetClass=widgets[0]
        value=command[dataidx]
        if value is None: continue
        if widgetClass==wx.TextCtrl:
           textSizer = wx.BoxSizer(wx.HORIZONTAL)
           textCtrl=widgetClass(panel,-1,size=(widgets[3],-1),style=wx.TR_SINGLE if widgets[2] else wx.MULTIPLE)
           textCtrl.SetValue(str(value))
           textSizer.Add(wx.StaticText(panel, -1, widgets[1]), 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
           textSizer.Add(textCtrl, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL, 5)
           comOptSizer.Add(textSizer, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 5)
           widgetsList[dataidx]=textCtrl
        elif widgetClass==wx.RadioBox:
           idxBase=widgets[3]
           mult=widgets[4] if len(widgets)>4 else 1
           radioBox=widgetClass(panel,-1,widgets[1],choices=widgets[2])
           radioBox.SetSelection(int((value-idxBase)*mult))
           comOptSizer.Add(radioBox, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 5)
           widgetsList[dataidx]=radioBox
        elif widgetClass==wx.CheckBox:
           checkBox=widgetClass(panel,-1,widgets[1])
           checkBox.SetValue(value)
           comOptSizer.Add(checkBox, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ALIGN_CENTER, 5)
           widgetsList[dataidx]=checkBox
    if widgetsList:
       comOptSizer.widgetsList=widgetsList
       comOptSizer.widgetsNidx=widgetsNidx
       saveButton=wx.Button(panel,-1,'&Save options changes')
       saveButton.Bind(wx.EVT_BUTTON,Functor(IDE_saveMacroCommandOptionsChanges,macrosList,commandsList,comOptSizer,panel))
       comOptSizer.Add(wx.StaticLine(panel,-1), 0, wx.EXPAND|wx.TOP, 5)
       comOptSizer.Add(saveButton, 0, wx.TOP|wx.ALIGN_CENTER, 5)
    else:
       comOptSizer.Add(wx.StaticText(panel,-1,'< no available options >'), 0, wx.TOP|wx.ALIGN_CENTER, 5)
    # handles navigational wx events
    if WIN:
       for c in getWxSizerWidgets(comOptSizer):
           c.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)
    IDE_refitMacroManagerWindow(frame,comOptSizer,mgrSizer)
    panel.Thaw() # let it be updated altogether

def IDE_saveMacroCommandOptionsChanges(macrosList,commandsList,comOptSizer,panel,ce):
    widgetVal={ wx.CheckBox:'Value',
                wx.TextCtrl:'Value',
                wx.RadioBox:'Selection'}
    midx=macrosList.GetSelection()
    cidx=commandsList.GetSelection()
    command=MACROS[midx][1][cidx]
    refreshCommandOptions=False
    for idx,widget in list(comOptSizer.widgetsList.items()):
        idx+=1
        wt=type(widget)
        valType=type(command[idx])
#         print valType,
        value=getattr(widget,'Get'+widgetVal[wt])()
#         print value,
        if command[0]==COM_type and value.find('\n')>-1:
           defaultArgs=IDE_COMMANDSdefaultArgs[COM_paste]
           # use universal newline
           value=value.replace('\r\n','\n').replace('\r','\n')
           defaultArgs[0]=value
           command=MACROS[midx][1][cidx]=[COM_paste]+defaultArgs
           refreshCommandOptions=True
        try:
           newVal=valType(value)
           updatedWidgetVal=newVal
           if wt==wx.RadioBox:
              mult=comOptSizer.widgetsNidx[idx-1][4] if len(comOptSizer.widgetsNidx[idx-1])>4 else 1
              newVal=valType(newVal/mult) # restores index multiplier
              newVal+=comOptSizer.widgetsNidx[idx-1][3] # restores index base
           elif wt==wx.TextCtrl and valType==int and newVal<1:
              IDE_spawnWxModal(IDE_spawnWxInfoDialog, ('Please enter a positive non-zero number !',))
              widget.SetFocus()
              return
           command[idx]=newVal
           if refreshCommandOptions:
              macrosList.SetSelection(midx)
              macrosList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
              commandsList.SetSelection(cidx)
              commandsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
           else:
              getattr(widget,'Set'+widgetVal[wt])(str(updatedWidgetVal) if wt==wx.TextCtrl else updatedWidgetVal)
              if wt==wx.TextCtrl:
                 newCommandText=command[0]+' '+' '.join([i for i in command[1:] if type(i) in STRINGTYPE])
                 oldItem=commandsList.GetStringSelection()
                 if oldItem!=newCommandText:
                    commandsList.SetString(commandsList.GetSelection(),newCommandText)
#            print newVal
        except:
           error='Cannot convert %s to %s'%(value.__class__.__name__,valType.__name__)
           IDE_spawnWxErrorDialog(error)
           widget.SetFocus()
           break

def IDE_refitMacroManagerWindow(frame,comOptSizer,mgrSizer):
    # re-organizes the newly generated widgets
    comOptSizer.Layout()
    if WIN:
       wxApp.ProcessIdle()
    mgrSizer.Fit(frame)
    mgrSizer.SetSizeHints(frame)
    mgrSizer.SetSizeHints(frame)
    # this makes me dizzy
#     frame.Center()

def IDE_macroSelected(macrosList,commandsList,setDefaultButton,newNameText,comOptSizer,ce):
    idx=macrosList.GetSelection()
    if idx<0: return
    newNameText.SetValue(MACROS[idx][0])
    commands=[m[0]+' '+' '.join([i for i in m[1:] if type(i) in STRINGTYPE]) for m in MACROS[idx][1]]
    commandsList.SetItems(commands)
    commandsList.SetSelection(0)
    commandsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    setDefaultButton.Disable() if idx==0 else setDefaultButton.Enable()

def IDE_setMacroAsDefault(macrosList,ce):
    button=ce.GetEventObject()
    idx=macrosList.GetSelection()
    default=MACROS.pop(idx)
    MACROS.insert(0,default)
    macrosList.SetItems([m[0] for m in MACROS])
    macrosList.SetSelection(0)
    button.Disable()

def IDE_delMacro(args,ce):
    IDE_spawnWxModal( IDE_spawnWxYesNoDialog,(
        'Are you sure to remove this macro ?', IDE_doDelMacro,args)
        )

def IDE_doDelMacro(args):
    if not args or len(MACROS)==0: return
    macrosList,commandsList,namesSizer,commandsSizer,comOptSizer=args
    idx=macrosList.GetSelection()
    MACROS.pop(idx)
    if MACROS:
       macrosList.SetItems([m[0] for m in MACROS])
       macrosList.SetSelection(min(len(MACROS)-1,idx))
       macrosList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
       macrosList.SetFocus()
    else:
       macrosList.Clear()
       commandsList.Clear()
       comOptSizer.DeleteWindows()
       for w in getWxSizerWidgets([namesSizer,commandsSizer]):
           w.Disable()

def IDE_delMacroCommand(args,ce):
    IDE_spawnWxModal( IDE_spawnWxYesNoDialog,(
        'Are you sure to remove this command ?', IDE_doDelMacroCommand,args)
        )

def IDE_doDelMacroCommand(args):
    if not args: return
    macrosList,commandsList,delComButton,copyComButton,comOptSizer=args
    midx=macrosList.GetSelection()
    cidx=commandsList.GetSelection()
    MACROS[midx][1].pop(cidx)
    macrosList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    if len(MACROS[midx][1]):
       commandsList.SetSelection(min(len(MACROS[midx][1])-1,cidx))
       commandsList.ProcessEvent(wx.CommandEvent(wx.wxEVT_COMMAND_LISTBOX_SELECTED))
    else:
       delComButton.Disable()
       copyComButton.Disable()
       comOptSizer.DeleteWindows()

def IDE_closeMacroManager(commandsList,comOptSizer,ce):
    IDE_saveMacrosToDisk()
    comOptSizer.widgetsList=None
    comOptSizer.widgetsNidx=None
    # if it's left bound, it would crash on Linux
    commandsList.Unbind(wx.EVT_LISTBOX)
    IDE_closeWxInterface(ce)

################################################################################
def IDE_findProcessWxChar(nextButton,e):
    KC=e.GetKeyCode()
    EO=e.GetEventObject()
    if KC==wx.WXK_ESCAPE:
       # closes the window
       IDE_closeWxInterface(e.GetEventObject().GetGrandParent())
    elif KC in (wx.WXK_NUMPAD_ENTER,wx.WXK_RETURN):
       if type(EO)==wx.ComboBox and EO.GetName()=='find':
          e=wx.CommandEvent(wx.wxEVT_COMMAND_BUTTON_CLICKED)
          e.EventObject=nextButton
          nextButton.ProcessEvent(e)
    else:
       e.Skip()

def IDE_toggleBackslash(replaceInput,e):
    e.Skip()
    if e.GetEventObject().GetValue():
       replaceInput.SetFont(wx.Font(*IDE_REfont))
    else:
       replaceInput.SetFont(replaceInput.__origFont)

def IDE_toggleRE(findInput,wholeWordCB,wildcardsCB,e):
    e.Skip()
    if e.GetEventObject().GetValue(): # it's RE
       wholeWordCB.__lastVal=wholeWordCB.GetValue()
       wholeWordCB.SetValue(0)
       wholeWordCB.Disable()
       wildcardsCB.__lastVal=wildcardsCB.GetValue()
       wildcardsCB.SetValue(0)
       wildcardsCB.Disable()
       findInput.SetFont(wx.Font(*IDE_REfont))
    else:
       wholeWordCB.SetValue(wholeWordCB.__lastVal)
       wholeWordCB.Enable()
       wildcardsCB.SetValue(wildcardsCB.__lastVal)
       wildcardsCB.Enable()
       findInput.SetFont(findInput.__origFont)

def IDE_pickReplaceAllDir(*args):
    sizer,textbox,recurseCB,extCB,filesList=args[:-1]
    defaultPath=textbox.GetValue()
    if not os.path.exists(defaultPath):
       defaultPath=''
       textbox.SetValue('')
    Ddlg = wx.DirDialog(None, defaultPath=defaultPath, style=wx.OPEN)
    res=Ddlg.ShowModal()
    Ddlg.Destroy()
    if res==wx.ID_OK:
       path = Ddlg.GetPath()
       textbox.SetValue(path)
       IDE_updateReplaceInDirFilesList(*args)

def IDE_updateReplaceInDirFilesList(sizer,rootCB,recurseCB,extCB,filesList,e=None):
    if e: e.Skip()
    path=rootCB.GetValue()
    if not os.path.exists(path):
       filesList.DeleteAllItems()
       return
    exts=[e.lower() for e in extCB.GetValue().strip().replace(';',' ').replace(',',' ').split()]
    recurse=recurseCB.GetValue()
    if recurse:
       fullPathFiles=[]
       for root, dirs, files in os.walk(path):
           for f in files:
               if os.path.splitext(f)[1].lower()[1:] in exts:
                  fullPathFiles.append(joinPaths(root,f))
    else:
       fullPathFiles=[joinPaths(path,n) for n in os.listdir(path) if os.path.splitext(n)[1].lower()[1:] in exts]
       fullPathFiles=[f for f in fullPathFiles if os.path.isfile(f)]
    filesNdirs=(tuple(reversed(os.path.split(p))) for p in fullPathFiles)
    files=[[fn,d.replace(path,'')] for fn,d in filesNdirs]
    openedFiles=[f.FullPath for f in IDE_documents]
    openedFilesFont=wx.Font(8, filesList.__fontFamily, wx.NORMAL, wx.BOLD)
    #~ print '\n'.join(fullPathFiles)
    filesList.DeleteAllItems()
    filesList.initSorter(files,init=not hasattr(filesList,'itemDataMap'))
    #~ listTextColor=(0,0,0)
    for i in range(len(fullPathFiles)):
        #~ filesList.SetItemTextColour(i,listTextColor)
        filesList.Select(i,1)
        if fullPathFiles[i] in openedFiles:
           filesList.SetItemFont(i,openedFilesFont)
    filesList.__fullPathFiles=fullPathFiles
    if filesList._col>-1:
       filesList.SortListItems(filesList._col,filesList._colSortFlag[filesList._col])
       resorted=filesList.OnSortOrderChanged()
       if resorted:
          for i in range(len(fullPathFiles)):
              filesList.Select(i,1)
    sizer.GetStaticBox().SetLabel(' Replace All In Files %s'%(('(%s listed) '%len(fullPathFiles))*bool(fullPathFiles)))

def IDE_findOrReplace(replace=False):
    global IDE_lastMode,IDE_dialog
    if IDE_doc and IDE_doc.recordMacro:
       IDE_SOUND_blockedKeyb.play()
       IDE_setMessage('You cannot find or replace when recording macro.')
       return
    if replace and IDE_doc.readonly:
       warnReadonlyDoc()
       return
    IDE_dialog=None
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_noInput)
    frame = wx.Frame(None, -1, 'Replace' if replace else 'Find')
    frame.Bind(wx.EVT_CLOSE,IDE_closeWxInterface)
    panel = wx.Panel(frame)

    vertSizer = wx.BoxSizer(wx.VERTICAL)
    gridSizer = wx.FlexGridSizer(2,2,0,0)
    prevNextSizer = wx.BoxSizer(wx.HORIZONTAL)

    findText = wx.StaticText(panel, -1, '&Replace :' if replace else '&Find :')
    findInput = wx.ComboBox(panel,-1,size=(350,-1),choices=IDE_FIND_list,name='find'*(not replace))
    findInput.__origFont=findInput.GetFont()
    validInput=lambda: findInput.GetValue()
    if IDE_FIND_re:
       findInput.SetFont(wx.Font(*IDE_REfont))
    startLine,startCol,endLine,endCol = IDE_getOrderedBlock()
    if IDE_doc.isSelecting and startLine==endLine and startCol!=endCol:
       selText=IDE_doc.File[startLine][startCol:endCol]
       findInput.SetValue(selText)
    elif len(IDE_doc.File[IDE_doc.line].rstrip('\n')) and not IDE_doc.File[IDE_doc.line].isspace():
       origCol=IDE_doc.column
       s=IDE_doc.File[IDE_doc.line]
       if IDE_doc.column>0:
          sameType=IDE_areSameType(s[IDE_doc.column-1:IDE_doc.column+1])
          if IDE_doc.column>0 and (sameType or (not sameType and s[IDE_doc.column-1] in myLettersDigits)):
             IDE_gotoPrevWord()
       startCol=IDE_doc.column
       IDE_gotoNextWord()
       selText=IDE_doc.File[IDE_doc.line][startCol:IDE_doc.column]
       IDE_doc.column=origCol
       IDE_updateCurPos()
       if not selText.isspace():
          findInput.SetValue(selText)
    if not findInput.GetValue():
       findInput.SetSelection(0)

    reCB = wx.CheckBox(panel,-1,"it's Regular E&xpressions")
    reCB.SetValue(IDE_FIND_re)
    if replace:
       replacePartialOrAllSizer = wx.BoxSizer()
       partialSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Replace Some '),wx.VERTICAL)
       replaceText = wx.StaticText(panel, -1, 'Wit&h :')
       replaceInput = wx.ComboBox(panel,-1,size=(350,-1),choices=IDE_REPLACE_list,name='replace')
       replaceInput.__origFont=replaceInput.GetFont()
       if IDE_REPLACE_slash:
          replaceInput.SetFont(wx.Font(*IDE_REfont))
       replaceInput.SetSelection(0)
       slashCB = wx.CheckBox(panel,-1,'convert \\escape \\&sequences')
       slashCB.SetToolTipString('Use backslashes to build special characters, instead of left literally')
       slashCB.SetValue(IDE_REPLACE_slash)
       slashCB.Bind(wx.EVT_CHECKBOX,Functor(IDE_toggleBackslash,replaceInput))

    caseCB = wx.CheckBox(panel,-1,'&CaSe SeNsiTiVe')
    caseCB.SetValue(IDE_FIND_caseSensitive)
    wholeWordCB = wx.CheckBox(panel,-1,'&whole word')
    wholeWordCB.__lastVal=IDE_FIND_wholeWord
    wildcardsCB = wx.CheckBox(panel,-1,'use * and ? as wildc&ards')
    wildcardsCB.__lastVal=IDE_FIND_wildcards
    if IDE_FIND_re:
       wholeWordCB.SetValue(0)
       wholeWordCB.Disable()
       wildcardsCB.SetValue(0)
       wildcardsCB.Disable()
    else:
       wholeWordCB.SetValue(IDE_FIND_wholeWord)
       wildcardsCB.SetValue(IDE_FIND_wildcards)
    reCB.Bind(wx.EVT_CHECKBOX,Functor(IDE_toggleRE,findInput,wholeWordCB,wildcardsCB))

    if replace:
       promptCB = wx.CheckBox(panel,-1,'prompt &each replace')
       promptCB.SetValue(IDE_REPLACE_prompt)
    args=[ replaceInput if replace else 0,
           promptCB if replace else 0,
           slashCB if replace else 0,
           findInput, reCB, caseCB, wholeWordCB, wildcardsCB,
           frame ]
    prevButton = wx.Button(panel, -1, '&Previous')
    prevButton.Bind(wx.EVT_BUTTON,Functor(IDE_doFind,*([0]+args)))
    nextButton = wx.Button(panel, -1, '&Next')
    nextButton.Bind(wx.EVT_BUTTON,Functor(IDE_doFind,*([1]+args)))
    if replace:
       replaceAllSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Replace All '),wx.VERTICAL)
       replaceAllInFilesSizer = wx.StaticBoxSizer(wx.StaticBox(panel,-1,' Replace All In Files '),wx.VERTICAL)
       replaceAllButtons1Sizer = wx.BoxSizer(wx.HORIZONTAL)
       replaceAllGridSizer = wx.FlexGridSizer(2,4,0,0)
       replaceAllSizer2 = wx.BoxSizer(wx.HORIZONTAL)
       replaceAllInFileButton = wx.Button(panel, -1, 'In current &file')
       replaceAllInFileButton.__currFile=IDE_doc
       replaceAllArgs=list(args)
       replaceAllArgs[1]=False # no confirmation please
       replaceAllArgs.insert(0,-1) # -1 means replace all
       replaceAllInFileButton.Bind(wx.EVT_BUTTON,Functor(IDE_replaceAllInCurrFile,validInput,replaceAllArgs))
       replaceAllInOpenedFileButton = wx.Button(panel, -1, 'In &open files')
       replaceAllInOpenedFileButton.Bind(wx.EVT_BUTTON,Functor(IDE_replaceInAllOpenedFiles,*replaceAllArgs))
       replaceAllInDirText = wx.StaticText(panel, -1, '&Dir :')
       replaceAllInDirRootCB = wx.ComboBox(panel,choices=IDE_REPLACE_dirList,size=(350,-1))
       browsePic = wx.Bitmap(joinPaths(IDE_imagesPath,'IDE_dir.png'))
       replaceAllInDirBrowseButton = wx.BitmapButton(panel, -1, browsePic,size=(28,28))
       currFilePic = wx.Bitmap(joinPaths(IDE_imagesPath,'IDE_text.png'))
       replaceAllInDirCurrFileButton = wx.BitmapButton(panel, -1, currFilePic,size=(28,28))
       replaceAllInDirCurrFileButton.SetToolTipString("Use current file's location")
       recurseCB = wx.CheckBox(panel,-1,'rec&ursive')
       recurseCB.SetValue(IDE_REPLACE_recurse)
       replaceAllInDirExtText = wx.StaticText(panel, -1, 'Filters :')
       replaceAllInDirExtCB = wx.ComboBox(panel,choices=IDE_REPLACE_dirFilter,size=(200,-1))
       replaceAllInDirExtCB.SetToolTipString('Comma, space, or semi-colon separated extensions filter')
       replaceAllInDirExtCB.SetSelection(0)
       refreshPic = wx.Bitmap(joinPaths(IDE_imagesPath,'IDE_refresh.png'))
       refreshButton = wx.BitmapButton(panel, -1, refreshPic,size=(28,28))
       refreshButton.SetToolTipString('Refresh files list')
       replaceAllInDirFilesList = SortableListCtrl(panel,-1,size=(440,180), images=LCimageList,
         style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
       replaceAllInDirFilesList.InsertColumn(0, 'Filename',wx.LIST_FORMAT_LEFT,200)
       replaceAllInDirFilesList.InsertColumn(1, 'Subdirectory',wx.LIST_FORMAT_LEFT,400)
       replaceAllInDirFilesList.SetToolTipString('The bold files are open ones')
       replaceAllInDirFilesList.__fontFamily=replaceAllInDirFilesList.GetFont().GetFamily()
       replaceAllInDirButton = wx.Button(panel, -1, "Go replace in selected files !")
       replaceAllInDirButton.Bind(wx.EVT_BUTTON, Functor(IDE_confirmReplaceInFilesInDir,
          validInput,replaceAllInDirRootCB,replaceAllInDirExtCB,replaceAllInDirFilesList,
          recurseCB,replaceAllArgs))
       updateArgs=[replaceAllInFilesSizer,replaceAllInDirRootCB,recurseCB,replaceAllInDirExtCB,replaceAllInDirFilesList]
       replaceAllInDirBrowseButton.Bind(wx.EVT_BUTTON, Functor(IDE_pickReplaceAllDir,*updateArgs))
       replaceAllInDirExtCB.Bind(wx.EVT_COMBOBOX, Functor(IDE_updateReplaceInDirFilesList,*updateArgs))
       refreshButton.Bind(wx.EVT_BUTTON, Functor(IDE_updateReplaceInDirFilesList,*updateArgs))
       replaceAllInDirRootCB.Bind(wx.EVT_TEXT, Functor(IDE_updateReplaceInDirFilesList,*updateArgs))
       if IDE_REPLACE_dirList:
          replaceAllInDirRootCB.SetSelection(0)
          IDE_updateReplaceInDirFilesList(*updateArgs)
       if IDE_doc.FullPath:
          replaceAllInDirCurrFileButton.Bind(wx.EVT_BUTTON,
             lambda crap: replaceAllInDirRootCB.SetValue(IDE_doc.DirName) or
                IDE_updateReplaceInDirFilesList(*updateArgs))
       else:
          replaceAllInDirCurrFileButton.Disable()
       recurseCB.Bind(wx.EVT_CHECKBOX, Functor(IDE_updateReplaceInDirFilesList,*updateArgs))

    prevNextSizer.Add(prevButton)
    prevNextSizer.Add(nextButton)
    gridSizer.Add(findText,0,wx.TOP|wx.ALIGN_RIGHT,5)
    gridSizer.Add(findInput)
    gridSizer.Add((0,0))
    gridSizer.Add(reCB,0,wx.BOTTOM,5)
    if replace:
       gridSizer.Add((0,3))
       gridSizer.Add((0,3))
       gridSizer.Add(replaceText,0,wx.TOP|wx.ALIGN_RIGHT,5)
       gridSizer.Add(replaceInput)
       gridSizer.Add((0,-1))
       gridSizer.Add(slashCB)
       partialSizer.Add(promptCB, 0, wx.ALIGN_CENTER, 5)
       partialSizer.Add(prevNextSizer, 0, wx.ALIGN_CENTER)
    vertSizer.Add(gridSizer, 0, wx.ALL|wx.ALIGN_CENTER, 5)
    vertSizer.Add((0,-1), 0, wx.ALL, 5)
    vertSizer.Add(caseCB, 0, wx.LEFT|wx.BOTTOM, 5)
    vertSizer.Add(wholeWordCB, 0, wx.LEFT|wx.BOTTOM, 5)
    vertSizer.Add(wildcardsCB, 0, wx.LEFT|wx.BOTTOM, 5)
    vertSizer.Add(wx.StaticLine(panel), 0, wx.BOTTOM|wx.EXPAND, 5)
    if replace:
       replaceAllButtons1Sizer.Add(replaceAllInFileButton, 0, wx.ALIGN_CENTER, 5)
       replaceAllButtons1Sizer.Add(replaceAllInOpenedFileButton, 0, wx.ALIGN_CENTER, 5)
       replaceAllGridSizer.Add(replaceAllInDirText, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
       replaceAllGridSizer.Add(replaceAllInDirRootCB, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
       replaceAllGridSizer.Add(replaceAllInDirBrowseButton, 0, wx.ALIGN_CENTER, 5)
       replaceAllGridSizer.Add(replaceAllInDirCurrFileButton, 0, wx.ALIGN_CENTER, 5)
       replaceAllSizer2.Add(recurseCB, 0, wx.ALIGN_CENTER, 5)
       replaceAllSizer2.Add((40,0))
       replaceAllSizer2.Add(replaceAllInDirExtText, 0, wx.ALIGN_CENTER, 5)
       replaceAllSizer2.Add(replaceAllInDirExtCB, 0, wx.ALIGN_CENTER, 5)
       replaceAllGridSizer.Add((0,0))
       replaceAllGridSizer.Add(replaceAllSizer2, 0, wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
       replaceAllGridSizer.Add(refreshButton, 0, wx.ALIGN_CENTER, 5)
       currFileText=wx.StaticText(panel,-1,'current file : "%s"'%IDE_doc.FileName)
       topBot=wx.TOP|wx.BOTTOM if currFileText.Size.y!=promptCB.Size.y else 0
       replaceAllSizer.Add(currFileText, 0, topBot|wx.ALIGN_CENTER, 5)
       replaceAllSizer.Add(replaceAllButtons1Sizer, 0, wx.ALIGN_CENTER, 5)
       replaceAllInFilesSizer.Add(replaceAllGridSizer, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER, 5)
       replaceAllInFilesSizer.Add(replaceAllInDirFilesList, 0, wx.TOP|wx.ALIGN_CENTER|wx.EXPAND, 5)
       replaceAllInFilesSizer.Add(replaceAllInDirButton, 0, wx.TOP|wx.ALIGN_CENTER, 5)
       replacePartialOrAllSizer.Add(partialSizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 5)
       replacePartialOrAllSizer.Add(replaceAllSizer, 0, wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 5)
       vertSizer.Add(replacePartialOrAllSizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER, 5)
       vertSizer.Add(replaceAllInFilesSizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_CENTER|wx.EXPAND, 5)
    else:
       vertSizer.Add(prevNextSizer, 0, wx.BOTTOM|wx.ALIGN_CENTER, 5)

    for c in getWxSizerWidgets(vertSizer):
        c.Bind(wx.EVT_CHAR,Functor(IDE_findProcessWxChar,nextButton))
        # handles navigational wx events
        if WIN:
           c.Bind(wx.EVT_KEY_DOWN,handleNavigationalWxEvents)

    panel.SetSizer(vertSizer)
    vertSizer.Fit(frame)
    vertSizer.SetSizeHints(frame)
    frame.Center()
    frame.Show()
    findInput.SetFocus()

def IDE_doFind(dir,replaceInput=0,promptCB=None,slashCB=None,
        findInput=0,reCB=0,caseCB=0,wholeWordCB=0,wildcardsCB=0,frame=0,e=None):
    global IDE_FIND_re,IDE_FIND_caseSensitive,IDE_FIND_wholeWord,IDE_FIND_wildcards,\
      IDE_REPLACE_prompt,IDE_REPLACE_slash,\
      IDE_REPLACE_lastNumReplaced,IDE_REPLACE_numReplaced
    v=findInput.GetValue() if findInput else IDE_FIND_list[0] if IDE_FIND_list else 0
    if not v: return
    slash=slashCB.GetValue() if slashCB else IDE_REPLACE_slash
    replace=bool(replaceInput) or type(replaceInput) in STRINGTYPE
    newV=replaceInput.GetValue() if type(replaceInput)==wx.ComboBox else replaceInput if replace else 0
    if type(slashCB)==wx.CheckBox:
       if newV:
          if newV in IDE_REPLACE_list:
             IDE_REPLACE_list.remove(newV)
          IDE_REPLACE_list.insert(0,newV)
          if slash: # converts escape sequence
             exec("newV='%s'"%newV)
       IDE_REPLACE_slash=slash
    IDE_FIND_re = isRE = reCB.GetValue() if reCB else IDE_FIND_re
    if type(reCB)==wx.CheckBox:
       if v in IDE_FIND_list:
          IDE_FIND_list.remove(v)
       IDE_FIND_list.insert(0,v)
    prompt=promptCB.GetValue() if type(promptCB)==wx.CheckBox else promptCB if promptCB is not None else IDE_REPLACE_prompt
    if type(promptCB)==wx.CheckBox:
       IDE_REPLACE_prompt=prompt
    IDE_FIND_caseSensitive=caseSensitive=caseCB.GetValue() if caseCB else IDE_FIND_caseSensitive
    IDE_FIND_wholeWord=wholeWord=wholeWordCB.GetValue() if wholeWordCB else IDE_FIND_wholeWord
    IDE_FIND_wildcards=wildcards=wildcardsCB.GetValue() if wildcardsCB else IDE_FIND_wildcards
    if frame:
       IDE_closeWxInterface(frame)
       WxStep()

    if replace and not prompt and IDE_REPLACE_numReplaced is None:
       IDE_REPLACE_numReplaced=0
       msg=createMsg('Replacing, please wait.....',fg=(0,0,0,1),bg=(.9,.8,.4,.85))
       putMsg(msg,'replacing text',0,stat=True)
       renderFrame(2)
       msg.removeNode()

    # must be escaped before replacing the wildcards, or it would be escaped too
    if not isRE:
       v=re.escape(v)
    if wildcards:
       v=v.replace('\\*','.+?').replace('\\?','.') # excludes empty string
    ww=r'\b'*wholeWord
    cS=re.IGNORECASE*(not caseSensitive)
    pat=re.compile(v if isRE else '%s%s%s'%(ww,v,ww),cS)
    isLoadedFile=type(IDE_doc)!=types.FunctionType
    numReplaced=0
    found=False
    if dir==-1 : # REPLACE ALL
       if isLoadedFile:
          # prepares for replace all occurences, bring the cursor to document start
          IDE_doc.line=IDE_doc.column=0
          IDE_doc.isSelecting=False
          IDE_updateCurPos()
          IDE_updateBlock()
          __exposeCurrentLine()
       dir=1 # and go forward
    if dir: #_____ forward
       for l in range(IDE_doc.line,IDE_doc.numLines):
           s=IDE_doc.File[l][IDE_doc.column if IDE_doc.line==l else 0:]
           res=pat.search(s)
           if res:
              start=res.start(0)
              end=res.end(0)
              IDE_doc.isSelecting=False
              IDE_doc.column=(IDE_doc.column if IDE_doc.line==l else 0) + start
              IDE_doc.line=l
              IDE_setSelection(True)
              IDE_doc.column+=end-start
              if IDE_doc.column>0 and len(IDE_doc.File[l])==IDE_doc.column and \
                   IDE_doc.File[l][IDE_doc.column-1]=='\n':
                 IDE_doc.line+=1
                 IDE_doc.column=0
              found=True
              break
    else: #_____ backward
       end=0
       for l in range(IDE_doc.line,-1,-1):
           s=IDE_doc.File[l]
           if IDE_doc.line==l:
              s=s[:IDE_doc.column]
           while 1:
                 res=pat.search(s,end)
                 if res:
                    start=res.start(0)
                    end=res.end(0)
                    found=True
                 else:
                     break
           if found:
              IDE_doc.isSelecting=False
              IDE_doc.column=end
              IDE_doc.line=l
              endsWithEoL=IDE_doc.column>0 and len(IDE_doc.File[l])==IDE_doc.column and \
                IDE_doc.File[l][IDE_doc.column-1]=='\n'
              if endsWithEoL:
                 IDE_doc.line+=1
                 IDE_doc.column=0
              IDE_setSelection(True)
              if endsWithEoL:
                 IDE_doc.line-=1
              IDE_doc.column=start
              break

    if found:
       if isLoadedFile and (not replace or (replace and prompt)):
          IDE_updateCurPos()
          IDE_updateBlock()
          __exposeCurrentLine()
       if replace:
          if prompt:
             if IDE_dialog is None:
                IDE_confirmReplace(IDE_replaceConfirmedLastOccurence,[dir,newV,prompt])
             oldZ=IDE_textCursor.getZ(IDE_root)
             coveredZone=.575*IDE_dialog.height
             visibleZone=coveredZone*1.5
             z=clampScalar(-visibleZone,visibleZone,
               -coveredZone*oldZ/abs(oldZ)) if -coveredZone<oldZ<coveredZone else 0
             if z!=oldZ:
                lastPos=IDE_dialog.root.getPos()
                IDE_dialog.root.setZ(IDE_root,z)
                IDE_dialog.root.posInterval(.2,IDE_dialog.root.getPos(),lastPos,
                  blendType='easeOut',name=IDE_ivalsName+'updown dialog'
                  ).start()
             return
          else:
             return dir,newV,prompt,True
    else:
       if IDE_dialog: # prompted replace
          IDE_closeConfirmReplaceDialog()
          global IDE_lastMode
          IDE_lastMode=IDE_getMode()
          IDE_setMode(MODE_noInput)
          IDE_openOkDialog('REPLACE : no more match found',IDE_setMode,IDE_lastMode)
       elif replace: # non-prompted replace
          if IDE_REPLACE_numReplaced:
             IDE_setMessage('REPLACE: replaced %s occurence(s)'%IDE_REPLACE_numReplaced)
          else:
             IDE_setMessage('REPLACE: no match')
          IDE_REPLACE_lastNumReplaced=IDE_REPLACE_numReplaced
          IDE_REPLACE_numReplaced=None
       else:
          IDE_setMessage('FIND %s: no match'%('NEXT' if dir else 'PREV'))
    return dir,newV,prompt,False

def IDE_confirmReplace(confirmFunc,args):
#     Whalf=.5
#     Hhalf=.15
#     vtx=[
#       (-Whalf,Hhalf),
#       (-Whalf,0),
#       (-Whalf+Hhalf,-Hhalf),
#       (Whalf,-Hhalf),
#       (Whalf,0),
#       (Whalf-Hhalf,Hhalf),
#     ]
#     butPoly=DU.createPolygon(vtx,color=(20,50,80,230))
#     butPoly.reparentTo(aspect2d)
#     DU.createPolygonEdge(vtx,(0,.5,.8),3).reparentTo(aspect2d)
#     print 'BUTTON CREATED'
    global IDE_lastMode,IDE_dialog
    # IDE_lastMode is already "active" mode
    IDE_setMode(MODE_replacing)
    ync=loader.loadModel('models/yncDialog/ync')
    headlight=ync.find('**/rigHeadlightOn')
    Sequence( headlight.colorScaleInterval(.25,Vec4(1,1,1,0)),
              Wait(.2),
              headlight.colorScaleInterval(.2,Vec4(1,1,1,1)),
              name=IDE_ivalsName+'dialog headlight blink'
            ).loop()
    b3=ync.getTightBounds()
    text=OnscreenText(parent=ync,text='Replace this occurence ?',font=IDE_FONT_monospace,scale=IDE_dialogMsgScale)
    textB3=text.getTightBounds()
    text.setZ((textB3[1]-textB3[0])[2]+IDE_dialogMsgPad*IDE_FONT_monospace.getLineHeight()*IDE_dialogMsgScale)
    bx=max((b3[1]-b3[0])[0]*.485,(textB3[1]-textB3[0])[0]*.5+.05)/ync.getSx()
    CM=CardMaker('')
    CM.setFrame(-bx,bx,0,2*text.getBounds().getCenter()[2])
    dialogBG=loader.loadTexture('models/yncDialog/dialogBG.png')
    cardParent=ync.attachNewNode('textBG',sort=-1)
    card=cardParent.attachNewNode(CM.generate(),sort=-1)
    card.setTexScale(TextureStage.getDefault(),1,text.getBounds().getCenter()[2]*IDE_dialogUVscale)
    card.setTexture(dialogBG)
    card.setTransparency(TransparencyAttrib.MAlpha)
    text.wrtReparentTo(cardParent)
    ync.prepareScene(base.win.getGsg())
    ync.node().setBounds(OmniBoundingVolume())
    ync.node().setFinal(1)
    renderFrame()
    ync.node().setFinal(0)
    ync.node().clearBounds()
    ync.reparentTo(IDE_overlayParent)
    ync.setZ(IDE_2Droot,-1.2)
    ync.setBin('gaugeBin',1)

    buttons = [
       IDEPolyButton.myButton(ync, 'y', ('hover','pressed'), hitKey='y',
          command=Functor(confirmFunc,*(args+[True])),
          enable=1, stayAlive=1, text='Yes',font=IDE_FONT_transmetals),
       IDEPolyButton.myButton(ync, 'n', ('hover','pressed'), hitKey='n',
          command=Functor(confirmFunc,*(args+[False])),
          enable=1, stayAlive=1, text='No',font=IDE_FONT_transmetals,
          textScale=.07,textPos=(0,-.15)),
       # sets the CANCEL button as default one, so pack it in a sequence
       [IDEPolyButton.myButton(ync, 'c', ('hover','pressed'), hitKey=('c','escape'),
          command=Functor(confirmFunc,*(args+[None])),
          enable=1, stayAlive=1, text='Cancel',font=IDE_FONT_transmetals)
          ],
       ]
    buttons[2][0].text.setSx(-1)

    IDE_dialog = IDEPolyButton.myDialog(
        root = ync,
        pos = (0,0,0), scale=IDE_dialogScale,
        buttons=buttons, keyboard=True
        )
    minb,maxb=IDE_dialog.root.getTightBounds()
    dim=maxb-minb
    IDE_dialog.height=IDE_root.getRelativeVector(IDE_dialog.root.getParent(),Vec3(0,0,dim[2]))[2]
    IDE_dialog.uvFlow = LerpFunc(
       lambda v:card.setTexOffset(TextureStage.getDefault(),0,v), duration=.4)
    IDE_dialog.uvFlow.loop()
    IDEPolyButton.start()

def IDE_closeConfirmReplaceDialog():
    global IDE_dialog
    IDEPolyButton.stop()
    IDE_dialog.uvFlow.pause()
    IDE_dialog.cleanup()
    IDE_dialog=None
    IDE_setMode(IDE_lastMode)

def IDE_replaceConfirmedLastOccurence(dir,newV,prompt,confirmed=True):
    if confirmed is None:
       IDE_closeConfirmReplaceDialog()
       return
    if confirmed:
       IDE_doReplace(dir,newV,prompt)
    IDE_doFind(dir,newV,prompt)

def IDE_replaceAllInCurrFile(validInput,replaceAllArgs,e):
    global REPLACING,UPDATE_DISPLAY
    if not validInput(): return
    doc=e.GetEventObject().__currFile
    if doc!=IDE_doc:
       doc.setDocActive(tempSwitch=True)
    REPLACING=True
    UPDATE_DISPLAY=False
    IDE_doc.groupHistoryOn=False # be sure to cut edit history grouping
    # and remember the current index to pack the replacement actions
    # so it can be undone altogether
    lastHistoryIdx=IDE_doc.historyIdx
    startT=globalClock.getRealTime()
    dir,newV,prompt,found=IDE_doFind(*replaceAllArgs)
    while found:
       IDE_doReplace(dir,newV,prompt)
       found=IDE_doFind(dir,newV,prompt)[3]
    print('REPLACE completed in :',globalClock.getRealTime()-startT, file=IDE_DEV)
    IDE_packHistoryEntriesSince(lastHistoryIdx)
    REPLACING=False
    UPDATE_DISPLAY=True
    IDE_setHilighter(IDE_doc.hilight) # force recollect quotes
    adjustCanvasLength(IDE_doc.numLines,forced=1)
    IDE_updateCurPos()
    IDE_updateBlock()
    __exposeCurrentLine()
    IDE_arrangeDocsTabs()

def IDE_doReplace(dir,newV,prompt):
    global IDE_REPLACE_numReplaced
    if newV:
       UnewV=newV.replace('\r\n','\n').replace('\r','\n') # use universal newline
       IDE_paste(UnewV,smartPaste=False)
    else:
       IDE_delSelection()
    if not prompt:
       IDE_REPLACE_numReplaced+=1

def IDE_replaceInAllOpenedFiles(*args):
    if not args[4].GetValue(): # search value
       return
    global UPDATE_DISPLAY
    UPDATE_DISPLAY=False
    lastDoc=IDE_doc
    totalReplaced=numEditedFiles=0
    if type(args[-1])==list:
       docs=args[-1]
       args=args[:-1]
    else:
       docs=IDE_documents
    for f in docs:
        if not f.readonly:
           f.setDocActive(tempSwitch=1)
           IDE_doc.groupHistoryOn=False # be sure to cut edit history grouping
           # and remember the current index to pack the replacement actions
           # so it can be undone altogether
           lastHistoryIdx=IDE_doc.historyIdx
           if args is None:
              # pass -1 instead of dir so each file's cursor will be put at 0:0
              # before searching
              found=IDE_doFind(-1,newV,prompt)[3]
           else:
              dir,newV,prompt,found=IDE_doFind(*args)
              args=None
           while found:
              IDE_doReplace(dir,newV,prompt)
              found=IDE_doFind(dir,newV,prompt)[3]
           print('\n   %s: replaced %s occurence(s)'%(f.FileName,IDE_REPLACE_lastNumReplaced))
           if IDE_REPLACE_lastNumReplaced:
              IDE_packHistoryEntriesSince(lastHistoryIdx)
              totalReplaced+=IDE_REPLACE_lastNumReplaced
              numEditedFiles+=1
           adjustCanvasLength(IDE_doc.numLines,forced=1)
           IDE_updateCurPos()
           IDE_updateBlock()
           __exposeCurrentLine()
    UPDATE_DISPLAY=True
    IDE_arrangeDocsTabs()
    msg='REPLACE ALL: replaced %s occurence(s) in %s opened file(s)'%(totalReplaced,numEditedFiles)
    print(msg)
    IDE_setMessage(msg)
    lastDoc.setDocActive(tempSwitch=1)
    return dir,newV,prompt,totalReplaced,numEditedFiles

def IDE_confirmReplaceInFilesInDir(validInput,rootCB,extCB,filesList,recurseCB,replaceAllArgs,e):
    numSel=filesList.GetSelectedItemCount()
    if not (validInput() and numSel): return
    files=filesList.__fullPathFiles
    sel=[files[filesList.GetItemData(i)] for i in range(len(files)) if filesList.IsSelected(i)]
#     print '##############################\n'+'\n'.join(sel)
    opened=[d for d in IDE_documents if d.FullPath in sel]
    numOpened=len(opened)
    IDE_spawnWxModal( IDE_spawnWxYesNoDialog,(
        '''Selection : %s opened, %s external files
%s
Are you sure to replace all occurences in %s selected file%s ?'''\
        %(numOpened,len(sel)-numOpened,
         '\nBIG WARNING : This process can NOT be undone for external files.\n'*(len(sel)-numOpened>0),
         ('these '+str(numSel)) if numSel>1 else 1, 's'*(numSel>1)),
        IDE_replaceInFilesInDir,[rootCB,extCB,recurseCB,sel,opened,replaceAllArgs]),
        e)

def IDE_replaceInFilesInDir(args):
    if not args: return
    global IDE_REPLACE_recurse, IDE_REPLACE_dirFilter, IDE_REPLACE_dirList, IDE_doc, HISTORY_ON
    rootCB,extCB,recurseCB,files,opened,replaceAllArgs=args
    IDE_REPLACE_recurse=recurseCB.GetValue()
    root=rootCB.GetValue()
    if root in IDE_REPLACE_dirList:
       IDE_REPLACE_dirList.remove(root)
    IDE_REPLACE_dirList.insert(0,root)
    ext=extCB.GetValue()
    if ext in IDE_REPLACE_dirFilter:
       IDE_REPLACE_dirFilter.remove(ext)
    IDE_REPLACE_dirFilter.insert(0,ext)
    openedPaths=[d.FullPath for d in opened]
    notOpenedFiles=difference(files,openedPaths)
#     print 'opened: (%s)\n'%len(opened),'\n'.join(openedPaths)
    totalReplaced=numEditedFiles=0
    externalReplaced=numEditedExternalFiles=0
    if opened:
       replaceAllArgs.append(opened)
       dir,newV,prompt,totalReplaced,numEditedFiles=IDE_replaceInAllOpenedFiles(*replaceAllArgs)
       replaceAllArgs=None
    if notOpenedFiles:
       lastDoc=IDE_doc
       lastHISTORY_ON=HISTORY_ON
       HISTORY_ON=False
       for externalFile in notOpenedFiles:
           IDE_doc=lambda:0
           IDE_doc.line=IDE_doc.column=0
           IDE_doc.isSelecting=False
           IDE_doc.readonly=False
           IDE_doc.recordMacro=False
           f=open(externalFile,'rU')
           IDE_doc.File=[ l.expandtabs() for l in f.readlines() ] # I HATE TABs
           f.close()
           IDE_doc.numLines=len(IDE_doc.File)
           if IDE_doc.File[-1].endswith('\n'):
              IDE_doc.numLines+=1
              IDE_doc.File.append('')
           if replaceAllArgs is None:
              found=IDE_doFind(dir,newV,prompt)[3]
           else:
              dir,newV,prompt,found=IDE_doFind(*replaceAllArgs)
              replaceAllArgs=None
           while found:
              IDE_doReplace(dir,newV,prompt)
              found=IDE_doFind(dir,newV,prompt)[3]
           print('(EXTERNAL) %s: replaced %s occurence(s)'%(os.path.basename(externalFile),IDE_REPLACE_lastNumReplaced))
           # save only if it was changed
           if IDE_REPLACE_lastNumReplaced:
              errstr=IDE_doWriteFile(externalFile,IDE_doc.File)
              if errstr:
                 print('  ERROR: unable to save file,',errstr)
                 break
              externalReplaced+=IDE_REPLACE_lastNumReplaced
              numEditedExternalFiles+=1
#               print 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
#               print ''.join(IDE_doc.File)
       IDE_doc=lastDoc
       HISTORY_ON=lastHISTORY_ON
    msg='REPLACE ALL: replaced %s occurence(s) in %s opened file(s), %s in %s external file(s)' \
       %(totalReplaced,numEditedFiles,externalReplaced,numEditedExternalFiles)
    print(msg)
    IDE_setMessage(msg)


################################################################################
# APPEARANCE & GENERAL COLORS UPDATE

def IDE_updateCaretsTypes():
    IDE_textCursor.removeChildren()
    IDE_REALtextCursor[IDE_CFG[CFG_insCaret]].copyTo(IDE_textCursor)
    IDE_REALtextCursor[IDE_CFG[CFG_ovrCaret]].copyTo(IDE_textCursor)
    if 'IDE_doc' in globals() and IDE_doc:
       IDE_doToggleInsert(IDE_insert)

def IDE_updateGeneralColors():
    if IDE_documents:
       for d in IDE_documents:
           if d.FullPath==APP_mainFile:
              bg=IDE_COLOR_tabLabelMainModActive if d==IDE_doc else IDE_COLOR_tabLabelMainModInactive
           else:
              bg=IDE_COLOR_tabLabelOtherModActive
           d.tab['text_fg']=IDE_COLOR_tabTextActive if d==IDE_doc else IDE_COLOR_tabTextInactive
           d.tabLabel.setColorScale(bg,1)
           d.callTipBG.setColorScale(IDE_COLOR_callTipsBG)
           if not d.callTipParent.isHidden():
              d.callTipParent.find('**/CT').setColor(IDE_COLOR_callTipsText)
       if IDE_log:
          IDE_log.textParent.setColorScale(IDE_COLOR_log,priority=-10)
    IDE_textCursor.setColorScale(IDE_COLOR_caret)
    IDE_textCursorIval[0].setEndColorScale(IDE_COLOR_caret)
    IDE_REALblock.setColor(IDE_REALblockGetColor())
    IDE_CTargHL.setColor(IDE_COLOR_callArgsBG,1)
    IDE_CTargHL.getChild(0).setColorScale(IDE_COLOR_callTipsText,10)
    IDE_frame['frameColor']=IDE_frameGetColor()
    logOverScene=IDE_logOverSceneParent.find(IDE_logOverSceneNodeName)
    if not logOverScene.isEmpty():
       logOverScene.setColorScale(IDE_COLOR_logOverScene,2)
    IDE_docsTabsBG['frameColor']=statusBar['frameColor']=IDE_tabsNstatusBarBGgetColor()
    SliderBG['frameColor']=SliderBGgetColor()
    IDE_markersBar.setColorScale(IDE_markersBarGetColor(),10)
    for ost in (IDE_curPosText,IDE_marksStatusText,IDE_macroNotif,IDE_errNotif,
                IDE_pauseStatusText,IDE_messageLine):
        ost['fg']=IDE_COLOR_statusText
    IDE_updateCCcolors()
    IDE_updateSGBcolors()

def IDE_updateCCcolors():
    CCdescClearCol = Vec4(*IDE_availCodesListGetColor())
    for o in (IDE_availCodesList.Frame,CCtextBG,IDE_objDesc.Frame,IDE_resolutionsList.Frame):
        o['frameColor'] = CCdescClearCol
    fg = Vec4(*IDE_availCodesListFGgetColor())
    IDE_availCodesList.setRolloverColor(fg)
    IDE_resolutionsList.setRolloverColor(fg)
    if not IDE_objDesc.Frame.isHidden():
       IDE_CC_displayDesc(later=False)

def IDE_updateSGBcolors():
    BGcol = Vec4(*IDE_availCodesListGetColor())
    SGBframe['frameColor']=NProps.frame['frameColor']=BGcol
    FGcol = Vec4(*IDE_availCodesListFGgetColor())
    NProps.setTextColor(FGcol)
    invBGcol = Vec4(1-BGcol[0],1-BGcol[1],1-BGcol[2],1)
    SGB.setTextColor(FGcol,rebuild=False)
    SGB.setRolloverColor(invBGcol)

def IDE_setBlockColorAnim(animate):
    IDE_CFG[CFG_animSelColor]=animate
    getattr(IDE_REALblockIval,'loop' if animate else 'finish')()

def IDE_adjustWSopacity(inc):
    IDE_CFG[CFG_WSopacity]=clampScalar(0,100,IDE_CFG[CFG_WSopacity]+inc)
    IDE_frame['frameColor']=IDE_frameGetColor()

def IDE_adjustCCopacity(inc):
    IDE_CFG[CFG_CCopacity]=clampScalar(0,100,IDE_CFG[CFG_CCopacity]+inc)
    IDE_updateCCcolors()

def IDE_setWSfontProps(size,Hspc,updateLogTex=False):
    M.IDE_fontPixelsPerUnit=size
    M.IDE_fontTexMargin=Hspc
    IDE_setupWSfont()
    IDE_REALblockIval.pause()
    IDE_REALblock.removeNode()
    createREALblock()
    IDE_REALbrHL.removeNode()
    IDE_REALbrMatchHL.removeNode()
    createREALbrHL()
    IDE_textCursor.setScale(IDE_all_chars_maxWidth/IDE_REALtextCursorOrigScale[0],1,
      IDE_lineheight/IDE_REALtextCursorOrigScale[2])
    if updateLogTex:
       # removes all logOverScene textures for all OSes,
       # so it will be updated the next time the IDE runs on other OSes 
       texName=IDE_logOverSceneTexPath.split('-')[0]
       for f in glob(texName+'*'):
           try:
               os.remove(f)
           except:
               pass
       msgText=logTexGenText%('obsolete','Updating')
       M.isLogTexObsolete=True
       createLogTextTexture(msgText)
    if IDE_doc:
       for d in IDE_documents:
           d.textParent.setTexture(IDE_normal_chars_tex)
           d.blockParent.setScale(IDE_textScale)
           d.textParent.setScale(IDE_textScale)
           d.callTipParent.setScale(IDE_textScale)
           d.lineMarkParent.setScale(IDE_textScale)
           height=-IDE_lineheight
           for m in asList(d.lineMarkParent.getChildren()):
               m.setZ(int(m.getName())*height)
       adjustCanvasLength(IDE_doc.numLines if IDE_doc else 0,forced=True)
       IDE_refreshWorkspace(all=True)
       IDE_updateCurPos()
       IDE_updateBlock()
       if not IDE_doc.callTipParent.isHidden():
          IDE_doc.hideCallTip()
       IDE_handleWindowEvent(base.win,forced=True)
       renderFrame()


################################################################################

NProps = NodeProps(textColor=IDE_availCodesListFGgetColor())
SGB_overScene = SGB_useBBox = False
SGBframeOverScene = None

def SGB_useNoBoundsHilight():
    IDE_removeAnyMenuNcallTip()
    sel = NProps.getNodePath()
    if sel is not None:
       sel.hideBounds()

def SGB_nodeSelected(n):
    SGB_useNoBoundsHilight()
    NProps.setNodePath(n)
    NProps_wrapAroundSGB()
    n.showTightBounds() if SGB_useBBox else n.showBounds()

def SGB_toggleCollSolids(n,SGBitem,show):
    if show:
       n.showCS()
    else:
       n.hideCS()
    SGB.updateItemIcons(SGBitem,recursive=True)

def SGB_copyHierarchyText(n,rev):
    ss = StringStream()
    if rev:
       n.reverseLs(ss)
    else:
       n.ls(ss)
    IDE_copy(ss.getData())
    msg = createMsg('Hierarchy text copied to clipboard.',bg=(0,1,0,.85))
    putMsg(msg,'hierarchy copied',2)

def SGB_copyCharParts(n,valToo):
    ss = StringStream()
    if valToo:
       n.writePartValues(ss)
    else:
       n.writeParts(ss)
    IDE_copy(ss.getData())
    msg = createMsg('Character hierarchy copied to clipboard.',bg=(0,1,0,.85))
    putMsg(msg,'hierarchy copied',2)

def SGB_copyGeomsInfo(n,detailed):
    ss = StringStream()
    if detailed:
       n.writeVerbose(ss,2)
    else:
       n.writeGeoms(ss,2)
    IDE_copy(ss.getData())
    msg = createMsg('Geoms info copied to clipboard.',bg=(0,1,0,.85))
    putMsg(msg,'geoms info copied',2)

def SGB_copyModelPoolInfo():
    ss = StringStream()
    ModelPool.listContents(ss)
    IDE_copy(ss.getData())
    msg = createMsg('ModelPool info copied to clipboard.',bg=(0,1,0,.85))
    putMsg(msg,'ModelPool info copied',2)

def SGB_toggleNodeVis(n,SGBitem):
    n.show() if n.isHidden() else n.hide()
    SGB.updateItemIcons(SGBitem)

def SGB_listNodeTags(n):
    print('\nNODE TAGS :')
    n.listTags()

def SGB_createContextMenu(n,SGBitem):
    node = n.node()
    nodeType = type(node) 
    def setRM(m,thickness,pri):
        n.setRenderMode(m,thickness,pri)
        SGB.updateItemIcons(SGBitem)
    renderModes = [ 
      (setRM if n.getRenderMode()!=rm else 0,rm,1,1) \
        for rm in (RenderModeAttrib.MWireframe,
                   RenderModeAttrib.MFilled, RenderModeAttrib.MPoint)
    ]

    items = ()
    if nodeType==Camera:
       frustumVis = n.find('frustum')
       hasFrustumVis = not frustumVis.isEmpty() and type(frustumVis.node())==GeomNode
       items+=(
         ('%s _frustum'%('Hide' if hasFrustumVis else 'Show'),0, node.hideFrustum if hasFrustumVis else node.showFrustum),
         0,
       )
    items += (
      ('_Show collision solids',0,SGB_toggleCollSolids,n,SGBitem,True),
      ('_Hide collision solids',0,SGB_toggleCollSolids,n,SGBitem,False),
      0,
      ('Toggle _visibility','IDE_visibility.png',SGB_toggleNodeVis,n,SGBitem),
      ('_Render mode',0, (
        ('_Wireframe',0,)+renderModes[0],
        ('_Filled',0,)+renderModes[1],
        ('_Point',0,)+renderModes[2],
      )),
      0,
      ('Set _as root',0,IDE_refreshSGB,n),
      0,
      ('List _tags','IDE_tag.png')+((0,) if SGBitem.holder.find('**/icon_tag').isEmpty() else (SGB_listNodeTags,n)),
      ('_Copy hierarchy','IDE_copy.png', SGB_copyHierarchyText, n, False),
      ('Copy reversed hierarchy','IDE_copy.png', SGB_copyHierarchyText, n, True),
#         ('Place()',0,lambda:n.place() ),
    )
    if nodeType==Character:
       items+=(
         0,
         ("Copy char's parts",0,SGB_copyCharParts,node,False),
         ("Copy char's parts + values",0,SGB_copyCharParts,node,True),
       )
    elif nodeType==GeomNode:
       items+=(
         0,
         ('Copy geoms short info',0,SGB_copyGeomsInfo,node,False),
         ('Copy geoms detailed info',0,SGB_copyGeomsInfo,node,True),
       )
    elif nodeType==ModelRoot:
       items+=(
         0,
         ('List _ModelPool contents',0,SGB_copyModelPoolInfo),
       )


    nodeContextMenu = PopupMenu(
#       parent=IDE_overlayParent,
      parent=SGBframe,
      buttonThrower=None if IDE_root.isHidden() else IDE_BTnode,
      items=items,
      font=IDE_FONT_medrano, baselineOffset=-.27,
      scale=IDE_statusBarHeight*.65, itemHeight=1.05,
      leftPad=.2, separatorHeight=.45,
      underscoreThickness=2,
      BGColor=(.3,.3,.2,.9),
      BGBorderColor=(.8,.3,0,1),
      separatorColor=(1,1,1,1),
      frameColorHover=(1,.8,.3,1),
      frameColorPress=(0,1,0,1),
      textColorReady=(1,1,1,1),
      textColorHover=(0,0,0,1),
      textColorPress=(0,0,0,1),
      textColorDisabled=(.45,.45,.45,1),
      minZ=IDE_calcMenuMinZ()
    )
    nodeContextMenu.menu.setBin('gaugeBin',1)

def SGB_chooseRoot():
    IDE_removeAnyMenuNcallTip()
    chooseRootMenu = PopupMenu(
      parent=SGB.rootTitle,
      buttonThrower=None if IDE_root.isHidden() else IDE_BTnode,
      items=(
        ('render',0)+((0,) if SGB.root==render else (IDE_refreshSGB,render)),
        ('render2d',0)+((0,) if SGB.root==render2d else (IDE_refreshSGB,render2d)),
      ),
      font=IDE_FONT_medrano, baselineOffset=-.27,
      scale=IDE_statusBarHeight*.65, itemHeight=1.05,
      leftPad=.2, separatorHeight=.45,
      underscoreThickness=2,
      BGColor=(.3,.3,.2,.9),
      BGBorderColor=(.8,.3,0,1),
      separatorColor=(1,1,1,1),
      frameColorHover=(1,.8,.3,1),
      frameColorPress=(0,1,0,1),
      textColorReady=(1,1,1,1),
      textColorHover=(0,0,0,1),
      textColorPress=(0,0,0,1),
      textColorDisabled=(.45,.45,.45,1),
      minZ=IDE_calcMenuMinZ()
    )
    chooseRootMenu.menu.setBin('gaugeBin',1)
    pos = ((DGG.UR, DGG.UL) if SGB.root==render else (DGG.LR, DGG.LL)) + ((.007,-.01),)
    Aligner.alignTo(*((chooseRootMenu.menu, SGB.chooseRootButton)+pos) )

def SGB_updateBoundingVol():
    IDE_removeAnyMenuNcallTip()
    SGB.useBBoxButton['image'] = 'IDE_bbox-%s.png'%('on' if SGB_useBBox else 'off')
    SGB.useBSphereButton['image'] = 'IDE_bsphere-%s.png'%('off' if SGB_useBBox else 'on')
    sel = NProps.getNodePath()
    if sel is not None:
       SGB_nodeSelected(sel)

def SGB_useBBoxHilight():
    M.SGB_useBBox = True
    SGB_updateBoundingVol()

def SGB_useBSphereHilight():
    M.SGB_useBBox = False
    SGB_updateBoundingVol()

def SGB_setOverScene():
    IDE_removeAnyMenuNcallTip()
    M.SGB_overScene = not SGB_overScene
    SGB.overSceneButton['image']='IDE_SGBoverScene-%s.png'%('on' if SGB_overScene else 'off')
    if not SGB_overScene and SGBframeOverScene is not None:
       SGBframeOverScene.removeNode()
       M.SGBframeOverScene=None


SGB = SceneGraphBrowser(
   parent=IDE_root, # where to attach SceneGraphBrowser frame
   root=None, # display children under this root node
   includeRoot=True,
   command=SGB_nodeSelected, # user defined method, executed when a node get selected,
                             # with the selected node passed to it
   contextMenu=SGB_createContextMenu, passItemToMenu=True,
   BTnode=IDE_BTnode,
   # selectTag and noSelectTag are used to filter the selectable nodes.
   # The unselectable nodes will be grayed.
   # You should use only selectTag or noSelectTag at a time. Don't use both at the same time.
   #selectTag=['select'],   # only nodes which have the tag(s) are selectable. You could use multiple tags.
   #noSelectTag=['noSelect','dontSelectMe'], # only nodes which DO NOT have the tag(s) are selectable. You could use multiple tags.
   # nodes which have exclusionTag wouldn't be displayed at all
   #exclusionTag=['internal component'],
   frameSize=(1,1.2),
   font=IDE_FONT_medrano, titleFont=IDE_FONT_transmetals,
   titleScale=.05, titleZ=.02,
   itemIndent=.05, itemScale=.035, itemTextScale=1.1, itemTextZ=0,
   textColor=Vec4(*IDE_availCodesListFGgetColor()), rolloverColor=(1,1,1,1),
   collapseAll=0, # initial tree state
   collapseAllImage='IDE_minus.png', collapseImage='IDE_downArrow.png',
   expandAllImage='IDE_plus.png', expandImage='IDE_rightArrow.png',
   hiddenIcon='IDE_hidden.png', tagIcon='IDE_tag.png',
   wireframeIcon='IDE_wireframe.png', pointIcon='IDE_point.png',
   mouseCallback=IDE_removeAnyMenuNcallTip,
   taskNamePrefix=IDE_tasksName,
   suppressMouseWheel=1,  # 1 : blocks mouse wheel events from being sent to all other objects.
                          #     You can scroll the window by putting mouse cursor
                          #     inside the scrollable window.
                          # 0 : does not block mouse wheel events from being sent to all other objects.
                          #     You can scroll the window by holding down the modifier key
                          #     (defined below) while scrolling your wheel.
   modifier='control'  # shift/control/alt
   )

def IDE_refreshSGB(newRoot=None):
    M.SGBisDirty=SGB.isHidden() and not SGBframeOverScene
    if SGBisDirty and not newRoot:
       return
    IDE_removeAnyMenuNcallTip()
    SGB.refreshSGBbutton.hide()
    tt = createMsg('REFRESHING...',bg=(1,0,0,1),pad=(1,1,.5,.5))
    tt.reparentTo(SGB.rootTitle)
    fr=SGB.rootTitle.node().getFrame()
    tt.setScale(.75*(fr[3]-fr[2]))
    Aligner.alignTo(tt,SGBframe,DGG.C)
    renderFrame(2)
    tt.removeNode()
    SGB.refreshSGBbutton.show()
    sel = NProps.getNodePath()
    if sel is not None:
       sel.hideBounds()
    NProps.setBlank()
    M.SGBisDirty = False
    if newRoot:
       SGB.setRoot(newRoot)
    else:
       if SGB.hasRoot:
          SGB.refresh()
       else:
          SGB.setRoot(render)
    rootTitleText = SGB.rootTitle.stateNodePath[0].find('**/+TextNode')
    Aligner.alignTo(SGB.refreshSGBbutton,rootTitleText,DGG.CR,DGG.CL,gap=(.2,0))
    Aligner.alignTo(SGB.chooseRootButton,rootTitleText,DGG.CL,DGG.CR,gap=(.2,0))

def IDE_toggleSGBAndNProps():
    SGB.toggleVisibility()
    if not SGB.isHidden() and SGBisDirty:
       IDE_refreshSGB()
    if SGB.isHidden():
       IDE_textCursorIval.resume()
    else:
       IDE_textCursorIval.pause()

def IDE_hideSGB():
    SGB.hide()
    SGB_LMBup()
    IDE_textCursorIval.resume()

def SGB_LMBdown(mwp):
    IDE_removeAnyMenuNcallTip()
    SGBframe.setAlphaScale(.15)
    mpos = base.mouseWatcherNode.getMouse()
    pos = SGBframe.getPos(render2dp)
    dragTask=taskMgr.add(SGB_dragFrame, dragSGBTaskName)
    dragTask.offset = mpos-Point2(pos[0],pos[2])
    dragTask._lastPos=Point2(mpos)

def SGB_dragFrame(t):
    if base.mouseWatcherNode.hasMouse():
       mpos = base.mouseWatcherNode.getMouse()
       if t._lastPos != mpos and -.95<mpos[0]<.95 and -.95<mpos[1]<.95:
          pos = mpos-t.offset
          SGBframe.setPos(render2dp,pos[0],0,pos[1])
          IDE_syncConfigInPreferences(CFG_SGBPos, (pos[0],0,pos[1]))
          t._lastPos = Point2(mpos)
    return Task.cont

def SGB_LMBup(mwp=None):
    taskMgr.remove(dragSGBTaskName)
    SGBframe.setAlphaScale(1)

def NProps_LMBdown(mwp):
    IDE_removeAnyMenuNcallTip()
    mpos = base.mouseWatcherNode.getMouse()
    pos = NProps.frame.getPos(render2dp)
    dragTask=taskMgr.add(NProps_dragFrame, dragNPropsTaskName)
    dragTask.offset = mpos-Point2(pos[0],pos[2])
    dragTask._lastPos = Point2(mpos)

def NProps_LMBup(mwp):
    taskMgr.remove(dragNPropsTaskName)

def NProps_dragFrame(t):
    if base.mouseWatcherNode.hasMouse():
       mpos = base.mouseWatcherNode.getMouse()
       if t._lastPos != mpos and -.95<mpos[0]<.95 and -.95<mpos[1]<.95:
          pos=mpos-t.offset
          NProps.frame.setPos(render2dp,pos[0],0,pos[1])
          NProps_wrapAroundSGB()
          t._lastPos = Point2(mpos)
    return Task.cont

def NProps_wrapAroundSGB():
    fs = NProps.frame['frameSize']
    NPropsDim = ( (fs[1]-fs[0])*NProps.frame.getSx(SGBframe),
                  (fs[3]-fs[2])*NProps.frame.getSz(SGBframe) )
    NPropsTop = fs[3]*NProps.frame.getSz(SGBframe)
    pos = NProps.frame.getPos(SGBframe)
    if SGBfs[0]-SGBpad[0]-NPropsDim[0] < pos[0] < SGBfs[1]+SGBpad[1] and\
       SGBfs[2]-SGBpad[2] < pos[2]+NPropsTop < SGBfs[3]+SGBpad[3]+NPropsDim[1]:
       midX = pos[0]+.5*NPropsDim[0]
       midZ = pos[2]+NPropsTop-.5*NPropsDim[1]
       closeToTop = SGBfs[3]+SGBpad[3]-midZ < midZ-SGBfs[2]-SGBpad[2]
       if closeToTop:
          dZ = SGBfs[3]+SGBpad[3]-(pos[2]+NPropsTop-NPropsDim[1])
       else:
          dZ = pos[2]+NPropsTop-SGBfs[2]-SGBpad[2]
       closeToRight = midX-SGBfs[0]>SGBfs[1]-midX
       if closeToRight:
          dX = SGBfs[1]+SGBpad[1]-pos[0]
       else:
          dX = pos[0]+NPropsDim[0]-(SGBfs[0]-SGBpad[0])

       # horizontal wins
       if dX<dZ:
          if closeToRight:
             pos.setX(SGBfs[1]+SGBpad[1])
          else:
             pos.setX(-SGBpad[0]-NPropsDim[0])
       # vertical wins
       else:
          if closeToTop:
             pos.setZ(SGBfs[3]+SGBpad[3]+NPropsDim[1]-NPropsTop)
          else:
             pos.setZ(SGBfs[2]-SGBpad[2]-NPropsTop)
       NProps.frame.setPos(SGBframe,pos)
    IDE_syncConfigInPreferences(CFG_NPropsPos, (pos[0],0,pos[2]))


SGBisDirty = True
SGBframe = SGB.childrenFrame
SGBframe.setBin('dialogsBin',0)
SGB.rootTitle.stateNodePath[0].reparentTo(SGB.rootTitle,sort=-10)
SGB.rootTitle.setBin('overDialogsBin',0)
SGBfs = SGBframe['frameSize']
SGBpad = (.05,.015,.005,.07)
for f in (SGBframe,SGB.rootTitle):
    f.bind(DGG.B1PRESS, SGB_LMBdown)
    f.bind(DGG.B1RELEASE, SGB_LMBup)
NProps.frame.bind(DGG.B1PRESS, NProps_LMBdown)
NProps.frame.bind(DGG.B1RELEASE, NProps_LMBup)

SGB.refreshSGBbutton = DirectButton(parent=SGB.rootTitle,image='IDE_refresh.png', relief=None,
   scale=.025,# pos=SGB.expandAllDB.getPos()+(SGB.expandAllDB.getPos()-SGB.collapseAllDB.getPos())*1.25,
   command=IDE_refreshSGB, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.refreshSGBbutton.alignTo(SGB.rootTitle, DGG.CL)
SGB.refreshSGBbutton.setTransparency(1)
SGB.refreshSGTT = createTooltip('Refresh',align=TextProperties.ALeft, alpha=0)
SGB.refreshSGTT.reparentTo(SGB.refreshSGBbutton.stateNodePath[2])
SGB.refreshSGTT.setSz(NProps.gotoModelLocDB,NProps.tooltipScale/SGB.refreshSGBbutton['scale'])
SGB.refreshSGTT.setSx(SGB.refreshSGTT.getSz())
SGB.refreshSGTT.setPos(SGB.refreshSGTT,.7,0,1.5)
SGB.refreshSGTT.copyTo(SGB.refreshSGBbutton.stateNodePath[1])
SGB.chooseRootButton = DirectButton(parent=SGB.rootTitle,image='IDE_downArrow.png', relief=None,
   scale=.02,# pos=SGB.expandAllDB.getPos()+(SGB.expandAllDB.getPos()-SGB.collapseAllDB.getPos())*1.25,
   command=SGB_chooseRoot, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.chooseRootButton.alignTo(SGB.rootTitle, DGG.CL)
SGB.chooseRootButton.setTransparency(1)
SGB.chooseRootTT = createTooltip('Choose root',align=TextProperties.ARight, alpha=0)
SGB.chooseRootTT.reparentTo(SGB.chooseRootButton.stateNodePath[2])
SGB.chooseRootTT.setSz(NProps.gotoModelLocDB,NProps.tooltipScale/SGB.chooseRootButton['scale'])
SGB.chooseRootTT.setSx(SGB.chooseRootTT.getSz())
SGB.chooseRootTT.setZ(SGB.chooseRootTT,1.5)
SGB.chooseRootTT.copyTo(SGB.chooseRootButton.stateNodePath[1])
SGB.overSceneButton = DirectButton(parent=SGB.rootTitle,image='IDE_SGBoverScene-off.png', relief=None,
   scale=.025,# pos=SGB.expandAllDB.getPos()+(SGB.expandAllDB.getPos()-SGB.collapseAllDB.getPos())*1.25,
   command=SGB_setOverScene, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.overSceneButton.alignTo(SGB.expandAllDB, DGG.CL, DGG.CR, gap=(.4,0))
SGB.overSceneButton.setTransparency(1)
SGB.overSceneTT = createTooltip('Active over scene',align=TextProperties.ALeft, alpha=0)
SGB.overSceneTT.reparentTo(SGB.overSceneButton.stateNodePath[2])
SGB.overSceneTT.setSz(SGB.refreshSGTT.getSz())
SGB.overSceneTT.setSx(SGB.overSceneTT.getSz())
SGB.overSceneTT.setPos(SGB.overSceneTT,.7,0,1.5)
SGB.overSceneTT.copyTo(SGB.overSceneButton.stateNodePath[1])

SGB.useBSphereButton = DirectButton(parent=SGB.rootTitle,
   image='IDE_bsphere-%s.png'%('off' if SGB_useBBox else 'on'), relief=None,
   scale=.025,# pos=(SGB.rootTitle.node().getFrame()[1]-1.5*SGB.refreshSGBbutton.getSx(),0,SGB.refreshSGBbutton.getZ()),
   command=SGB_useBSphereHilight, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.useBSphereButton.alignTo(SGB.rootTitle, DGG.CR, gap=(.15,)*2)
SGB.useBSphereButton.setTransparency(1)
SGB.useBSphereButton.setColor(0,1,0,1)
SGB.useBSphereTT = createTooltip('Use sphere hilighter',align=TextProperties.ARight, alpha=0)
SGB.useBSphereTT.reparentTo(SGB.useBSphereButton.stateNodePath[2])
SGB.useBSphereTT.setSz(SGB.refreshSGTT.getSz())
SGB.useBSphereTT.setSx(SGB.useBSphereTT.getSz())
SGB.useBSphereTT.setZ(SGB.useBSphereTT,1.5)
SGB.useBSphereTT.copyTo(SGB.useBSphereButton.stateNodePath[1])
SGB.useBBoxButton = DirectButton(parent=SGB.rootTitle,
   image='IDE_bbox-%s.png'%('on' if SGB_useBBox else 'off'), relief=None,
   scale=.025,# pos=SGB.useBSphereButton.getPos()-Point3(2.25*SGB.useBSphereButton['scale'],0,0),
   command=SGB_useBBoxHilight, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.useBBoxButton.alignTo(SGB.useBSphereButton, DGG.CR, DGG.CL)
SGB.useBBoxButton.setTransparency(1)
SGB.useBBoxButton.setColor(0,1,0,1)
SGB.useBBoxTT=createTooltip('Use box hilighter',align=TextProperties.ARight, alpha=0)
SGB.useBBoxTT.reparentTo(SGB.useBBoxButton.stateNodePath[2])
SGB.useBBoxTT.setSz(SGB.refreshSGTT.getSz())
SGB.useBBoxTT.setSx(SGB.useBBoxTT.getSz())
SGB.useBBoxTT.setZ(SGB.useBBoxTT,1.5)
SGB.useBBoxTT.copyTo(SGB.useBBoxButton.stateNodePath[1])
SGB.hideBoundsButton = DirectButton(parent=SGB.rootTitle,image='IDE_noBounds.png', relief=None,
   scale=.025,# pos=SGB.useBBoxButton.getPos()-Point3(2.25*SGB.useBSphereButton['scale'],0,0),
   command=SGB_useNoBoundsHilight, clickSound=0, rolloverSound=0, pressEffect=0)
SGB.hideBoundsButton.alignTo(SGB.useBBoxButton, DGG.CR, DGG.CL)
SGB.hideBoundsButton.setTransparency(1)
SGB.hideBoundsButton.setColor(0,1,0,1)
SGB.hideBoundsTT=createTooltip('Remove hilight',align=TextProperties.ARight, alpha=0)
SGB.hideBoundsTT.reparentTo(SGB.hideBoundsButton.stateNodePath[2])
SGB.hideBoundsTT.setSz(SGB.refreshSGTT.getSz())
SGB.hideBoundsTT.setSx(SGB.hideBoundsTT.getSz())
SGB.hideBoundsTT.setZ(SGB.hideBoundsTT,1.5)
SGB.hideBoundsTT.copyTo(SGB.hideBoundsButton.stateNodePath[1])

if IDE_CFG[CFG_SGBPos] is None:
   IDE_CFG[CFG_SGBPos] = (SGBframe.getX(render2dp),0,SGBframe.getZ(render2dp))
else:
   SGBframe.setPos(render2dp, *IDE_CFG[CFG_SGBPos])
if IDE_CFG[CFG_NPropsPos] is None:
   IDE_CFG[CFG_NPropsPos] = (SGBfs[1]+NProps.fieldHeight*.2, 0, -NProps.fieldHeight*.5)
   NProps.frame.setPos(SGBframe, *IDE_CFG[CFG_NPropsPos])
   NProps.frame.wrtReparentTo(SGBframe)
else:
   NProps.frame.reparentTo(SGBframe)
   NProps.frame.setPos(SGBframe, *IDE_CFG[CFG_NPropsPos])
NProps_wrapAroundSGB()
SGB.hide()

################################################################################
IDE_frame.bind(DGG.B1PRESS,IDE_canvas_LMBdown)
IDE_frame.bind(DGG.B3PRESS,IDE_canvas_RMBdown)

# EVENTS
IDE_EVT_fileSaved='file has been saved'

IDE_DO = DirectObject()

MODE_noInput = 'IDE-noInput'
MODE_jump2scene = 'IDE-jump2scene'
MODE_active = 'IDE-active'
MODE_completing = 'IDE-completing'
MODE_noFile = 'IDE-noFile'
MODE_pickFiles = 'IDE-pickFiles'
MODE_chooseRecentFiles = 'IDE-chooseRecentFiles'
MODE_chooseCWD = 'IDE-chooseCWD'
MODE_repeatChars = 'IDE-repeatChars'
MODE_confirmMacroPaste = 'IDE-confirmMacroPaste'
MODE_nameNewMacro = 'IDE-nameNewMacro'
MODE_openMacroManager = 'IDE-openMacroManager'
MODE_saveFileAs = 'IDE-saveFileAs'
MODE_exiting = 'IDE-exiting'
MODE_errorOccurs = 'IDE-errorOccurs'
MODE_slidingDocsTabs = 'IDE-slidingDocsTabs'
MODE_selecting = 'IDE-selecting'
MODE_replacing = 'IDE-replacing'
MODE_forcingRender = 'IDE-forcingRender'
MODE_offerReload = 'IDE-offerReload'
MODE_chooseResolution = 'IDE-chooseResolution'
MODE_ALL = (
    MODE_active, MODE_completing, MODE_chooseResolution,
    MODE_noFile, MODE_pickFiles, MODE_saveFileAs,
#     MODE_jump2scene  <---- don't add this mode
#     MODE_chooseRecentFiles, MODE_chooseCWD,
#     MODE_repeatChars, MODE_confirmMacroPaste,
#     MODE_nameNewMacro, MODE_openMacroManager,
    MODE_starting, MODE_exiting,
    MODE_errorOccurs, MODE_slidingDocsTabs,
    MODE_selecting, MODE_replacing, MODE_forcingRender
    )
MODE_activeOrCompleting = (MODE_active,MODE_completing)
MODE_preferenceAvail = (MODE_noFile,MODE_active,MODE_completing,MODE_chooseResolution)

#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
# IDE_MODES=[MODE_pickFiles]#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
# IDE_acceptKeys('escape',IDE_FileDialog.cancel)


actsInModes = {
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
MODE_preferenceAvail: {
  'Preferences':[ [['shift-%s-p'%Ctrl], IDEPreferences.openPreferences,[],False], AC_gen, 'Preferences', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_chooseResolution,): {
  'toggleFullscreenRESapply':[ [['enter'], IDE_applyResolution,[],False], AC_gen, 'Apply selected display resolution (if going fullscreen fails)', ],
  'toggleFullscreenREScancel':[ [['escape'], IDE_cancelResolutionChange,[],False], AC_gen, 'Cancel display resolution change (if going fullscreen fails)', ],
  'toggleFullscreenRESnext':[ [['arrow_down'], IDE_resolutionsList.highlightNextItem,[],True], AC_gen, 'Select next display resolution (if going fullscreen fails)', ],
  'toggleFullscreenRESprev':[ [['arrow_up'], IDE_resolutionsList.highlightPrevItem,[],True], AC_gen, 'Select previous display resolution (if going fullscreen fails)', ],
  'toggleFullscreenRESjumpToFirst':[ [['home'], IDE_resolutionsList.highlightFirstItem,[],False], AC_gen, 'Goto first display resolution (if going fullscreen fails)', ],
  'toggleFullscreenRESjumpToLast':[ [['end'], IDE_resolutionsList.highlightLastItem,[],False], AC_gen, 'Goto last display resolution (if going fullscreen fails)', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_jump2scene,): {
  'toggleLogOverScene':[ [['f9'], IDE_toggleLogOverScene,[],False], AC_scene, 'Toggle log over scene', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_active,MODE_completing,MODE_noFile,MODE_jump2scene): {
  'toggleIDEorScene':[ [['f5'], IDE_toggleIDEorScene,[],False], AC_scene, 'Toggle IDE / scene', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_active,MODE_noFile): {
  'Shutdown':[ [['escape'], IDE_exit,[],False], AC_gen, 'Shutdown IDE', ],
  'docSwitchLog':[ [[Ctrl+'-l'], IDE_openLog,[],False], AC_doc, 'Open / switch to log', ],
  'PstatsEnable':[ [['alt-p'], IDE_enablePStats,[],False], AC_gen, 'Enable PStats', ],
  'toggleSGB':[ [['shift-%s-s'%Ctrl], IDE_toggleSGBAndNProps,[],False], AC_scene, 'Toggle SceneGraphBrowser', ],
  'docBorn':[ [[Ctrl+'-n'], IDE_newDoc,[],False], AC_doc, 'Create new document', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_active,MODE_completing,MODE_noFile): {
  'pause':[ [['pause'], IDE_toggleSceneActive,[],False], AC_scene, 'Pause / resume scene', ],
  'clearPools':[ [['alt-f12'], IDE_clearPools,[],False], AC_scene, 'Clear model and texture pools', ],
  'openFiles':[ [[Ctrl+'-o'], IDE_pickFiles,['open'],False], AC_doc, 'Open files', ],
  'openFilesRecent':[ [[Ctrl+'-r'], IDE_openRecentFilesInterface,[],False], AC_doc, 'Open recent files', ],
  'cleanupScene':[ [['alt-c'], IDE_cleanupScene,[True],False], AC_scene, 'Cleanup scene', ],
  'toggleBufferViewer':[ [[Ctrl+'-b'], base.bufferViewer.toggleEnable,[],False], AC_scene, 'Toggle buffer viewer', ],
  'toggleResetCam':[ [['alt-t'], IDE_toggleResetCameraTransform,[],False], AC_scene, 'Toggle reset camera transform on update', ],
  'toggleFullscreen':[ [['alt-f11'], IDE_toggleFullscreen,[],False], AC_gen, 'Toggle fullscreen', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_completing,): {
  'CCgotoPrev':[ [['arrow_up'], IDE_CC_gotoPrev,[],True], AC_comp, 'Select previous item', ],
  'CCgotoNext':[ [['arrow_down'], IDE_CC_gotoNext,[],True], AC_comp, 'Select next item', ],
  'CCjumpToFirst':[ [['home'], IDE_CC_gotoFirst,[],False], AC_comp, 'Goto first item', ],
  'CCjumpToLast':[ [['end'], IDE_CC_gotoLast,[],False], AC_comp, 'Goto last item', ],
  'CCscrollCodesUp':[ [['page_up'], IDE_CC_gotoPrev,[20],True], AC_comp, 'Scroll list up', ],
  'CCscrollCodesDown':[ [['page_down'], IDE_CC_gotoNext,[20],True], AC_comp, 'Scroll list down', ],
  'CCscrollDescUp':[ [[Ctrl+'-arrow_up'], IDE_objDesc.scrollCanvas,[-.08],True], AC_comp, 'Scroll description up', ],
  'CCscrollDescDown':[ [[Ctrl+'-arrow_down'], IDE_objDesc.scrollCanvas,[.08],True], AC_comp, 'Scroll description down', ],
  'CDscrollDescToTop':[ [[Ctrl+'-home'], IDE_objDesc.scrollCanvas,[-MAXINT],True], AC_comp, 'Scroll description to top', ],
  'CDscrollDescToEnd':[ [[Ctrl+'-end'], IDE_objDesc.scrollCanvas,[MAXINT],True], AC_comp, 'Scroll description to end', ],
  'COaccept':[ [['enter'], IDE_CC_accept,[],False], AC_comp, 'Accept item', ],
  'COcycleMode':[ [['f2'], IDE_CC_cycleMode,[],False], AC_comp, 'Cycle match modes', ],
  'COdesc':[ [['f1'], IDE_CC_toggleDesc,[],False], AC_comp, 'Show / hide description', ],
  'COout':[ [['escape'], IDE_CC_cancel,[],False], AC_comp, 'Cancel', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_active,MODE_completing): {
  'completionCode':[ [[Ctrl+'-space'], IDE_completion,[False,True,False],False], AC_comp, 'Code completion', ],
  'completionSnippet':[ [['alt-s'], IDE_completion,[None,None,True],False], AC_comp, 'Snippet completion', ],
  'toggleAutoComplete':[ [['f4'], IDE_CC_toggleAutoComplete,[],False], AC_comp, 'Toggle auto-complete', ],
  'delCharNext':[ [['delete'], IDE_delChar,[],True], AC_edit, 'Delete next character', ],
  'delLineTail':[ [['shift-%s-delete'%Ctrl], IDE_delLineTail,[],False], AC_edit, 'Delete to end of line', ],
  'delLineHead':[ [['shift-%s-backspace'%Ctrl], IDE_delLineHead,[],False], AC_edit, 'Delete to start of line', ],
  'delWordTail':[ [[Ctrl+'-delete'], IDE_delWordTail,[],True], AC_edit, 'Delete to word tail', ],
  'delWordHead':[ [[Ctrl+'-backspace'], IDE_delWordHead,[],True], AC_edit, 'Delete to word head', ],
  'gotoCharPrev':[ [['arrow_left'], IDE_gotoPrevColumn,[],True], AC_edit, 'Goto previous character', ],
  'gotoCharNext':[ [['arrow_right'], IDE_gotoNextColumn,[],True], AC_edit, 'Goto next character', ],
  'gotoWordPrev':[ [[Ctrl+'-arrow_left'], IDE_gotoPrevWord,[],True], AC_edit, 'Goto previous word', ],
  'gotoWordNext':[ [[Ctrl+'-arrow_right'], IDE_gotoNextWord,[],True], AC_edit, 'Goto next word', ],
  'historyUndo':[ [[Ctrl+'-z'], IDE_undo,[],True], AC_edit, 'Undo', ],
  'historyRedo':[ [['shift-%s-z'%Ctrl], IDE_redo,[],True], AC_edit, 'Redo', ],
  'toggleInsert':[ [['insert'], IDE_toggleInsert,[],False], AC_edit, 'Toggle insert / overwrite', ],
  'unindentOrDelPrevChar':[ [['backspace'], IDE_backSpcChar,[],True], AC_edit, 'Unindent OR Delete previous character', ],
  'unindentFixed':[ [['shift-backspace'], IDE_backSpcChar,[None,1,1],True], AC_edit, 'Unindent (fixed space)', ],
  'updateScene':[ [['f9'], IDE_saveAllAndUpdate,[],False], AC_scene, 'Update scene', ],
  'updateSceneAutoJump':[ [[Ctrl+'-f9'], IDE_saveAllAndUpdate,[True],False], AC_scene, 'Update + jump to scene', ],
  'updateSceneClearTex':[ [['f10'], IDE_saveAllAndUpdate,[False,True,False],False], AC_scene, 'Update + clear texture pool', ],
  'updateSceneClearTexAutoJump':[ [[Ctrl+'-f10'], IDE_saveAllAndUpdate,[True,True,False],False], AC_scene, 'Update + clear texture pool + jump to scene', ],
  'updateSceneClearModel':[ [['f11'], IDE_saveAllAndUpdate,[False,False,True],False], AC_scene, 'Update + clear model pool', ],
  'updateSceneClearModelAutoJump':[ [[Ctrl+'-f11'], IDE_saveAllAndUpdate,[True,False,True],False], AC_scene, 'Update + clear model pool + jump to scene', ],
  'updateSceneClearTexModel':[ [['f12'], IDE_saveAllAndUpdate,[False,True,True],False], AC_scene, 'Update + clear model and texture pool', ],
  'updateSceneClearTexModelAutoJump':[ [[Ctrl+'-f12'], IDE_saveAllAndUpdate,[True,True,True],False], AC_scene, 'Update + clear model and texture pool + jump to scene', ],
  },
#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
(MODE_active,): {
  'WSopacityUp':[ [[], IDE_adjustWSopacity,[2],True], AC_gen, 'Increase workspace opacity', ],
  'WSopacityDn':[ [[], IDE_adjustWSopacity,[-2],True], AC_gen, 'Decrease workspace opacity', ],
  'CTcreate':[ [[], IDE_createCallTips,[],False], AC_edit, 'Show call tips', ],
  'CTinsert':[ [[], IDE_insertCallArgs,[],False], AC_edit, 'Insert call arguments-set', ],
  'bookmarkClearAll':[ [['alt-arrow_right'], IDE_clearAllLineMarks,[],False], AC_mark, 'Clear all bookmarks', ],
  'bookmarkGotoPrev':[ [['alt-arrow_up'], IDE_gotoPrevMarkedLine,[],True], AC_mark, 'Goto previous mark', ],
  'bookmarkGotoNext':[ [['alt-arrow_down'], IDE_gotoNextMarkedLine,[],True], AC_mark, 'Goto next mark', ],
  'bookmarkToggle':[ [['alt-arrow_left'], IDE_toggleMarkLine,[],False], AC_mark, 'Toggle bookmark', ],
  'breakLine':[ [['enter'], IDE_breakLine,[],True], AC_edit, 'Break line', ],
  'delLine':[ [[Ctrl+'-y','shift-delete',], IDE_delLine,[],True], AC_edit, 'Delete line', ],
  'indent':[ [['tab'], IDE_indentLine,[],True], AC_edit, 'Indent', ],
  'indentFixed':[ [['shift-tab'], IDE_indentLine,[-1],True], AC_edit, 'Indent (fixed space)', ],
  'case1Lower':[ [[Ctrl+'-,'], IDE_changeCase,[-1],True], AC_edit, 'To lower case', ],
  'case2Upper':[ [[Ctrl+'-.'], IDE_changeCase,[1],True], AC_edit, 'To UPPER CASE', ],
  'caseSwap':[ [[Ctrl+'-/'], IDE_changeCase,[0],True], AC_edit, 'Swap case', ],
  'clipCopy':[ [[Ctrl+'-c'], IDE_copy,[],False], AC_edit, 'Copy', ],
  'clipCut':[ [[Ctrl+'-x'], IDE_cut,[],False], AC_edit, 'Cut', ],
  'clipPaste':[ [[Ctrl+'-v'], IDE_paste,[],True], AC_edit, 'Paste', ],
  'clipPasteSticky':[ [['shift-%s-v'%Ctrl], IDE_paste,[None,True,True],True], AC_edit, 'Paste without moving caret', ],
  'docClose':[ [[Ctrl+'-w'], IDE_closeDoc,[],False], AC_doc, 'Close document', ],
  'docSave':[ [[Ctrl+'-s'], IDE_saveCurrFile,[],False], AC_doc, 'Save document', ],
  'docSaveAs':[ [[Ctrl+'-d'], IDE_pickFiles,['saveas'],False], AC_doc, 'Save document as...', ],
  'docSaveDupAs':[ [['alt-d'], IDE_saveDocDuplicateAs,[],False], AC_doc, 'Save document copy as...', ],
  'docSwitchNext':[ [[Ctrl+'-tab',], IDE_cycleDoc,[1],True], AC_doc, 'Goto next document', ],
  'docSwitchPrev':[ [['shift-%s-tab'%Ctrl], IDE_cycleDoc,[-1],True], AC_doc, 'Goto previous document', ],
  'docSwitchMain':[ [[Ctrl+'-m'], IDE_switchToMainFile,[],False], AC_doc, 'Goto main module', ],
  'docSetAsMain':[ [[Ctrl+'-enter'], IDE_openSetMainFileInterface,[],False], AC_doc, 'Set as main module', ],
  'docSetAsMainCWD':[ [['shift-%s-enter'%Ctrl], IDE_openSetMainFileInterface,[None,True],False], AC_doc, 'Set as main module + options', ],
  'gotoDocBeg':[ [[Ctrl+'-home'], IDE_gotoDocBeg,[],False], AC_edit, 'Goto document start', ],
  'gotoDocEnd':[ [[Ctrl+'-end'], IDE_gotoDocEnd,[],False], AC_edit, 'Goto document end', ],
  'gotoDocBegNselect':[ [['shift-%s-home'%Ctrl], IDE_gotoDocBeg,[1],False], AC_edit, 'Select to document start', ],
  'gotoDocEndNselect':[ [['shift-%s-end'%Ctrl], IDE_gotoDocEnd,[1],False], AC_edit, 'Select to document end', ],
  'gotoPageUp':[ [['page_up'], IDE_gotoPrevLine,[20],True], AC_edit, 'Page up', ],
  'gotoPageDown':[ [['page_down'], IDE_gotoNextLine,[20],True], AC_edit, 'Page down', ],
  'gotoPageUpNselect':[ [['shift-page_up'], IDE_gotoPrevLine,[20,1],True], AC_edit, 'Page up and select', ],
  'gotoPageDownNselect':[ [['shift-page_down'], IDE_gotoNextLine,[20,1],True], AC_edit, 'Page down and select', ],
  'gotoVisLineFirst':[ [[Ctrl+'-page_up'], IDE_gotoPageBeg,[],False], AC_edit, 'Goto first line in view', ],
  'gotoVisLineLast':[ [[Ctrl+'-page_down'], IDE_gotoPageEnd,[],False], AC_edit, 'Goto last line in view', ],
  'gotoVisLineFirstNselect':[ [['shift-%s-page_up'%Ctrl], IDE_gotoPageBeg,[1],False], AC_edit, 'Select to first line in view', ],
  'gotoVisLineLastNselect':[ [['shift-%s-page_down'%Ctrl], IDE_gotoPageEnd,[1],False], AC_edit, 'Select to last line in view', ],
  'gotoWordNextNselect':[ [['shift-%s-arrow_right'%Ctrl], IDE_gotoNextWord,[1],True], AC_edit, 'Select to next word', ],
  'gotoWordPrevNselect':[ [['shift-%s-arrow_left'%Ctrl], IDE_gotoPrevWord,[1],True], AC_edit, 'Select to previous word', ],
  'gotoHLineStart':[ [['home'], IDE_gotoFront,[],False], AC_edit, 'Goto line start', ],
  'gotoHLineEnd':[ [['end'], IDE_gotoBack,[],False], AC_edit, 'Goto line end', ],
  'gotoHLineStartNselect':[ [['shift-home'], IDE_gotoFront,[1],False], AC_edit, 'Select to line start', ],
  'gotoHLineEndNselect':[ [['shift-end'], IDE_gotoBack,[1],False], AC_edit, 'Select to line end', ],
  'gotoLinePrev':[ [['arrow_up'], IDE_gotoPrevLine,[],True], AC_edit, 'Goto previous line', ],
  'gotoLineNext':[ [['arrow_down'], IDE_gotoNextLine,[],True], AC_edit, 'Goto next line', ],
  'gotoLinePrevNselect':[ [['shift-arrow_up'], IDE_gotoPrevLine,[1,1],True], AC_edit, 'Select to previous line', ],
  'gotoLineNextNselect':[ [['shift-arrow_down'], IDE_gotoNextLine,[1,1],True], AC_edit, 'Select to next line', ],
  'gotoCharPrevNselect':[ [['shift-arrow_left'], IDE_gotoPrevColumn,[1,1],True], AC_edit, 'Select to previous character', ],
  'gotoCharNextNselect':[ [['shift-arrow_right'], IDE_gotoNextColumn,[1,1],True], AC_edit, 'Select to next character', ],
  'insertRepetitiveChars':[ [[Ctrl+'-i'], IDE_repeatChars,[],False], AC_edit, 'Insert repetitive characters', ],
  'joinLines':[ [[Ctrl+'-j'], IDE_joinLines,[],False], AC_edit, 'Join lines', ],
  'linesMoveUp':[ [[Ctrl+'-alt-arrow_up'], IDE_moveLines,[-1],True], AC_edit, 'Move lines up', ],
  'linesMoveDown':[ [[Ctrl+'-alt-arrow_down'], IDE_moveLines,[1],True], AC_edit, 'Move lines down', ],
  'linesDupUp':[ [[Ctrl+'-alt-page_up'], IDE_duplicateLine,[-1],True], AC_edit, 'Duplicate line upward', ],
  'linesDupDown':[ [[Ctrl+'-alt-page_down'], IDE_duplicateLine,[1],True], AC_edit, 'Duplicate line downward', ],
  'searchFind':[ [[Ctrl+'-f'], IDE_findOrReplace,[False],False], AC_search, 'Find', ],
  'searchReplace':[ [[Ctrl+'-h'], IDE_findOrReplace,[True],False], AC_search, 'Replace', ],
  'searchFindNext':[ [['f3'], IDE_doFind,[1],True], AC_search, 'Find next occurence', ],
  'searchFindPrev':[ [[Ctrl+'-f3'], IDE_doFind,[0],True], AC_search, 'Find previous occurence', ],
  'pickColor01':[ [['shift-%s-c'%Ctrl], IDE_chooseColor,[0],False], AC_edit, 'Pick color (0..1)', ],
  'pickColor0255':[ [['%s-alt-c'%Ctrl], IDE_chooseColor,[1],False], AC_edit, 'Pick color (0..255)', ],
  'pickColor025501':[ [['shift-%s-alt-c'%Ctrl], IDE_chooseColor,[2],False], AC_edit, 'Pick color (0..1 | 0..255)', ],
  'selectAll':[ [[Ctrl+'-a'], IDE_selectAll,[],False], AC_edit, 'Select all', ],
  'selectAdjExpand':[ [[Ctrl+'-+',Ctrl+'-='], IDE_adjustSelection,[1],True], AC_edit, 'Expand selection', ],
  'selectAdjShrink':[ [[Ctrl+'--'], IDE_adjustSelection,[-1],True], AC_edit, 'Shrink selection', ],
  'selectInBrkBeg':[ [[Ctrl+'-['], IDE_selectInsideBrackets,[False],False], AC_edit, 'Select in brackets (caret at start)', ],
  'selectInBrkEnd':[ [[Ctrl+'-]'], IDE_selectInsideBrackets,[True],False], AC_edit, 'Select in brackets (caret at end)', ],
  'scrollViewUp':[ [['wheel_up'], IDE_scrollView,[-1,False],False], AC_edit, 'Scroll view up', ],
  'scrollViewDown':[ [['wheel_down'], IDE_scrollView,[1,False],False], AC_edit, 'Scroll view down', ],
  'scrollLineUp':[ [[Ctrl+'-arrow_up'], IDE_scrollView,[-1],True], AC_edit, 'Scroll line up (scroll + keep caret in view)', ],
  'scrollLineDown':[ [[Ctrl+'-arrow_down'], IDE_scrollView,[1],True], AC_edit, 'Scroll line down (scroll + keep caret in view)', ],
  'toggleComment':[ [[Ctrl+'-\\'], IDE_toggleComment,[],False], AC_edit, 'Toggle comment', ],
  'macroMgr':[ [['f7'], IDE_openMacroManager,[],False], AC_macro, 'Macro Manager', ],
  'macroPlay':[ [['f8'], IDE_playMacro,[],True], AC_macro, 'Play default / latest macro', ],
  'macroRecord':[ [['%s-f7'%Ctrl], IDE_recordMacro,[],False], AC_macro, 'Start / stop macro recording', ],
  'snippetMgr':[ [['f6'], IDESnipMgr.openSnippetsManager,[],False], AC_comp, 'Snippets Manager', ],
  'snippetSave':[ [[Ctrl+'-f6'], IDE_saveToSnippets,[],False], AC_comp, 'Save to snippets', ],
  },
}
# IDE_acceptKeys(Ctrl+'-`',IDE_cycleTabSkin,[1])
# IDE_acceptKeys('shift-%s-`'%Ctrl,IDE_cycleTabSkin,[-1])
# IDE_acceptKeys(Ctrl+'-*',IDE_cycleSliderSkin,[1])
# IDE_acceptKeys('shift-%s-*'%Ctrl,IDE_cycleSliderSkin,[-1])


IDE_DEF_KEYMAP = {} # default keymap
IDE_KEYMAP = {} # actual keymap
IDE_ACT_DESC = {} # actions descriptions
ACTS_IN_MODES = {}
MODES_OF_ACT = {}
CAT_OF_ACT = {} # category of action
for modes,acts in list(actsInModes.items()):
    for act,storage in list(acts.items()):
#         setattr(M,'ACT_'+act,act)
        KMcomNargs, CAT_OF_ACT[act], IDE_ACT_DESC[act] = storage
        IDE_DEF_KEYMAP[act] = IDE_KEYMAP[act] = KMcomNargs[0]
        for m in modes:
            if m not in ACTS_IN_MODES:
               ACTS_IN_MODES[m]=[]
            ACTS_IN_MODES[m].append(act)
        MODES_OF_ACT[act]=modes

def IDE_applyKeys(newKM,forced=False):
    global IDE_MODES, IDE_KEYMAP
    if IDE_KEYMAP==newKM and not forced: # no changes
       return
    IDE_DO.ignoreAll()
    # no-prefix events
    IDE_DO.accept('IDE_buttonDown',IDE_analyzeButtonDown)
    IDE_DO.accept('IDE_btnStroke',IDE_analyzeButtonStroke)
    IDE_DO.accept('window-event',IDE_handleWindowEvent)
    IDE_DO.accept(closeWindowEventName,IDE_handleCloseWindowEvent)
    IDE_MODES = MODE_ALL#v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v^v
    IDE_acceptKeys(Ctrl,IDE_setControlDown)
    IDE_acceptKeys(Ctrl+'-up',IDE_setControlUp)
    IDE_KEYMAP = newKM
    for modes,acts in list(actsInModes.items()):
        IDE_MODES=modes
        for act,storage in list(acts.items()):
            IDE_acceptKeyMap(*([IDE_KEYMAP[act]] + storage[0][1:]))
    if not forced:
       dumpToFile(IDE_KEYMAP,IDE_keymapPath)
       text='New keymap applied'
       msg=createMsg(text,bg=(0,1,0,.85))
       putMsg(msg,'keymap applied',2,stat=True)

# loads keymap
if os.path.exists(IDE_keymapPath):
   savedKM=loadFromFile(IDE_keymapPath)
   newActs=[]
   # overrides the default keymap
   for act in IDE_KEYMAP:
       if act in savedKM:
          IDE_KEYMAP[act]=savedKM[act]
       else: # new action
          newActs.append(act)
   if newActs:
      IDEPreferences.KEYMAP_COPY = deepcopy(IDE_KEYMAP)
      print('\n=== NEW ACTION(s) ===')
      for act in newActs:
          print('  ',IDE_ACT_DESC[act],IDE_KEYMAP[act])
          for e in IDE_KEYMAP[act]:
              # used by some actions (plus itself)
              if len(IDEPreferences.getKeyUsers(e,act))>1:
                 IDE_KEYMAP[act].remove(e)
                 print('"%s" is used by other action(s), disabled'%e)
      print('='*21)
      del IDEPreferences.KEYMAP_COPY
   del savedKM
# saves after load, to save any new actions
dumpToFile(IDE_KEYMAP,IDE_keymapPath)
# accepts events
IDE_applyKeys(IDE_KEYMAP,forced=True)

################################################################################
class IDE_document:
  def __init__(self,fullpath,progressRange=1,reset=1):
      global IDE_newDocIdx
      self.blockParent=IDE_canvas.attachNewNode('block_display_%s'%id(self))
      self.blockParent.setScale(IDE_textScale)
      self.textParent=IDE_canvas.attachNewNode('text_display_%s'%id(self),sort=10)
      self.textParent.setTexture(IDE_normal_chars_tex)
      self.textParent.setScale(IDE_textScale)
      self.callTipParent=IDE_canvas.attachNewNode('callTip_display_%s'%id(self),sort=20)
      self.callTipParent.setScale(IDE_textScale)
      self.callTipParent.hide()
      self.callTipBG=DirectFrame(state=DGG.NORMAL,frameColor=(1,1,1,1),
        relief=DGG.GROOVE, suppressMouse=0, enableEdit=0)
      self.callTipBG.reparentTo(self.callTipParent)
      self.callTipBG.setTransparency(TransparencyAttrib.MAlpha)
      self.callTipBG.setColorScale(IDE_COLOR_callTipsBG)
      self.callTipBG.bind(DGG.B1PRESS,self.callTipLMBdown)
      self.callTipBG.bind(DGG.B3PRESS,self.callTipRMBdown)
      self.callTipInsertIdx=0
      self.lineMarkParent=IDE_frame.attachNewNode('bookMark_display_%s'%id(self))
      self.lineMarkParent.setScale(IDE_textScale)
      self.helperLine=IDE_REALhelperLine.copyTo(self.textParent,-100)
      self.helperLine.hide()
      self.FullPath=fullpath
      self.insertCursor=1
      self.isChanged=0
      self.isObsolete=False
      self.isSelecting=False
      self.blockStartLine=0
      self.blockStartCol=0
      self.line=0
      self.column=0
      self.lastMaxColumn=0
      self.canvasXpos=0
      self.canvasZpos=0
      self.preferedCWD='.'
      self.preferedArgs=[]
      self.readonly=0
      self.groupHistoryOn=False
      self.historyIdx=self.historyIdxOnSave=-1
      self.changedSinceSaved=False
      self.history=[]
      self.recordMacro=False
      self.macro=[]
      self.macro_idx=0
      self.macro_undoIdx={}
      self.macro_redoIdx={}
      self.markedLines=[]
      self.markedColumns={}
      self.errors=[]
      self.errHLivals=[]
      self.numErrors=0
      self.displayed={}
      self.valid=True
      if fullpath is not None:
         if fullpath==IDE_LOG_NAME:
            self.FileName=fullpath
            self.FullPath=None
            self.numLines=0
            self.readonly=1
            self.hilight=IDE_HL_None
         else:
            self.DirName=os.path.dirname(self.FullPath)
            self.FileName=os.path.basename(self.FullPath)
            self.File=[]
            self.Display=[]
            self.quoted=[]
            self.numLines=0
            self.loadFile(progressRange,reset)
      else:
         IDE_newDocIdx+=1
         self.FileName='New-%s.py'%IDE_newDocIdx
         self.File=['']
         self.Display=[]
         self.quoted=[0]
         self.numLines=1
         self.hilight=IDE_HL_Python
         self.createTab()

  def loadFile(self,progressRange=1,reset=1,fullLog=1):
      global adjustCanvasLength
      fileExt=os.path.splitext(self.FileName)[1][1:].lower()
      if fileExt in ('py','pyw','pyx'):
         self.hilight=IDE_HL_Python
      else:
         self.hilight=IDE_HL_None
      self.setInactive()
      if reset:
         IDE_gauge.reset()
      #~ print>>IDE_DEV, '\nLOADING '+self.FileName,
      if self.FullPath is None and self.FileName==IDE_LOG_NAME:
         if fullLog:
            sL=LOG.log.splitlines(True)
            for i in range(len(sL)):
                filled=LOG_TW.fill(sL[i]).replace('\n','\n   ')
                sL[i]=filled+('\n' if sL[i] and sL[i][-1]=='\n' else '')
            logStr=''.join(sL)
         else:
            logStr='<THIS IS LOG SINCE %.2f SECONDS AFTER THE IDE STARTED>\n\n'%globalClock.getRealTime()
         self.File=[ l.expandtabs() for l in logStr.splitlines(1) ] # I HATE TABs
         self.numLines=len(self.File)
         self.textParent.setColorScale(IDE_COLOR_log,priority=-10)
      else:
         self.File=[]
         f=open(self.FullPath,'rU')
         null='\x00'
         l=' '
         while l:
               l=f.readline()
               if l.find(null)>-1:
                  self.valid=False
                  self.File=['']
                  break
               self.File.append(l.expandtabs()) # I HATE TABs
         f.close()
         self.numLines=len(self.File)
         if self.File[-1].endswith('\n'):
            self.numLines+=1
            self.File.append('')
         if self.FullPath in IDE_filesProps:
            size = os.path.getsize(self.FullPath),
            modTime = os.stat(self.FullPath)[stat.ST_MTIME]
            line, column, markedLines,canvasXpos, canvasZpos,\
               preferedCWD, preferedArgs = IDE_filesProps[self.FullPath][2:]
            IDE_filesProps[self.FullPath][1]=modTime
            self.line=min(line,self.numLines-1)
            self.canvasXpos=canvasXpos
            self.canvasZpos=canvasZpos*IDE_lineScale[2]
            self.preferedCWD=preferedCWD
            self.preferedArgs=preferedArgs
            self.lastMaxColumn=self.column=min(column,len(self.File[self.line].rstrip('\n')))
            if markedLines:
               # the old [line,...] format
               if type(markedLines[0])==int:
                  # strips off non-existing marks
                  self.markedLines=[l for l in markedLines if l<self.numLines]
                  for m in self.markedLines:
                      self.markedColumns[m]=0
               # the new [(line,column),...] format
               else:
                  self.markedLines=[ml for ml,mc in markedLines if ml<self.numLines]
                  self.markedColumns=dict(markedLines)
                  for m in [m for m in list(self.markedColumns.keys()) if m not in self.markedLines]:
                      del self.markedColumns[m]
               self.markedLines.sort()
            for m in self.markedLines:
                mark=IDE_lineMark.instanceUnderNode(self.lineMarkParent,str(m))
                mark.setZ(-m*IDE_lineheight)
      #~ print>>IDE_DEV, '<done>'

      lastProgress=0
      gaugeStart=IDE_gauge.get()
      step=IDE_safeStep if run == IDE_safeRun else renderFrame
      if self.hilight:  # highlighted
         self.collectQuotedLines(gaugeStart,progressRange,step)
      elif progressRange:
         r=.05
         for i in range(int(progressRange/r)):
             IDE_gauge.set(gaugeStart+i*r)
             step()
      if lastProgress<1:
         IDE_gauge.set(.5*(IDE_gauge.get()+gaugeStart+progressRange))
         step()
#       print>>IDE_DEV, self.quoted
      # creates file tab
      self.createTab()

  def updateQuotedLines(self,startLine,isQuoted=None,forced=False,numStatic=1):
      if startLine>=self.numLines:
         return False
      if isQuoted is None:
         if startLine==0:
            isQuoted=False
         else:
            isQuoted=IDE_IDX2QUOTE[self.quoted[startLine-1]]
            isQuoted=self.hilightLine(self.File[startLine-1],None,isQuoted)
      if isQuoted==IDE_IDX2QUOTE[self.quoted[startLine]] and not forced: # nothing changed
         return False
      numNotChanged=0
      for l in range(startLine,self.numLines):
          newQ=IDE_QUOTE2IDX[isQuoted]
          if self.quoted[l]==newQ:
             numNotChanged+=1
          else:
             numNotChanged=0
#           print '>>> numNotChanged:',numNotChanged
          if numNotChanged>numStatic:
             break
          self.quoted[l]=newQ
          isQuoted=self.hilightLine(self.File[l],None,isQuoted)
#       print>>IDE_DEV, '++ upd Quoted( %s )Lines ++'%(l-startLine)
      return True

  def collectQuotedLines(self,gaugeStart=None,progressRange=None,step=None):
      isQuoted=False
      lastProgress=z=0
      self.quoted=[]
      for line in self.File:
          self.quoted.append(IDE_QUOTE2IDX[isQuoted])
          isQuoted=self.hilightLine(line,None,isQuoted)
          if gaugeStart is not None:
             progress=float(z)/self.numLines
             z+=1
             if progressRange and progress-lastProgress>=.05/progressRange:
                lastProgress=progress
                IDE_gauge.set(gaugeStart+progress*progressRange)
                step()

  def createTab(self):
      self.tab=DirectButton( parent=IDE_docsTabsHandle, text=self.FileName,
         text_fg=IDE_COLOR_tabTextInactive,
         relief=DGG.FLAT, pad=(.7,.3), frameColor=(1,1,1,0),
         pos=(0,0,-IDE_tabsHeight*(1-.325)),scale=IDE_tabsHeight*.6,
#          command=self.setDocActive, extraArgs=[0,1],
         rolloverSound=0,clickSound=0,pressEffect=0)
      self.tab.bind(DGG.B3PRESS,self.tabRMBdown)
      self.tab.bind(DGG.B1PRESS,IDE_tabs_LMBdown,[self])
      self.tab.bind(DGG.B2PRESS,IDE_tabs_MMBdown,[self])
      self.tab.bind(DGG.ENTER,self.showLoc)
      self.tab.bind(DGG.EXIT,self.removeLoc)
      self.tab.accept(self.tab.node().getPressEvent(MouseButton.wheelUp()),IDE_shiftDocsTabs,[.07])
      self.tab.accept(self.tab.node().getPressEvent(MouseButton.wheelDown()),IDE_shiftDocsTabs,[-.07])
      self.tabPoly=self.tab.attachNewNode('tabPoly')
      self.tabPoly.setColorScaleOff(1)
      self.createTabGeoms()
      self.tab.setBin('tabBin',0)
      self.tabBlink=Sequence(
         # the red channel in color config is set at least 1 (in 0..255 range),
         # so scale it by 255 to push it to 1
         self.tab.colorScaleInterval(.1,Vec4(255,0,0,1)),
         Wait(.1),
         self.tab.colorScaleInterval(.1,Vec4(1)),
         Wait(.1),
         self.tab.colorScaleInterval(.1,Vec4(1,1,1,0)),
         name=IDE_ivalsName+'tabBlink_%s'%id(self.tab)
         )

  def createTabGeoms(self):
      self.tabLabel=self.tabPoly.attachNewNode('label')
      self.tabBorder=self.tabPoly.attachNewNode('border')
      self.tabBorder.setY(-.5)
      self.tabCornerXoffset=.6
      fr=self.tab.node().getFrame()
#       Sz=fr[3]-fr[2]
      scale=IDE_tabsHeight*1.05
      self.tabPoly.setScale(IDE_2Droot,scale*IDE_scale[0],1,scale*IDE_scale[2])
      self.tabPoly.setY(2)
      self.tabPoly.setZ(IDE_docsTabsHandle,-IDE_tabsHeight-.005)

      self.tabLEdge=IDE_REALtabLcorner.instanceUnderNode(self.tabBorder,'')
      self.tabMid=IDE_REALtabMid.instanceUnderNode(self.tabBorder,'')
      self.tabREdge=IDE_REALtabRcorner.instanceUnderNode(self.tabBorder,'')
      self.tabLlabelEdge=IDE_REALtabLabelL.instanceUnderNode(self.tabLabel,'')
      self.tabLabelMid=IDE_REALtabLabelMid.instanceUnderNode(self.tabLabel,'')
      self.tabRlabelEdge=IDE_REALtabLabelR.instanceUnderNode(self.tabLabel,'')
      self.adjustTabGeoms()

      self.tabBorder.hide()
      if self.FullPath==APP_mainFile:
         self.tabLabel.setColorScale(IDE_COLOR_tabLabelMainModInactive,1)
      else:
         self.tabLabel.hide()

  def adjustTabGeoms(self):
      fr=self.tab.node().getFrame()
      self.tabLEdge.setX(self.tab,fr[0]+self.tabCornerXoffset)
      self.tabMid.setX(self.tabLEdge.getTightBounds()[1][0])
      self.tabMid.setSx(self.tab,fr[1]-fr[0]-self.tabCornerXoffset*2)
      self.tabMid.setTexScale(TextureStage.getDefault(),self.tabMid.getSx(),1)
      self.tabMid.setTexOffset(TextureStage.getDefault(),.5-.5*self.tabMid.getSx(),0)
      self.tabREdge.setX(self.tab,fr[1]-self.tabCornerXoffset)
      self.tabLlabelEdge.setX(self.tab,fr[0]+self.tabCornerXoffset)
      self.tabLabelMid.setX(self.tabLlabelEdge.getTightBounds()[1][0])
      self.tabLabelMid.setSx(self.tab,fr[1]-fr[0]-self.tabCornerXoffset*2)
      self.tabRlabelEdge.setX(self.tab,fr[1]-self.tabCornerXoffset)

  def showLoc(self,mwp):
      if not IDE_isInMode(MODE_active): return
      loc = self.DirName if hasattr(self,'DirName') else 'not yet saved'
      taskMgr.removeTasksMatching(IDE_docLocRemovalTaskName)
      IDE_docLocation.removeChildren()
      locText = createTooltip(loc, alpha=1)
      locText.reparentTo(IDE_docLocation)
      halfX =- locText.getTightBounds()[0][0]*IDE_docLocation.getSx(render2d)
      # first priority of visibility is the end, then the beginning
      x = min(.95-halfX,max(-.95+halfX,mwp.getMouse()[0]))
      locText.setX(render2d,x)

  def removeLoc(self,mwp):
      taskMgr.doMethodLater(.5,IDE_docLocation.removeChildren,
         IDE_docLocRemovalTaskName,extraArgs=[])

  def setActive(self):
      self.blockParent.unstash()
      self.textParent.unstash()
      self.callTipParent.unstash()
      self.lineMarkParent.unstash()
      self.tab['text_fg']=IDE_COLOR_tabTextActive
      bg=IDE_COLOR_tabLabelMainModActive if self.FullPath==APP_mainFile else IDE_COLOR_tabLabelOtherModActive
      self.tabLabel.setColorScale(bg,1)
      self.tabLabel.show()
      self.tabBorder.show()

  def setInactive(self):
      self.blockParent.stash()
      self.textParent.stash()
      self.callTipParent.stash()
      self.lineMarkParent.stash()
      self.canvasXpos=IDE_canvas.getX()
      self.canvasZpos=IDE_canvas.getZ()
      if hasattr(self,'tab'):
         self.tab['text_fg']=IDE_COLOR_tabTextInactive#(.01,0,0,1)
         if self.FullPath==APP_mainFile:
            self.tabLabel.setColorScale(IDE_COLOR_tabLabelMainModInactive,1)
         else:
            self.tabLabel.hide()
         self.tabBorder.hide()

  def setChangedStatus(self,changed,forced=False):
      if changed and self.historyIdxOnSave==self.historyIdx and not self.changedSinceSaved:
         changed=False
      elif changed==self.isChanged and not forced:
         return
      if changed:
         self.tab['text']='<+> %s'%self.FileName
      else:
         self.tab['text']=self.FileName
         self.historyIdxOnSave=self.historyIdx
         self.changedSinceSaved=False
         # it's important to cut the grouping, or it would violate changedSinceSaved
         self.groupHistoryOn=False
      self.tab.resetFrameSize()
      self.adjustTabGeoms()
      if self==IDE_doc:
         self.setActive()
      else:
         self.setInactive()
      self.isChanged=changed
      if UPDATE_DISPLAY:
         IDE_arrangeDocsTabs()

  def revertToSavePoint(self):
      global JUMP_TO_SAVED, UPDATE_DISPLAY
      IDE_setMessage('Reverting to a save point in edit history.....')
      renderFrame(2)
      adjustHistory = IDE_undo if self.historyIdx>self.historyIdxOnSave else IDE_redo
      JUMP_TO_SAVED = True
      UPDATE_DISPLAY = False
      while self.historyIdxOnSave != self.historyIdx:
            adjustHistory(update=False)
      JUMP_TO_SAVED = False
      UPDATE_DISPLAY = True
      populatePage(forced=True)
      IDE_updateBlock()
      IDE_addMessage(' done')

  def saveDuplicateAs(self,fullpath):
      if fullpath and not IDE_doWriteFile(fullpath,self.File):
         # transfers properties to the copy
         IDE_filesProps[fullpath]=[ os.path.getsize(fullpath),
                                    os.stat(fullPath)[stat.ST_MTIME],
                                    self.line,
                                    self.column,
                                    list(self.markedColumns.items()),
                                    self.canvasXpos,
                                    self.canvasZpos/IDE_lineScale[2],
                                    self.preferedCWD,
                                    self.preferedArgs,
                                    ]
         IDE_saveFilesList()
         IDE_setMessage('Duplicated as "%s"'%fullpath)

  def saveFile(self):
      if not self.isChanged and not self.isObsolete:
         print('NO CHANGES TO SAVE', file=IDE_DEV)
         if not IDE_getMode() in (MODE_active,MODE_completing):
            IDE_setMode(IDE_lastMode)
         return
      if not self.FullPath:
         IDE_spawnWxModal(IDE_WxBrowseFiles,(False,self.saveNew,os.path.dirname(APP_mainFile),self))
         return
      if IDE_doWriteFile(self.FullPath,self.File):
         return True # means unable to be saved
      self.setChangedStatus(0)
      self.isObsolete=False
      IDE_setMessage('SAVED : "%s"'%self.FileName)
      IDE_saveFilesList()
      if self.FullPath!=RunningAPP_mainFile:
         name=joinPaths(self.DirName,os.path.splitext(self.FileName)[0])
         for m in list(sys.modules.values()):
             if m and hasattr(m,'__file__'):
                if name==os.path.splitext(m.__file__)[0]:
                   self.rebind()
                   globalClock.setMode(ClockObject.MNormal)
                   print('THIS MODULE IS ALREADY IMPORTED, NOW REBOUND', file=IDE_DEV)
                   break
      messenger.send(IDE_EVT_fileSaved)

  def saveNew(self,fullpath,task=None):
      if not fullpath: # means user refused to save a new file
         if IDE_lastMode in (MODE_active,MODE_completing):
            IDE_setMode(IDE_lastMode)
         else:
            IDE_setMode(IDE_active)
         # this only happen during exiting, when user hasn't saved some new files
         if IDE_DO.isAccepting(IDE_EVT_fileSaved):
            IDE_DO.ignore(IDE_EVT_fileSaved)
         return
      IDE_setMode(IDE_lastMode)
      self.FullPath=fullpath
      self.DirName=os.path.dirname(self.FullPath)
      self.FileName=os.path.basename(self.FullPath)
      if IDE_doWriteFile(self.FullPath,self.File): return
      if self.FullPath in IDE_recentFiles:
         IDE_recentFiles.remove(self.FullPath)
      IDE_recentFiles.insert(0,self.FullPath)
      self.setChangedStatus(0,forced=True)
      self.isObsolete=False
      IDE_saveFilesList()
      messenger.send(IDE_EVT_fileSaved)
      IDE_setMessage('SAVED : "%s"'%IDE_doc.FileName)
      IDE_exposeTab()

  def rebind(self):
      # DON'T REBIND ANY OF IDE MODULES !!!!!!!!!!!!!!!!!!!!
      if hasattr(self,'DirName') and self.DirName==IDE_path:
         return
      exc = myFinder.rebindClass(__builtins__, self.FullPath)
      if exc: # EXCEPTION
         IDE_processException(exc)
         IDE_removeDoLaterTasks()

  def setDocActive(self,arrangeTabs=False,isClicked=False,tempSwitch=False):
      granted = IDE_getMode() in ( MODE_active, MODE_noFile,MODE_completing )
      if not ( granted or
               # when error occurs, and user is using an interface
               not ( granted or isClicked )
             ):
         return
      global IDE_frameWidth,IDE_doc,IDE_insert
      if IDE_doc:
         if not tempSwitch:
            if IDE_isInMode(MODE_selecting):
               IDE_canvas_LMBup(IDE_doc)
            messenger.send(cancelSliderBarDragEvent)
            IDE_doc.hideCallTip()
         IDE_doc.insertCursor=IDE_insert
         if self==IDE_doc:
            if isClicked:
               IDE_exposeTab()
               print('SELF CLICK', file=IDE_DEV)
               return
         else:
            if IDE_isInMode(MODE_completing) and not tempSwitch:
               IDE_CC_cancel()
            IDE_doc.setInactive()
      IDE_doc=self
      self.setActive()
      IDE_textCursor.reparentTo(self.textParent)
      IDE_insert=self.insertCursor
      IDE_updateCurPos()
      IDE_updateMacroNotif()
      IDE_updateErrNotif()
      recordMacro=IDE_doc.recordMacro
      IDE_doc.recordMacro=False
      IDE_canvas.setX(self.canvasXpos)
      IDE_canvas.setZ(self.canvasZpos)
      adjustCanvasLength(self.numLines,forced=1)
      lineMarksAvail=bool(self.markedLines)
      if lineMarksAvail:
         IDE_markersBar.show()
      else:
         IDE_markersBar.hide()
      Xoff=IDE_canvas_leftBgXR2D*lineMarksAvail
      IDE_frameWidth=2.*IDE_winORatio/IDE_scale[0]-IDE_canvasThumbWidth-IDE_canvasThumbBorder-Xoff
      fr=Vec4(IDE_frame.node().getFrame())
      fr.setY(IDE_frameWidth)
      IDE_frame['frameSize']=fr
      IDE_frame.setX(IDE_docsTabsBG,Xoff)
      SliderBG.setX(IDE_frameWidth)
      if tempSwitch:
         IDE_exposeTab()
         return
      else:
         IDE_forceRender()
      if arrangeTabs: IDE_arrangeDocsTabs()
      IDE_exposeTab()
      if IDE_doc==IDE_log or self.errHLivals:
         return
      IDE_toggleInsert(IDE_insert)
      IDE_doc.recordMacro=recordMacro
      IDE_updateCurPos()
      # TEMPORARY IMPORT FOR CODE COMPLETION >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
      self.processImports(0,self.numLines,clear=True)
      if self.isObsolete:
         self.offerReload()

  def processImports(self,startLine,endLine,clear=False):
      if not self.hilight or UNDO or REDO or\
         (hasattr(self,'DirName') and self.DirName==IDE_path):
         return
      lastImpCol=-1
      lineBreak='\\,('
      lineCont=0
      impLines=[]
      impLinesNo=[]
      for l in range(startLine,endLine):
          s=self.File[l].strip()
          sLen=len(s)
          # ignores empty lines
          if not sLen or self.quoted[l]:
             continue
          isImpL=s.find('import ')
          if isImpL>=0 or lineCont:
             isQuoted,color=IDE_doc.getLineQuotedNColor(l)
             charsColor=IDE_doc.hilightLine(s,color,isQuoted)[2]
             if charsColor[isImpL] in COLORIDX_notCode:
                continue
             if lineCont:
                col=lastImpCol
             else:
                col=self.File[l].find(s)
                if lastImpCol==-1:
                   lastImpCol=col
             if col<=lastImpCol:
                if lineCont:
                   if impLines[-1][-1]=='\\':
                      impLines[-1]=impLines[-1][:-1]+s
                   else:
                      impLines[-1]+=s
                else:
                   impLines.append(s)
                   impLinesNo.append(l+1)
             # respects line break
             lineCont=s[-1] in lineBreak
      # to make sure that all imports is relative to the file,
      # adds file path to sys.path temporarily
      pathInserted=0
      if self.FullPath and not self.DirName in sys.path:
         sys.path.insert(0,self.DirName)
         pathInserted=1
      errIvalsCleared=0
      if clear:
         IDE_CC_TEMP.cleanup()
      anyError=False
      for i in impLines:
#           print 'IMPORT:',i
          try:
             IDE_CC_TEMP.doImport(i)
          except Exception:
             anyError=True
             if not errIvalsCleared:
                errIvalsCleared=1
                self.removeErrHLivals()
                # clears all errors notification
                for e in asList(self.blockParent.findAllMatches('**/error')):
                    e.removeNode()
             print(IDE_errShoutout)
             traceback.print_exc()
             IDE_processException(traceback.format_exc(),impLinesNo[impLines.index(i)])
      if clear: print('TEMP_GLOBAL__', len(IDE_CC_TEMP_GLOBAL), file=IDE_DEV)
#       print>>IDE_DEV, IDE_CC_TEMP_GLOBAL.keys()
      # removes the temporary inserted path
      if pathInserted:
         sys.path.remove(self.DirName)
      return anyError

  def removeErrHLivals(self):
      for i in self.errHLivals:
          i.pause()
          i=None
      self.errHLivals=[]

  def blinkTab(self):
      self.tabBlink.loop()

  def stopBlinkTab(self):
      self.tabBlink.finish()
      self.tab.setColorScale(1,1,1,1)

  def tabRMBdown(self,m):
      IDE_removeAnyMenuNcallTip()
      IDE_CC_cancel()
      IDE_hideSGB()
      IDE_cancelResolutionChange()
      isSaved=hasattr(self,'DirName')
      myPopupMenu=PopupMenu(
         parent=IDE_overlayParent,
         onDestroy=IDE_textCursorIval.resume,
         buttonThrower=IDE_BTnode,
         items=(
           ('_Close','IDE_close.png',IDE_closeDoc, self),
           ('_Go to directory',0,self.gotoDir if isSaved else 0),
           0, # separator
           ('Set as m_ain module',0,IDE_openSetMainFileInterface, self),
           ('Set as main module + options',0,IDE_openSetMainFileInterface, self,True),
           0, # separator
           ('Insert file_name','IDE_insert.png',IDE_injectChar, self.FileName,None,False),
           ('Insert _directory','IDE_insert.png',)+((IDE_injectChar, self.DirName,None,False) if isSaved else (0,)),
           ('Insert _fullpath','IDE_insert.png',IDE_injectChar if self.FullPath else 0, self.FullPath,None,False),
           0, # separator
           ('Copy filename','IDE_copy.png',IDE_copy, self.FileName),
           ('Copy directory','IDE_copy.png',)+((IDE_copy,self.DirName) if isSaved else (0,)),
           ('Copy fullpath','IDE_copy.png',IDE_copy if self.FullPath else 0, self.FullPath),
         ),
         #~ font=IDE_FONT_digitalStrip, baselineOffset=-.35,
         #~ scale=IDE_statusBarHeight*.55, itemHeight=1.2,
         font=IDE_FONT_medrano, baselineOffset=-.27,
         scale=IDE_statusBarHeight*.65, itemHeight=1.05,
         leftPad=.2, separatorHeight=.45,
         underscoreThickness=2,
         BGColor=(.3,.3,.2,.9),
         BGBorderColor=(.8,.3,0,1),
         separatorColor=(1,1,1,1),
         frameColorHover=(1,.8,.3,1),
         frameColorPress=(0,1,0,1),
         textColorReady=(1,1,1,1),
         textColorHover=(0,0,0,1),
         textColorPress=(0,0,0,1),
         textColorDisabled=(.45,.45,.45,1),
      )
      myPopupMenu.menu.setBin('gaugeBin',1)
      IDE_textCursorIval.pause()

  def callTipLMBdown(self,m):
      global IDE_lastMode
      mpos=base.mouseWatcherNode.getMouse()
      pos=self.callTipParent.getPos(render2d)
      dragTask=taskMgr.add(self.dragCallTip,dragCallTipTaskName)
      dragTask.offset=mpos-Point2(pos[0],pos[2])
      dragTask._lastPos=Point2(mpos)
      IDE_lastMode=IDE_getMode()
      IDE_setMode(MODE_noInput)
      IDE_DO.acceptOnce(IDE_BTnode.getPrefix()+'mouse1-up',self.stopDragCallTip)

  def dragCallTip(self,t):
      if base.mouseWatcherNode.hasMouse():
         mpos=base.mouseWatcherNode.getMouse()
         if t._lastPos!=mpos:
            p3=Point3(mpos[0],0,mpos[1])
            p3f=IDE_frame.getRelativePoint(render2d,p3)
            f=IDE_frame.node().getFrame()
            if f[0]<p3f[0]<f[1] and f[2]<p3f[2]<f[3]:
               pos=mpos-t.offset
               self.callTipParent.setPos(render2d,pos[0],0,pos[1])
               IDE_updateCallTipAlpha()
               t._lastPos=Point2(mpos)
      return Task.cont

  def stopDragCallTip(self):
      IDE_setMode(IDE_lastMode)
      IDE_updateCallTipAlpha()
      taskMgr.remove(dragCallTipTaskName)

  def hideCallTip(self):
      self.callTipParent.hide()
      taskMgr.remove(dragCallTipTaskName)

  def callTipRMBdown(self,m):
      print('callTipRMBdown')

  def getLineQuotedNColor(self,line=None):
      if self.hilight:
         if line is None:
            line=self.line
         quote=IDE_IDX2QUOTE[self.quoted[line]]
         color=IDE_QUOTE_COLOR[quote]
         return quote,color
      else:
         return False,COLORIDX_identifier

  def hilightLine(self,line,color,isQuoted):
      numChars=len(line)
      colorize=color is not None
      if colorize:
         charsColor=[]
      c=0
      if isQuoted:
         numQuotes=len(isQuoted)
         if isQuoted==IDE_SQUOTE1:
            backSlsQuote=IDE_REptr_backSlsQuote1
         elif isQuoted==IDE_SQUOTE2:
            backSlsQuote=IDE_REptr_backSlsQuote2
         elif isQuoted==IDE_TQUOTE1:
            backSlsQuote=IDE_REptr_backSls3Quote1
         elif isQuoted==IDE_TQUOTE2:
            backSlsQuote=IDE_REptr_backSls3Quote2
         nextQuote=line.find(isQuoted)
         bStop=nextQuote+numQuotes if nextQuote>-1 else numChars
         bE=0
         while 1:
            backSls=backSlsQuote.search(line,bE,bStop)
            bStop=numChars
            if backSls:
               bS,bE=backSls.span()
               numSls=bE-bS-numQuotes
               if numSls%2==0:
                  bE-=numQuotes
                  break
            else:
                  break
         c=line[bE:].find(isQuoted)
         if c>-1:
            c+=bE+numQuotes
            isQuoted=False
         elif numQuotes==1:
            c=numChars
            lSt=line.rstrip()
            bSls=IDE_REptr_allBackSlsAtEnd.search(lSt)
            if bSls:
               bSlsS,bSlsE=bSls.span()
               # single-quoted string continues to next line
               # (ONLY) IF broken by odd count of backslashes
               if (bSlsE-bSlsS)%2==0:
                  isQuoted=False
            else:
               isQuoted=False
         else:
            c=numChars
         if colorize:
            color=COLORIDX_string if numQuotes<=2 else COLORIDX_doc
            charsColor+=[color if IDE_TDExtensionAvail else IDE_TEXT_COLORS[color]]*c
            if not isQuoted:
               color=COLORIDX_identifier
      stringStart=None
      if not isQuoted:
         while c<numChars:
             char=line[c]
             if char.isspace():
                res=IDE_REptr_space.search(line,c)
                start,end=c,res.end()
                stringStart=None
             elif char=='#':
                start,end=c,numChars
                if colorize:
                   color=COLORIDX_comment
                   stringStart=None
             elif char in IDE_QUOTES:
                REptr_allQuotes=IDE_REptr_quotesSequence1 if char=='\'' else IDE_REptr_quotesSequence2
                allQuotes=REptr_allQuotes.search(line,c)
                start,end=allQuotes.span()
                numQuotes=end-start
                if numQuotes==2 or ((numQuotes)%6)==0:
                   isQuoted=False
                else:
                   quotes=char if numQuotes==1 else char*3
                   numQuotes=len(quotes)
                   backSlsQuote=IDE_REptr_backSlsQuote1 if quotes[0]=='\'' else IDE_REptr_backSlsQuote2
                   nextQuote=line[end:].find(quotes)
                   bStop=end+nextQuote+numQuotes if nextQuote>-1 else numChars
                   bE=end
                   while 1:
                      backSls=backSlsQuote.search(line,bE,bStop)
                      bStop=numChars
                      if backSls:
                         bS,bE=backSls.span()
                         numSls=bE-bS-numQuotes
                         if numSls%2==0:
                            bE-=numQuotes
                            break
                      else:
                            break
                   nextQuote=line[bE:].find(quotes)
                   if nextQuote==-1 and numQuotes==1:
                      end=numChars
                      lSt=line.rstrip()
                      bSls=IDE_REptr_allBackSlsAtEnd.search(lSt)
                      if bSls:
                         bSlsS,bSlsE=bSls.span()
                         # single-quoted string continues to next line
                         # (ONLY) if broken by odd count of backslashes
                         if (bSlsE-bSlsS)%2==0:
                            isQuoted=False
                         else:
                            isQuoted=quotes
                      else:
                         isQuoted=False
                   elif nextQuote==-1:
                      end=numChars
                      isQuoted=quotes
                   else:
                      end=bE+nextQuote+len(quotes)
                      isQuoted=False
                if colorize:
                   color=COLORIDX_string if numQuotes<=2 else COLORIDX_doc
                   if stringStart is not None and numQuotes>2:
                      charsColor[stringStart:]=[color if IDE_TDExtensionAvail else IDE_TEXT_COLORS[color]]*(c-stringStart)
                   stringStart=None
             elif char in myPunctuation:
                isNum=False
                res=IDE_REptr_possibleNum.search(line,c)
                # it might be a float
                if res:
                   start,end=res.span()
                   res=IDE_REptr_punctFloat.search(line,c)
                   if res and res.start()==c and res.end()==end:
                      start,end=res.span()
                      color=COLORIDX_float
                      isNum=True
                if not isNum:
                   res=IDE_REptr_punctNoHashQuotes.search(line,c)
                   start,end=res.span()
                   if end-start>1 and end<len(line) and line[end-1]=='.' and '0'<=line[end]<='9':
                      end-=1
                   color=COLORIDX_punct
                stringStart=None
             elif char in myLettersScore:
                res=IDE_REptr_lettersScore.search(line,c)
                if res:
                   start,end=res.span()
                   if colorize:
                      stringStart=None
                      word=line[start:end]
                      wordLen=len(word)
                      if wordLen==2 and c+2<numChars and word.lower()=='ru' and line[c+2] in IDE_QUOTES:
                         stringStart=c
                         color=COLORIDX_string
                      elif wordLen==1 and c+1<numChars and word.lower() in ('r','u') and line[c+1] in IDE_QUOTES:
                         stringStart=c
                         color=COLORIDX_string
                      elif word in IDE_SYNTAX_builtin:
                         color=COLORIDX_builtin
                      elif word in IDE_SYNTAX_keyword:
                         color=COLORIDX_keyword
                      else:
                         color=COLORIDX_identifier
                else:
                   start,end=c,c+1
                   color=COLORIDX_invalid
                   print(line[c:])
             elif '0'<=char<='9':
                res=IDE_REptr_possibleNum.search(line,c)
                if res:
                   start,end=res.span()
                   # it might be a float
                   res=IDE_REptr_float.search(line,c)
                   if res and res.start()==c and res.end()==end:
                      start,end=res.span()
                      numeral=line[start:end]
                      if numeral.find('e')>-1 or numeral.find('.')>-1:
                         color=COLORIDX_float
                      else:
                         color=COLORIDX_int
   #                    res=IDE_REptr_digits.search(line,c)
   #                    if res and res.start()==c:# and res.end()==end:
   #                       start,end=res.span()
   #                       color=COLORIDX_int
                   else:
#                       res=IDE_REptr_possibleNum.search(line,c)
#                       start,end=res.span()
                      color=COLORIDX_invalid
                stringStart=None
             else:
                start,end=c,c+1
                color=COLORIDX_invalid
                stringStart=None

             if colorize:
                charsColor+=[color if IDE_TDExtensionAvail else IDE_TEXT_COLORS[color]]*(end-start)
             c=end
      if colorize:
         return IDE_TEXT_COLORS[color],isQuoted,charsColor
      else:
         return isQuoted

  def drawTextLine(self,line,lineParent,color=COLORIDX_identifier,isQuoted=False):
      line=self.File[line]
      if self.hilight:  # highlighted
         color,isQuoted,charsColor=self.hilightLine(line,color,isQuoted)
      else: # no syntax highlighting
         color=COLORIDX_identifier
         charsColor=[color if IDE_TDExtensionAvail else IDE_TEXT_COLORS[color]]*len(line)
      lineParent.node().removeAllChildren()
      IDE_drawText(line,lineParent,charsColor)
      return color,isQuoted

  def gotoDir(self):
      IDE_gotoDir(self.DirName)

  def confirmReload(self):
      #~ print 'confirmReload'
      IDE_reloadFiles([self])

  def offerReload(self):
      if IDE_isInMode(MODE_offerReload):
         return
      IDE_removeAnyMenuNcallTip()
      IDE_CC_cancel()
      M.IDE_lastMode=IDE_getMode()
      IDE_setMode(MODE_offerReload)
      IDE_openYesNoDialog('File "%s" is obsolete.\nReload from disk ?'%self.FileName,self.doReload)

  def doReload(self,result):
      if result:
         IDE_reloadFiles([self])
      else:
         IDE_setMode(IDE_lastMode)


################################################################################
IDE_newDocIdx=0
IDE_tabXtraSideSpace=1.
IDE_tabsXlen=0
IDE_insert=True
IDE_CC_sttBegin=IDE_CC_sttEnd=-1
IDE_CC_autoComplete=IDE_CFG[CFG_autoComplete]
################################################################################
def IDE_arrangeDocsTabs():
    sx=IDE_documents[0].tab.getSx()
    x=0
    for d in IDE_documents:
        frame=d.tab.node().getFrame()
        bLen = (frame[1]-frame[0])*sx
        d.tab.setX(x+bLen*.5)
        x+=bLen

def IDE_exposeTab():
    if not len(IDE_documents): return
    docTabX=IDE_doc.tab.getX(render2dp)
    docTabXright=render2dp.getRelativePoint(IDE_doc.tab,Point3(IDE_doc.tab.node().getFrame()[1],0,0))[0]
    docTabHalfWidth=docTabXright-docTabX
    docTabX-=docTabHalfWidth
    l=-1<docTabX<1
    r=-1<docTabXright<1
    tab=IDE_documents[-1].tab
    tabXmostR2D=render2dp.getRelativePoint(tab,Point3(tab.node().getFrame()[1],0,0))[0]
    posR2D=IDE_docsTabsHandle.getX(render2dp)
    if (l!=r or (l==r and not l)) and (1.e-7<tabXmostR2D-1 or posR2D<-1):
       if docTabX<-1:
          x=-1-IDE_doc.tab.getX()*IDE_docsTabsHandle.getSx(render2dp)+docTabHalfWidth
       else:
          x=1-IDE_doc.tab.getX()*IDE_docsTabsHandle.getSx(render2dp)-docTabHalfWidth
       x=clampScalar(-(tabXmostR2D-posR2D)+1,-1,x)
    else:
       x=clampScalar(-(tabXmostR2D-posR2D)+1,-1,posR2D)
    IDE_docsTabsHandle.setX(render2dp,x)

def IDE_tabs_LMBdown(doc,mwp):
    global IDE_lastMode
    IDE_removeAnyMenuNcallTip()
    IDE_CC_cancel()
    IDE_hideSGB()
    IDE_cancelResolutionChange()
    doc.setDocActive(False,True)
    if doc.isObsolete:
       return
    IDE_lastMode=IDE_getMode()
    IDE_setMode(MODE_slidingDocsTabs)
    doc.tab.bind(DGG.B1RELEASE,IDE_tabs_LMBup,[doc])
    swapTask=taskMgr.add(IDE_swapTabs,IDE_tasksName+'swappingDocsTabs')
    swapTask.origX=base.mouseWatcherNode.getMouse()[0]
    swapTask.autoScroll=False
    swapTask.doc=doc

def IDE_swapTabs(t):
    if not base.mouseWatcherNode.hasMouse():
       return Task.cont
    mouseX=clampScalar(-1,1,base.mouseWatcherNode.getMouse()[0])
    docIdx=IDE_documents.index(t.doc)
    fr=t.doc.tab.node().getFrame()
    docTabLen=render2d.getRelativeVector(t.doc.tab,Vec3(fr[1]-fr[0],0,0))[0]
    for d in IDE_documents:
        if d==t.doc: continue
        dfr=d.tab.node().getFrame()
        mX=d.tab.getRelativePoint(render2d,Point3(mouseX,0,0))[0]
        if dfr[0]<mX<dfr[1]:
           dIdx=IDE_documents.index(d)
           l=render2d.getRelativePoint(d.tab,Point3(dfr[0],0,0))[0]
           r=render2d.getRelativePoint(d.tab,Point3(dfr[1],0,0))[0]
           thres=(l if docIdx>dIdx else r)+docTabLen*(1 if docIdx>dIdx else -1)
           if (mouseX<thres if docIdx>dIdx else mouseX>thres):
              IDE_documents[docIdx]=d
              IDE_documents[dIdx]=t.doc
              IDE_arrangeDocsTabs()
           break
    # 10 pixels offset to start autoScroll
    if not t.autoScroll and .5*abs(t.origX-mouseX)*IDE_winX>10.:
       t.autoScroll=True
    if t.autoScroll and not -.95<mouseX<.95:
       tab=IDE_documents[-1].tab
       tabXmostR2D=render2dp.getRelativePoint(tab,Point3(tab.node().getFrame()[1],0,0))[0]
       posR2D=IDE_docsTabsHandle.getX(render2dp)
       if 1.e-7<tabXmostR2D-1 or posR2D<-1:
          dx=globalClock.getDt()*.9
          x=clampScalar(-(tabXmostR2D-posR2D)+1,-1,posR2D+dx*(1 if mouseX<0 else -1))
          IDE_docsTabsHandle.setX(render2dp,x)
    return Task.cont

def IDE_tabs_LMBup(doc,mwp):
    taskMgr.remove(IDE_tasksName+'swappingDocsTabs')
    IDE_setMode(IDE_lastMode)
    doc.tab.unbind(DGG.B1RELEASE)
    IDE_saveFilesList()

def IDE_tabs_MMBdown(doc,mwp):
    global IDE_lastMode
    IDE_removeAnyMenuNcallTip()
    IDE_CC_cancel()
    IDE_hideSGB()
    IDE_cancelResolutionChange()
    if not IDE_isInMode(MODE_active):
       return
    if IDE_isCtrlDown: # close document
       IDE_closeDoc(doc)
       return
    tab=IDE_documents[-1].tab
    tabXmostR2D=render2dp.getRelativePoint(tab,Point3(tab.node().getFrame()[1],0,0))[0]
    if 1.e-7<tabXmostR2D-1 or IDE_docsTabsHandle.getX(render2dp)<-1:
       print('YOU CAN SLIDE TABS BAR', file=IDE_DEV)
       mpos=base.mouseWatcherNode.getMouse()
       slideTask=taskMgr.add(IDE_slideDocsTabs,IDE_tasksName+'slidingDocsTabs')
       slideTask.Xoffset=mpos[0]-IDE_docsTabsHandle.getX(render2dp)
       slideTask.tabMinX=-(tabXmostR2D-IDE_docsTabsHandle.getX(render2dp))+1
       IDE_lastMode=IDE_getMode()
       IDE_setMode(MODE_slidingDocsTabs)
       IDE_DO.acceptOnce(IDE_BTnode.getPrefix()+'mouse2-up',IDE_stopSlideDocsTabs)
    else:
       print('you can not slide tabs bar', file=IDE_DEV)

def IDE_shiftDocsTabs(inc,mwp):
    if IDE_getMode() not in (MODE_activeOrCompleting):
       return
    tab=IDE_documents[-1].tab
    tabXmostR2D=render2dp.getRelativePoint(tab,Point3(tab.node().getFrame()[1],0,0))[0]
    if 1.e-7<tabXmostR2D-1 or IDE_docsTabsHandle.getX(render2dp)<-1:
       tabMinX=-(tabXmostR2D-IDE_docsTabsHandle.getX(render2dp))+1
       x=clampScalar(tabMinX,-1,IDE_docsTabsHandle.getX(render2dp)+inc)
       IDE_docsTabsHandle.setX(render2dp,x)

def IDE_slideDocsTabs(t):
    if not base.mouseWatcherNode.hasMouse():
       return Task.cont
    mpos=base.mouseWatcherNode.getMouse()
    if -.9<mpos[0]<.9:
       x=clampScalar(t.tabMinX,-1,mpos[0]-t.Xoffset)
    else:
       tab=IDE_documents[-1].tab
       tabXmostR2D=render2dp.getRelativePoint(tab,Point3(tab.node().getFrame()[1],0,0))[0]
       posR2D=IDE_docsTabsHandle.getX(render2dp)
       dx=globalClock.getDt()*.9
       x=clampScalar(-(tabXmostR2D-posR2D)+1,-1,posR2D+dx*(1 if mpos[0]>0 else -1))
       t.Xoffset=mpos[0]-x
    IDE_docsTabsHandle.setX(render2dp,x)
    return Task.cont

def IDE_stopSlideDocsTabs():
    taskMgr.remove(IDE_tasksName+'slidingDocsTabs')
    IDE_setMode(IDE_lastMode)

################################################################################
# RECORDABLE COMMANDS
# for wx.TextCtrl :
#   1st: label
#   2nd: single or multiple line
#   3rd: textbox width
# for wx.RadioBox :
#   1st: label
#   2nd: choices
#   3rd: index base
#   4th: index multiplier (after index is shifted to zero-based)
numNselectDict={ 0:(wx.TextCtrl,'counts :',True,50),
                 1:(wx.CheckBox,'go and select')}
goNselectDict={0:(wx.CheckBox,'go and select',False)}
coms={
  'nextLine':(IDE_gotoNextLine, numNselectDict, [1,False],'goto next line'),
  'prevLine':(IDE_gotoPrevLine, numNselectDict, [1,False],'goto previous line'),
  'nextColumn':(IDE_gotoNextColumn, numNselectDict, [1,False],'goto next column'),
  'prevColumn':(IDE_gotoPrevColumn, numNselectDict, [1,False],'goto previous column'),
  'lineStart':(IDE_gotoFront,goNselectDict,[False],'goto line start'),
  'lineEnd':(IDE_gotoBack,goNselectDict,[False],'goto line end'),
  'docStart':(IDE_gotoDocBeg,goNselectDict,[False],'goto document start'),
  'docEnd':(IDE_gotoDocEnd,goNselectDict,[False],'goto document end'),
  'pageStart':(IDE_gotoPageBeg,goNselectDict,[False],'goto page start'),
  'pageEnd':(IDE_gotoPageEnd,goNselectDict,[False],'goto page end'),
  'nextWord':(IDE_gotoNextWord,goNselectDict,[False],'goto next word'),
  'prevWord':(IDE_gotoPrevWord,goNselectDict,[False],'goto previous word'),
  'expandSelection':(IDE_adjustSelection,[1],'expand selection'),
  'shrinkSelection':(IDE_adjustSelection,[-1],'shrink selection'),
  'delSelection':(IDE_delSelection,[],'delete selected text'),
  # 'delNextChar':(IDE_delChar,{0:(wx.TextCtrl,'counts :',True,50)}, [1,False],'delete next characters'),
  'delNextChar':(IDE_delChar,[1,False],'delete next characters'),
  # 'delPrevChar':(IDE_backSpcChar,{1:(wx.TextCtrl,'counts :',True,50)}, [None,1],'delete previous characters'),
  'delPrevChar':(IDE_backSpcChar,[None,1],'delete previous characters'),
  'delWordTail':(IDE_delWordTail,[],'delete to word end'),
  'delWordHead':(IDE_delWordHead,[],'delete to word start'),
  'delLine':(IDE_delLine,[],'delete current line'),
  'delLineTail':(IDE_delLineTail,[],'delete to end of line'),
  'delLineHead':(IDE_delLineHead,[],'delete to start of line'),
  'joinLines':(IDE_joinLines,
     { 0:(wx.TextCtrl,'connector :',True,50),
       1:(wx.CheckBox,'strip leading spaces')
     },
       [' ',True],'join selected lines'),
  'indent':(IDE_indentLine,[None],'indent'),
  'unindent':(IDE_backSpcChar,[None,1,None,False],'unindent'),
  'type':(IDE_injectChar,
     { 0:(wx.TextCtrl,'text :',False,200)}, ['something',None,False],'type some text'),
  'repeatChar':(IDE_doInsertRepeatedChars,
     { 0:(wx.TextCtrl,'text :',True,200),
       1:(wx.RadioBox,' mode : ',('fill until column','counts'),0),
       2:(wx.TextCtrl,'# :',True,50)
     },
       ['MAYDAY !!! ',True,2],'insert repeated text'),
  'changeCase':(IDE_changeCase,
     { 0:(wx.RadioBox,' case : ',('lower case','swap case','UPPER case'),-1),
     },
       [-1],'change case'),
  'breakLine':(IDE_breakLine,[],'insert line break'),
  'moveLines':(IDE_moveLines,
     { 0:(wx.RadioBox,' direction : ',('upward','downward'),-1,.5)}, [1],'move lines'),
  'duplicateLine':(IDE_duplicateLine,
     { 0:(wx.RadioBox,' direction : ',('upward','downward'),-1,.5)}, [1],'duplicate current line'),
  'selectInsideBrackets':(IDE_selectInsideBrackets,
     { 0:(wx.RadioBox,' put cursor at : ',('block start','block end'),0) }, [True],'select inside brackets'),
  'selectAll':(IDE_selectAll,[],'select all'),
  'cut':(IDE_cut,[],'cut'),
  'copy':(IDE_copy,[],'copy'),
  'paste':(IDE_paste,
     { 0:(wx.TextCtrl,'text :',False,200),
       1:(wx.CheckBox,'smart paste'),
       2:(wx.CheckBox,'keep cursor position')
     },
       [None,True,False],'paste'),
  'toggleInsert':(IDE_toggleInsert,[None],'toggle insert/overwrite'),
  'toggleComment':(IDE_toggleComment,[],'toggle comment/uncomment'),
}
IDE_COMMANDS={}
IDE_COMMANDSdefaultArgs={}
IDE_COMMANDSdescription={}
for com,fn in list(coms.items()):
    setattr(M,'COM_'+com,com)
    IDE_COMMANDS[com]=fn[:-2]
    IDE_COMMANDSdefaultArgs[com]=fn[-2]
    IDE_COMMANDSdescription[com]=fn[-1]
coms.clear()
del coms

IDE_REALtextCursor={}
# creates vertical caret
LScursor = LineSegs()
LScursor.setThickness(2)
LScursor.setColor(1,1,1,1)
LScursor.moveTo(0,0,0)
LScursor.drawTo(0,0,-IDE_lineheight)
IDE_REALtextCursor[CAR_vertical]=NodePath(LScursor.create())
# creates underline caret
LScursor.reset()
LScursor.moveTo(0,0,-IDE_lineheight)
LScursor.drawTo(IDE_all_chars_maxWidth*1.2,0,-IDE_lineheight)
IDE_REALtextCursor[CAR_underline]=NodePath(LScursor.create())
# creates top bottom caret
Redge = IDE_all_chars_maxWidth*1.1
Ledge =- IDE_all_chars_maxWidth*.1
LScursor.reset()
LScursor.moveTo(0,0,IDE_lineheight*.15)
LScursor.drawTo(Redge,0,IDE_lineheight*.15)
LScursor.drawTo(Redge,0,-IDE_lineheight*.3)
LScursor.drawTo(Redge,0,-IDE_lineheight*.5)
LScursor.drawTo(Redge,0,-IDE_lineheight)
LScursor.drawTo(Ledge,0,-IDE_lineheight)
LScursor.drawTo(Ledge,0,-IDE_lineheight*.5)
LScursor.drawTo(Ledge,0,-IDE_lineheight*.3)
LScursor.drawTo(Ledge,0,IDE_lineheight*.15)
LScursor.moveTo(Ledge,0,IDE_lineheight*.15)
LScursor.moveTo(Ledge,0,-IDE_lineheight)
LScursor.moveTo(Redge,0,IDE_lineheight*.15)
LScursor.moveTo(Redge,0,-IDE_lineheight)
IDE_REALtextCursor[CAR_cage] = NodePath(LScursor.create())
for v in (2,3,6,7):
    LScursor.setVertexColor(v,Vec4(1,1,1,.2))
# creates block caret
CM=CardMaker('text_cur')
CM.setFrame(0,IDE_all_chars_maxWidth*1.1,0,-IDE_lineheight)
IDE_REALtextCursor[CAR_block] = NodePath(CM.generate())
IDE_REALtextCursor[CAR_block].setColor(1,1,1,.7)
IDE_REALtextCursorOrigScale = Vec3(IDE_all_chars_maxWidth,1,IDE_lineheight)

IDE_textCursorTmpParent = NodePath('cursor parent')
IDE_textCursor = IDE_textCursorTmpParent.attachNewNode('')
IDE_textCursor.setTextureOff(100)
IDE_textCursor.setTransparency(TransparencyAttrib.MAlpha)
# I have to split it into an isolated render bin
# to avoid the blink bleeds to the text
IDE_textCursor.setBin('textCursorBin',0)
IDE_textCursorIval = Sequence(
    IDE_textCursor.colorScaleInterval(.1,IDE_COLOR_caret),
    Wait(.25),
    IDE_textCursor.colorScaleInterval(.1,Vec4(0,0,0,0)),
    name=IDE_ivalsName+'textCursor'
    )
IDE_textCursorIval.loop()
IDE_updateCaretsTypes()

# creates block quad
def createREALblock():
    CM=CardMaker('')
    CM.setFrame(0,IDE_all_chars_maxWidth,0,-IDE_lineheight)
    M.IDE_REALblock=NodePath(CM.generate())
    IDE_REALblock.setColor(IDE_REALblockGetColor())
    IDE_REALblock.setTransparency(TransparencyAttrib.MAlpha)
    M.IDE_REALblockIval=Sequence(
        IDE_REALblock.colorScaleInterval(.25,Vec4(3,3,3,1)),
        IDE_REALblock.colorScaleInterval(.25,Vec4(1,1,1,1)),
        Wait(.25),
        name=IDE_ivalsName+'block quad'
        )
    if IDE_CFG[CFG_animSelColor]:
       IDE_REALblockIval.loop()
IDE_REALblockGetColor=lambda:Vec4(IDE_COLOR_block[0],IDE_COLOR_block[1],IDE_COLOR_block[2],.5)
createREALblock()

# creates matching brackets hilight
def createREALbrHL():
    CM=CardMaker('')
    CM.setFrame(-.1*IDE_all_chars_maxWidth,IDE_all_chars_maxWidth*1.1,.2*IDE_lineheight,-IDE_lineheight*1.15)
    M.IDE_REALbrHL=NodePath(CM.generate())
    IDE_REALbrHL.setName('bracketMatchHilight')
    IDE_REALbrHL.setColor(Vec4(.55,.55,.55,1))
    M.IDE_REALbrMatchHL=NodePath(CM.generate())
    IDE_REALbrMatchHL.setColor(Vec4(1))
createREALbrHL()

# creates helper line for indentation
IDE_REALhelperLine = NodePath('')
IDE_REALhelperLine.attachNewNode( DU.createLine(color=(0,0,0,1), endColor=(1,.7,0,1),
    thickness=3, centered=0)).setTextureOff(10)
IDE_REALhelperLine.attachNewNode( DU.createUVLine(centered=0)).\
    setTexture(loader.loadTexture('horDash.png'),1 )
IDE_REALhelperLine.getChild(1).setY(-10)

IDE_REALhelperLine.setR(-90)
IDE_REALhelperLine.setTransparency(1)
# IDE_REALhelperLine.setAttrib(ColorAttrib.makeVertex())
# IDE_REALhelperLine.flattenLight()

LS=LineSegs('')
LS.setThickness(1)
LS.moveTo(0,0,0)
LS.drawTo(.5,0,0)
LS.drawTo(1,0,0)
LS.moveTo(0,0,-1)
LS.drawTo(.5,0,-1)
LS.drawTo(1,0,-1)
IDE_CTargHL=NodePath('')
IDE_CTargHL.attachNewNode(DU.createUVRect(align=0))
IDE_CTargHL.attachNewNode(DU.createUVRect(align=1,flipU=True))
IDE_CTargHL.setPos(.5,1,-1)
IDE_CTargHL.setSx(.5)
IDE_CTargHL.flattenStrong()
IDE_CTargHL=IDE_CTargHL.getChild(0)
IDE_CTargHL.setColor(IDE_COLOR_callArgsBG,1)
IDE_CTargHL.setTexture(pageArrowAlphaTex,10)
IDE_CTargHL.setTransparency(TransparencyAttrib.MAlpha)
argHLlines=IDE_CTargHL.attachNewNode(LS.create())
argHLlines.setTextureOff(100)
argHLlines.setColorOff(10)
argHLlines.setColorScale(IDE_COLOR_callTipsText,10)
for v in (0,2,3,5):
    LS.setVertexColor(v,1,1,1,0)

IDE_CTargsInsertTex=loader.loadTexture('IDE_insert.png')
IDE_CTargsInsertTex.setWrapU(Texture.WMClamp)
IDE_CTargsInsertTex.setWrapV(Texture.WMClamp)

# creates loading gauge
IDE_gauge=LoadingGauge(parent=IDE_overlayParent, scale=IDE_statusBarHeight*14,
   font=IDE_FONT_transmetals, ivalName=IDE_ivalsName+'hiding gauge')
IDE_gauge.hide()

# loads sounds
IDE_SOUND_oops=loadSound('aaow.mp3')
IDE_SOUND_error=loadSound('gotcha.mp3')
IDE_SOUND_errorOver=loadSound('plasma.mp3')
IDE_SOUND_notAvail=loadSound('springy.mp3')
IDE_SOUND_blockedKeyb=loadSound('wham.mp3')
IDE_SOUND_depleted=loadSound('punch.mp3')
IDE_SOUND_depleted.setPlayRate(2)

################################################################################
ERR_waitText=createMsg('ERROR, please wait a second',pad=(.5,.5,.25,.25))
ERR_waitText.setZ(-ERR_waitText.getTightBounds()[0][2])
ERR_waitText.flattenLight()
ERR_waitText.reparentTo(statusBar)
ERR_waitText.setScale(IDE_statusBarHeight*.7)
ERR_waitText.setX(render2d,0)
ERR_waitText.setBin('dialogsBin',-1)
ERR_waitText.hide()
IDE_errorWait = Sequence(
    Func(ERR_waitText.show),
    Wait(1),
    Func(IDE_SOUND_errorOver.play),
    Wait(.5),
    Func(ERR_waitText.hide),
    name=IDE_ivalsName+'wait after error'
    )
################################################################################

# creates bookmark
CM=CardMaker('')
CM.setFrame(0,1,-.5,.5)
IDE_lineMark=NodePath('bookmark')
IDE_lineMark.attachNewNode(CM.generate())
IDE_lineMark.setX(-IDE_canvas_leftBgXR2D/IDE_textScale[0])
IDE_lineMark.setZ(-.5*(1./IDE_lineheight-IDE_chars_maxBaseline2top))
IDE_lineMark.flattenLight()
IDE_lineMarkTex=loader.loadTexture('LM.png')
IDE_lineMarkTex.setWrapU(Texture.WMClamp)
IDE_lineMark.setTexture(IDE_lineMarkTex,2)
IDE_lineMark.setTransparency(TransparencyAttrib.MAlpha)
IDE_lineMarksCycleTime=0
IDE_lineMarksLastTime=0
IDE_lineMarksWrapThreshold=.3

# creates file tab parents
IDE_REALtabLcorner=NodePath('tab left corner')
IDE_REALtabMid=NodePath('tab middle')
IDE_REALtabRcorner=NodePath('tab right corner')
IDE_REALtabLabelL=NodePath('tab label left corner')
IDE_REALtabLabelMid=NodePath('tab label middle')
IDE_REALtabLabelR=NodePath('tab label right corner')
IDE_createTabGeoms()

# loads macros
if os.path.exists(IDE_macrosPath):
   MACROS = loadFromFile(IDE_macrosPath)

# loads snippets
updateSnips=not os.path.exists(IDE_snippetsPath)
if not updateSnips:
   defaultSnips=SNIPPETS
   SNIPPETS = loadFromFile(IDE_snippetsPath)
   oldNumSnips=len(list(SNIPPETS.keys()))
   for n,s in list(defaultSnips.items()):
       if n not in SNIPPETS:
          SNIPPETS[n]=s
   updateSnips=len(list(SNIPPETS.keys()))-oldNumSnips
if updateSnips:
   IDE_saveSnippetsToDisk()

# updates recent files list
recentFilesListName=joinPaths(IDE_path,'%s.%s'%(RECENT_FILES,PLATFORM))
if os.path.exists(recentFilesListName):
   IDE_recentFiles = loadFromFile(recentFilesListName)
else:
   IDE_recentFiles = list(APP_files)

# files records
filesPropsName=joinPaths(IDE_path,'%s.%s'%(FILES_PROPS,PLATFORM))
if os.path.exists(filesPropsName):
   IDE_filesProps=loadFromFile(filesPropsName)
   if len(IDE_filesProps):
      if len(list(IDE_filesProps.values())[0])==7: # OLD VERSION, w/o CWD & args
         for k,v in list(IDE_filesProps.items()):
             v+=['.', []] # CWD, arguments
             IDE_filesProps[k]=v
else:
   IDE_filesProps={}

# hidden documents, only used to store log file when it's closed
IDE_hiddenDocs=[]
# the opened redirected output
IDE_log=None
IDE_lastDocB4Jump2Scene=None
IDE_lastDocB4Log=None
IDE_logOverSceneParent=IDE_2Droot.attachNewNode('log over scene parent')

# loads documents
IDE_doc=None
IDE_documents=[]
IDE_openFiles(APP_files)
loadedFiles=[d.FullPath for d in IDE_documents]
IDE_documents[ loadedFiles.index(
  LAST_mainNcurr[-1] if LAST_mainNcurr[-1] in loadedFiles else APP_mainFile)
  ].setDocActive(arrangeTabs=True)

# lets file open process after loading the firstly loaded ones
# affects recent files list
UPDATE_RECENT_FILES=True

# clears notify output, to cleanup IDE startup notification rubbish,
# and prepares clean output for user's app
# LSS.setData('')

LOG_TW=TextWrapper()
# let's just save the calculation, so it only exists here in 1 spot, and
# when adjusting window size, I only need to call this
LOG_TW.calcWidth=lambda:int(IDE_frameWidth/(IDE_all_chars_maxWidth*IDE_textScale[0]))-4
LOG_TW.width=LOG_TW.calcWidth()

# creates log ?
if IDE_CFG[CFG_autoCreateLog]:
   IDE_openLog()
   IDE_switchToMainFile()

IDE_setMode(MODE_starting)
# initiates polygonal button system
IDEPolyButton.setup( parent=render2dp, buttonThrower=IDE_BTnode,
                     taskNamePrefix=IDE_tasksName, startNow=False)


# resumes user's scene
Sequence(
   Wait(.2),
   Func(IDE_toggleSceneActive),
   Func(IDE_setMode,MODE_active),
#    Func(IDE_toggleSGBAndNProps),
   name=IDE_ivalsName+'resume user scene'
).start()

relocateFRMeter()
pageUpSkin.show()
pageDnSkin.show()

# remove IDE's path so it won't be scanned by import completer
if IDE_path in sys.path:
   sys.path.remove(IDE_path)

if not IDE_TDExtensionAvail:
   msg = createMsg('Failed to load C++ TextDrawer extension.'+IDE_TDExtensionErr,bg=(1,0,0,.85))
   putMsg(msg,'TD not avail',10,stat=True)

if PStatsEnabled: # PStats is enabled from the welcome screen
   startPStatsServer()
   taskMgr.doMethodLater(.5,connectToPStatsServer,IDE_tasksName+'connectToPStatsServer',extraArgs=[])

def fileModCheck(t):
    autoReload=IDE_CFG[CFG_autoReloadFiles]
    if autoReload:
       reloaded=[]
    for d in IDE_documents:
        if d.FullPath:
           try:
              modTime=os.stat(d.FullPath)[stat.ST_MTIME]
              if modTime!=IDE_filesProps[d.FullPath][1] and not d.isObsolete:
                 d.isObsolete=True
                 if autoReload:
                    reloaded.append(d)
           except:
              pass
    if autoReload and reloaded:
       IDE_reloadFiles(reloaded)
       if IDE_CFG[CFG_autoUpdateMainMod] and APP_mainFile in [f.FullPath for f in reloaded] and\
          IDE_getDocByPath(APP_mainFile): # successfully reloaded ?
            wasInTheScene=IDE_root.isHidden()
            if wasInTheScene:
               IDE_2Droot.hide()
               IDE_goBackToIDE()
            IDE_saveAllAndUpdate(autoJumpToScene=wasInTheScene)
            if wasInTheScene:
               IDE_2Droot.show()
    return t.again


def IDE_getUpdatesList(onReceivedFunc):
    rf = Ramfile()
    http = HTTPClient()
    channel = http.makeChannel(True)
    channel.beginGetDocument(DocumentSpec('http://ynjh.%s/OIDE/965456'%IDEPreferences.UPGRADE_SRV[IDE_CFG[CFG_host]]))
    channel.downloadToRam(rf)
    M.IDE_isUpgrading = True
    def digest(path):
        openfile = open(path,'rb')
        content = openfile.read()
        openfile.close()
        m = md5()
        m.update(content)
        return m.digest()
    def downloadTask(task):
        if channel.run():
           return task.cont
#         checkingDllExistance = False
        if channel.isDownloadComplete():
           s = rf.getData()
           releaseData = cPickle.loads(zlib.decompress(s).replace('\r\n','\n').replace('\r','\n'))
           print('LATEST RELEASE: v'+releaseData['v'])
           M.IDE_PACKAGES = releaseData['PACKAGES']
           mustBeUpdated = []
           PACKAGESkeys = list(IDE_PACKAGES.keys())
           for d in [kk for kk in PACKAGESkeys if not kk.startswith('TextDrawer ')]:
               for f,sig in releaseData[d]:
                   fullpath = joinPaths(IDE_path,f)
                   if not os.path.exists(fullpath) or digest(fullpath)!=sig:
                      mustBeUpdated.append(d)
                      break
           if WIN:
              TDbinary = 'TextDrawer C++ extension for P3D %s'%P3D_VERSION
              if IDE_TDExtensionAvail:
                 f,sig = releaseData[TDbinary]
                 TDfullpath = joinPaths(IDE_path,f)
                 if os.path.exists(TDfullpath) and digest(TDfullpath)!=sig:
                    mustBeUpdated.append(TDbinary)
#                     print 'NEW TextDrawer !!'
              else:
                 if TDbinary in PACKAGESkeys:
                    mustBeUpdated.append(TDbinary)
                 else:
                    print('TextDrawer C++ extension for your P3D version is not available yet.')
           else:
              if not IDE_TDExtensionAvail:
                 mustBeUpdated.append('TextDrawer source')
#                  print 'You should download and build the TextDrawer extension.'
           result = [mustBeUpdated, releaseData['v']]
        else:
           result = [None]*2
        currTime = time.time()
        IDE_syncConfigInPreferences(CFG_lastUpdateCheckTime, currTime)
        M.IDE_isUpgrading = False
        onReceivedFunc(*result)
    taskMgr.add(downloadTask, IDE_tasksName+'download updates list')

def IDE_removeUpdateEndsButton():
    updateEndsButton = IDE_root.find('**/updateEndsButton')
    if not updateEndsButton.isEmpty():
       updateEndsButton.getPythonTag('destroy')()

def IDE_downloadUpdateEnds(error=False):
    def bringUpPrefWindow():
        updateEndsButton.destroy()
        if IDEPreferences.PREF_OPEN:
           IDEPreferences.openPreferences()
    updateEndsButton = DirectButton(parent=statusBar,relief=DGG.FLAT,
       text='ERROR DOWNLOADING UPGRADES' if error else 'Upgrades successfully installed.\nYou should restart the IDE.',
       text_font=IDE_FONT_monospace, text_align=TextNode.ALeft,
       scale=IDE_statusBarHeight*.58, pad=(IDE_statusBarHeight*10,)*2,
       frameColor=(1,1,1,.9), command=bringUpPrefWindow,
       clickSound=0, rolloverSound=0, pressEffect=0)
    updateEndsButton.setName('updateEndsButton')
    updateEndsButton.setPythonTag('destroy',updateEndsButton.destroy)
    updateEndsButton.setBin('dialogsBin',0)
    updateEndsButton.setPos(
       IDE_canvasThumbBorder-updateEndsButton.node().getFrame()[0]*updateEndsButton.getSx(),
       0,IDE_statusBarHeight+IDE_canvasThumbBorder-updateEndsButton.node().getFrame()[2]*updateEndsButton.getSz())
    Sequence(
      updateEndsButton.colorScaleInterval(.2,Vec4(1,0,0,1) if error else Vec4(0,.8,1,1),Vec4(1)),
      updateEndsButton.colorScaleInterval(.2,Vec4(1)),
      name=IDE_ivalsName+'update download ends'
    ).loop()

def IDE_offerUpdates(button,updates,releaseVersion):
    button.destroy()
    IDEPreferences.openPreferences()
    IDEPreferences.prefNotebook.Selection = 5 # UPDATES TAB
    if updates:
       mustBeUpdatedText = IDEPreferences.prefNotebook.FindWindowByName(IDEPreferences.AVAIL_UPGRADES)
       mustBeUpdatedText.mustBeUpdated = updates
       mustBeUpdatedText.releaseVersion = releaseVersion
       mustBeUpdatedText.buildDownloadItems()
       mustBeUpdatedText.Show()
       updateButton = IDEPreferences.prefNotebook.FindWindowByName(IDEPreferences.UPGRADE_NOW)
       updateButton.Show()
       updateButton.GetParent().GetSizer().Layout()

def IDE_autoCheckUpdate():
    if IDE_isUpgrading: return
    updateButton = DirectButton(parent=statusBar,relief=None,
       text='Checking upgrades...', text_font=IDE_FONT_monospace, text_align=TextNode.ALeft,
       scale=IDE_statusBarHeight*.58, pad=(IDE_statusBarHeight*10,)*2,
       frameColor=(1,1,1,.9),
       clickSound=0, rolloverSound=0, pressEffect=0)
    updateButton.setBin('dialogsBin',0)
    setUpdateButtonPos = lambda: updateButton.setPos(
       IDE_canvasThumbBorder-updateButton.node().getFrame()[0]*updateButton.getSx(),
       0,IDE_statusBarHeight+IDE_canvasThumbBorder-updateButton.node().getFrame()[2]*updateButton.getSz())
    setUpdateButtonPos()

    CM = CardMaker('card')
    CM.setFrame(0,1,0,1)
    card = updateButton.attachNewNode(CM.generate(),sort=-10)
    card.setTexture(IDE_gradingAlphaTexV0_2)
    updateButton.stateNodePath[0].reparentTo(updateButton,1)
    def fitCard(extraRight=False):
        fr = VBase4(updateButton.node().getFrame())
        if extraRight:
           fr[1] += (fr[3]-fr[2])*.75
           updateButton['frameSize'] = fr
        card.setPos(fr[0],1,fr[2])
        card.setScale(fr[1]-fr[0],1,fr[3]-fr[2])
    fitCard()

    def createCloseButton():
        updateButton.resetFrameSize()
        fitCard(extraRight=True)
        b = DirectButton(parent=updateButton, relief=None,
           image='IDE_close2.png', scale=.61,
           command=updateButton.destroy, clickSound=0, rolloverSound=0, pressEffect=0)
        b.alignTo(updateButton, DGG.UR, gap=(.3,)*2)
        b.setColorScaleOff()
        b.setColor(0,0,0,1)
        b.stateNodePath[2].setTexture(loader.loadTexture('IDE_close2inv.png'),1)
        return b
    def checkUpdateNow(mustBeUpdated,releaseVersion):
        if mustBeUpdated:
           updateButton['text']='Upgrades available.'
           createCloseButton()
           Sequence(
             updateButton.colorScaleInterval(.2,Vec4(.2,.6,.95,1),Vec4(1)),
             updateButton.colorScaleInterval(.2,Vec4(1)),
             name=IDE_ivalsName+'upgrade available'
           ).loop()
           updateButton['command']=lambda:IDE_offerUpdates(updateButton,mustBeUpdated,releaseVersion)
        else:
           if mustBeUpdated is not None:
#               print 'No new update.'
              updateButton['text']='No new updates'
              updateButton.resetFrameSize()
              fitCard()
              wait = 3
              color = Vec4(.5,.5,.5,1)
              Sequence(
                Wait(wait),
                updateButton.posInterval(3,updateButton.getPos()+Point3(0,0,-1)),
                Func(updateButton.destroy),
                name=IDE_ivalsName+'update destroy'
              ).loop()
           else:
#               print 'ERROR: updates check failed'
              updateButton['text']='Upgrades check failed.\nCheck your internet connection.'
              createCloseButton()
              wait = 5
              color = Vec4(1,0,0,1)
              def retry():
                  updateButton.destroy()
                  IDE_autoCheckUpdate()
              updateButton['command']=retry
           Sequence(
             updateButton.colorScaleInterval(.2,color,Vec4(1)),
             updateButton.colorScaleInterval(.2,Vec4(1)),
             name=IDE_ivalsName+'update colorscale'
           ).loop()
        setUpdateButtonPos()
    renderFrame(2)
    IDE_getUpdatesList(checkUpdateNow)

def IDE_scheduleNextUpdate():
    taskMgr.removeTasksMatching(IDE_scheduledUpdateTaskName)
    if IDE_CFG[CFG_regularUpdateInterval]:
       lastUpdateCheckTime = IDE_CFG[CFG_lastUpdateCheckTime]
       updateTime = max(0, lastUpdateCheckTime+IDEPreferences.UPGRADE_OPT[IDE_CFG[CFG_regularUpdateInterval]][1]-time.time())
       print('\nNext update : %s hours later'%(updateTime/3600))
       taskMgr.doMethodLater(updateTime,IDE_autoCheckUpdate,IDE_scheduledUpdateTaskName,extraArgs=[])
IDE_scheduleNextUpdate()
# IDE_autoCheckUpdate()# JUST FOR TESTING !!!!!!!!

taskMgr.doMethodLater(1,fileModCheck,IDE_tasksName+'fileModCheck')

if MAIN_MOD_ERROR:
   IDE_processException(MAIN_MOD_ERROR)

base.win.setCloseRequestEvent(closeWindowEventName)
globalClock.setMode(ClockObject.MNormal)
IDE_step = IDE_safeStep
# IDErun replaces the universal run (taskMgr.run).
# IDE_safeRun is a way to intercept and remove broken continuous tasks,
# without any need to drop to Python prompt to clean up user's messy tasks.
builtins.IDErun = IDE_safeRun
