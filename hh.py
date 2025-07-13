from direct.showbase.ShowBase import ShowBase
from panda3d.core import GeoMipTerrain, CollisionTraverser, CollisionNode
from panda3d.core import CollisionRay, CollisionHandlerQueue, BitMask32
from panda3d.core import NodePath
import sys

class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set up the terrain
        self.terrain = GeoMipTerrain("terrain")
        self.terrain.setHeightfield("heightmap.png")  # Replace with your heightmap
        self.terrain.setBlockSize(32)
        self.terrain.setNear(40)
        self.terrain.setFar(100)
        self.terrain.setFocalPoint(base.camera)
        self.terrain.getRoot().reparentTo(render)
        self.terrain.getRoot().setSz(50)  # Scale the terrain height
        self.terrain.generate()

        # Set collision mask for the terrain
        self.terrain.getRoot().setCollideMask(BitMask32.bit(1))
        #self.terrain.getRoot().setFromCollideMask(BitMask32.allOff())
        #self.terrain.getRoot().setIntoCollideMask(BitMask32.bit(1))

        # Load Ralph model
        self.ralph = loader.loadModel("ralph")
        self.ralph.reparentTo(render)
        self.ralph.setPos(10, 10, 10)  # Start above the terrain

        # Set up collision system
        self.cTrav = CollisionTraverser()
        self.cHandler = CollisionHandlerQueue()

        # Create a collision ray pointing downward
        self.ralphGroundRay = CollisionRay()
        self.ralphGroundRay.setOrigin(0, 0, 10)  # Relative to Ralph
        self.ralphGroundRay.setDirection(0, 0, -1)  # Downward

        # Attach the ray to a collision node
        self.ralphGroundCol = self.ralph.attachNewNode(CollisionNode("ralphRay"))
        self.ralphGroundCol.node().addSolid(self.ralphGroundRay)
        self.ralphGroundCol.node().setFromCollideMask(BitMask32.bit(1))
        self.ralphGroundCol.node().setIntoCollideMask(BitMask32.allOff())

        # Add the ray to the collision traverser
        self.cTrav.addCollider(self.ralphGroundCol, self.cHandler)

        # Add task to update Ralph's position
        taskMgr.add(self.update, "update")
        self.keyMap = {
            "left": 0, "right": 0, "forward": 0, "cam-left": 0, "cam-right": 0}
            
        self.accept("escape", sys.exit)
        self.accept("arrow_left", self.setKey, ["left", True])
        self.accept("arrow_right", self.setKey, ["right", True])
        self.accept("arrow_up", self.setKey, ["forward", True])
        self.accept("a", self.setKey, ["cam-left", True])
        self.accept("s", self.setKey, ["cam-right", True])
        self.accept("arrow_left-up", self.setKey, ["left", False])
        self.accept("arrow_right-up", self.setKey, ["right", False])
        self.accept("arrow_up-up", self.setKey, ["forward", False])
        self.accept("a-up", self.setKey, ["cam-left", False])
        self.accept("s-up", self.setKey, ["cam-right", False])
        
    # Records the state of the arrow keys
    def setKey(self, key, value):
        self.keyMap[key] = value
        
        
    def update(self, task):
        # Traverse the scene to detect collisions
        self.cTrav.traverse(render)

        # Process collision entries
        entries = list(self.cHandler.getEntries())
        if entries:
            # Sort entries by distance (closest first)
            entries.sort(key=lambda x: x.getSurfacePoint(render).getZ())
            # Get the closest collision point
            if entries[0].getIntoNode() == self.terrain.getRoot().node():
                z = entries[0].getSurfacePoint(render).getZ()
                self.ralph.setZ(z)  # Adjust Ralph's Z to the terrain height

        # Move Ralph (example: forward movement)
        if self.keyMap.get("forward", False):  # Assume keyMap is set up
            self.ralph.setY(self.ralph, -10 * globalClock.getDt())

        return task.cont

app = MyGame()
app.run()