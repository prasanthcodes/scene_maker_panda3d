from pandac.PandaModules import Vec3
# Task is not imported, so you'll get an error in Jack.changeColor()
# from direct.task import Task
from random import random
from direct.interval.IntervalGlobal import *

def changeColor():
    print('RECOLORED !!!')


class Jack:
  def __init__(self):
      num=10
      self.jacksParent=render.attachNewNode('')
      for j in range(num):
          jack=loader.loadModel("jack")
          jack.reparentTo(self.jacksParent)
          jack.setScale(.5)
          jack.setPos(-(num-1)*.5+j,-10,0)
          jack.setH(180)
      self.jacksParent.hprInterval(3,Vec3(0,0,360)).loop()
      taskMgr.doMethodLater(3,self.changeColor,'cc')
      taskMgr.doMethodLater(5,self.printMe,'pm')


  def changeColor(self,t):
      self.jacksParent.setColor(random(),random(),random(),1)
      print('RECOLORED !!!')
      # should give you an error since Task is not imported
      return Task.again

  # should give you an error, since the task is not accepted as the second argument,
  # because I don't set extraArgs=[] when creating the task
  def printMe(self):
      print(self.jacksParent)
