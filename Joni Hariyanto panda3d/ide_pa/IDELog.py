from direct.task import Task
import os, sys

class Log:
  def __init__(self,stream,mutedPythonOutput=None,recordPythonOutput=1):
      self.stream=stream
      self.mutedPythonOutput=mutedPythonOutput
      self.recordPythonOutput=recordPythonOutput
      if self.recordPythonOutput:
         self.log=''
      self.stdout=sys.stdout
      self.stderr=sys.stderr
      self.updater=None
      self.taskError=None

  def stdoutOn(self):
      sys.stdout=self.stdout
      sys.stderr=self.stderr
  def stdoutOff(self):
      sys.stdout=self.mutedPythonOutput if self.mutedPythonOutput else self
      sys.stderr=sys.stdout

  def out(self,s):
      self.stdoutOn()
      print(s, end=' ')
      self.stdoutOff()

  def write(self,s):
      self.out(s) # keep displaying python "print"s
      if self.recordPythonOutput:
         self.log+=s
         if callable(self.updater):
            self.stdoutOn() # only needed during devel, so I can see the errors
            self.updater(s)
            self.stdoutOff() # only needed during devel, so I can see the errors

  def startMonitorNotify(self):
      import IDE
      taskMgr.add(self.checkNotify,IDE.IDE_tasksName+'checkNotify',extraArgs=[])

  def checkNotify(self,getTaskErr=False):
      if self.stream.getDataSize():
         s=self.stream.getData()
         if getTaskErr:
            errPos=s.rfind(':task(error):')
            if errPos>-1:
               self.taskError=s[errPos:]
            elif self.taskError is not None:
               self.taskError=None
            return
         self.log+=s
         self.stream.clearData()
#          self.stream.setData('')
         if callable(self.updater):
            self.stdoutOn() # only needed during devel, so I can see the errors
            self.updater(s)
            self.stdoutOff() # only needed during devel, so I can see the errors
      return Task.cont

  def writeToDisk(self):
      f=open(os.path.join(os.path.dirname(__file__),sys.modules['IDE'].IDE_LOG_NAME),'w')
      f.write(self.log)
      f.close()

  def setUpdateCallback(self,method):
      self.updater=method
