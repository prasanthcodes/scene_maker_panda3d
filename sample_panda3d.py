from panda3d.core import *
from direct.showbase.ShowBase import ShowBase
from math import sin,cos


class Test(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Example scene
        scene = self.loader.loadModel("sphere.egg")
        scene.reparentTo(self.render)
        scene.setScale(0.25, 0.25, 0.25)
        scene.setPos(-8, 42, 0)
        self.taskMgr.add(self.spinCameraTask, "SpinCameraTask")

    def spinCameraTask(self,task):
        angleDegrees = task.time * 6.0
        angleRadians = angleDegrees * (3.14159 / 180.0)
        self.camera.setPos(20 * sin(angleRadians), -20 * cos(angleRadians), 3)
        self.camera.setHpr(angleDegrees, 0, 0)
        return task.cont

    

app = Test()
app.run()