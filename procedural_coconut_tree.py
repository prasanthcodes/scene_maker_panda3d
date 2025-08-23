import math
import random
from direct.showbase.ShowBase import ShowBase
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, NodePath, Point3, Vec3, TransformState

class CoconutTreeGenerator(ShowBase):
    def __init__(self, seed=0):
        ShowBase.__init__(self)
        random.seed(seed)
        tree = self.generate_coconut_tree()
        tree.reparentTo(self.render)
        self.camera.setPos(0, -20, 2)
        self.camera.lookAt(0, 0, 3)

    def generate_coconut_tree(self):
        tree_node = NodePath("coconut_tree")

        # Procedural parameters
        height = random.uniform(4, 6)
        bottom_radius = random.uniform(0.4, 0.6)
        top_radius = random.uniform(0.2, 0.3)
        num_leaves = random.randint(6, 10)
        num_coconuts = random.randint(2, 4)
        sides = 20  # for cylinder and sphere

        # Trunk (tapered cylinder)
        trunk = self.create_cylinder(bottom_radius, top_radius, height, sides)
        trunk.reparentTo(tree_node)

        # Leaves
        leaves_node = NodePath("leaves")
        leaves_node.setPos(0, 0, height)
        leaves_node.reparentTo(tree_node)
        for i in range(num_leaves):
            angle = i * 360 / num_leaves + random.uniform(-10, 10)
            pitch = random.uniform(30, 60)
            leaf = self.create_leaf()
            leaf.setHpr(angle, -pitch, 0)
            leaf.reparentTo(leaves_node)

        # Coconuts
        coconuts_node = NodePath("coconuts")
        coconuts_node.setPos(0, 0, height - 0.5)
        coconuts_node.reparentTo(tree_node)
        for i in range(num_coconuts):
            angle = random.uniform(0, 360)
            distance = random.uniform(0.1, 0.3)
            coconut = self.create_sphere(0.2, sides, sides // 2)
            coconut.setPos(math.sin(math.radians(angle)) * distance, math.cos(math.radians(angle)) * distance, 0)
            coconut.reparentTo(coconuts_node)

        return tree_node

    def create_cylinder(self, bottom_radius, top_radius, height, sides):
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('cylinder', format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        geom = Geom(vdata)
        tri = GeomTriangles(Geom.UHStatic)

        # Side vertices
        for i in range(sides):
            angle = 2 * math.pi * i / sides
            cos = math.cos(angle)
            sin = math.sin(angle)

            # Bottom
            vertex.addData3(bottom_radius * cos, bottom_radius * sin, 0)
            normal.addData3(cos, sin, 0)  # Approximate normal (ignoring taper for simplicity)
            color.addData4(0.5, 0.3, 0.1, 1)  # Brown

            # Top
            vertex.addData3(top_radius * cos, top_radius * sin, height)
            normal.addData3(cos, sin, 0)
            color.addData4(0.5, 0.3, 0.1, 1)

        # Side triangles
        for i in range(sides):
            a = i * 2
            b = a + 1
            c = ((i + 1) % sides) * 2 + 1
            d = c - 1
            tri.addVertices(a, b, c)
            tri.addVertices(a, c, d)

        # Bottom cap center
        bottom_center = vdata.getNumRows()
        vertex.addData3(0, 0, 0)
        normal.addData3(0, 0, -1)
        color.addData4(0.5, 0.3, 0.1, 1)

        # Top cap center
        top_center = bottom_center + 1
        vertex.addData3(0, 0, height)
        normal.addData3(0, 0, 1)
        color.addData4(0.5, 0.3, 0.1, 1)

        # Bottom cap triangles
        for i in range(sides):
            a = i * 2
            b = ((i + 1) % sides) * 2
            tri.addVertices(bottom_center, b, a)  # Reversed for normal

        # Top cap triangles
        for i in range(sides):
            a = i * 2 + 1
            b = ((i + 1) % sides) * 2 + 1
            tri.addVertices(top_center, a, b)  # Reversed for normal

        geom.addPrimitive(tri)
        node = GeomNode('cylinder')
        node.addGeom(geom)
        return NodePath(node)

    def create_sphere(self, radius, slices, rings):
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('sphere', format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        geom = Geom(vdata)
        tri = GeomTriangles(Geom.UHStatic)

        for i in range(rings + 1):
            v = i / rings
            theta = v * math.pi
            cos_theta = math.cos(theta)
            sin_theta = math.sin(theta)
            z = cos_theta * radius
            ring_radius = sin_theta * radius
            for j in range(slices):
                u = j / slices
                phi = u * 2 * math.pi
                cos_phi = math.cos(phi)
                sin_phi = math.sin(phi)
                x = cos_phi * ring_radius
                y = sin_phi * ring_radius
                vertex.addData3(x, y, z)
                normal.addData3(x / radius, y / radius, z / radius)
                color.addData4(0.2, 0.8, 0.2, 1)  # Green for coconut

        for i in range(rings):
            for j in range(slices):
                a = i * slices + j
                b = a + slices
                c = b + (1 if j < slices - 1 else 1 - slices)
                d = a + (1 if j < slices - 1 else 1 - slices)
                tri.addVertices(a, b, d)
                tri.addVertices(b, c, d)

        geom.addPrimitive(tri)
        node = GeomNode('sphere')
        node.addGeom(geom)
        return NodePath(node)

    def create_leaf(self):
        format = GeomVertexFormat.getV3n3c4()
        vdata = GeomVertexData('leaf', format, Geom.UHStatic)
        vertex = GeomVertexWriter(vdata, 'vertex')
        normal = GeomVertexWriter(vdata, 'normal')
        color = GeomVertexWriter(vdata, 'color')
        geom = Geom(vdata)
        tri = GeomTriangles(Geom.UHStatic)

        # Simple triangular leaf
        length = random.uniform(2, 3)
        width = random.uniform(0.3, 0.5)

        vertex.addData3(0, 0, 0)
        normal.addData3(0, 1, 0)
        color.addData4(0, 0.6, 0, 1)  # Green

        vertex.addData3(-width / 2, 0, length)
        normal.addData3(0, 1, 0)
        color.addData4(0, 0.6, 0, 1)

        vertex.addData3(width / 2, 0, length)
        normal.addData3(0, 1, 0)
        color.addData4(0, 0.6, 0, 1)

        tri.addVertices(0, 1, 2)

        # Back face (optional, for double-sided)
        tri.addVertices(0, 2, 1)

        geom.addPrimitive(tri)
        node = GeomNode('leaf')
        node.addGeom(geom)
        return NodePath(node)

app = CoconutTreeGenerator()
app.run()