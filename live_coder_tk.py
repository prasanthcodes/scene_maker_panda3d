from direct.showbase.ShowBase import ShowBase
from panda3d.core import *
from direct.task.Task import Task
import sys
import traceback
from direct.actor.Actor import Actor
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import tkinter.font as tkfont

class LiveCoder(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Set up initial scene node
        self.scene = self.render.attachNewNode("Scene")

        # Initial example: Load built-in sphere primitive (always available, no external file)
        self.load_example()

        # Camera setup
        self.disableMouse()
        self.camera.setPos(0, -10, 0)

        # Lighting for visibility
        alight = AmbientLight('alight')
        alight.setColor((0.4, 0.4, 0.4, 1))
        alnp = self.render.attachNewNode(alight)
        self.render.setLight(alnp)
        dlight = DirectionalLight('dlight')
        dlight.setDirection((-1, -1, -1))
        dlnp = self.render.attachNewNode(dlight)
        self.render.setLight(dlnp)

        self.startTk()
        
        self.root = self.tkRoot
        self.root.title("Panda3D Live Coder")
        self.root.geometry("1280x800")
        
        # Code text area with corrected example using loader for visible sphere
        self.initial_code = """
from direct.gui.DirectGui import *
from panda3d.core import *

ScrolledFrame_L1=DirectScrolledFrame(
	frameSize=(-2, 2, -2, 2),  # left, right, bottom, top
	canvasSize=(-2, 2, -2, 2),
	pos=(0,0,0),
	frameColor=(0.3, 0.3, 0.3, 0)
)
canvas_6=ScrolledFrame_L1.getCanvas()

dlabel_L0=DirectLabel(parent=canvas_6,text="LUT Loader",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.3, 0, 0.7))
CheckButton_L1 = DirectCheckButton(parent=canvas_6,text = "Enable LUT" ,scale=.06,pos=(-1.2, 1,0.6),text_align=TextNode.ALeft)
dlabel_L2=DirectLabel(parent=canvas_6,text="Current File:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.2, 0, 0.5))
dlabel_L3=DirectLabel(parent=canvas_6,text="R:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-0.8, 0, 0.5))
dbutton_L4 = DirectButton(parent=canvas_6,text='Select File',pos=(-1.2, 0, 0.4),scale=0.07,text_align=TextNode.ALeft)
dlabel_L5=DirectLabel(parent=canvas_6,text="LUT Factor:",text_scale=0.06,text_align=TextNode.ALeft,pos=(-1.2, 0, 0.3))
dentry_L6 = DirectEntry(parent=canvas_6,text = "", scale=0.06,width=6,pos=(-0.8, 0, 0.3),initialText="", numLines = 1, focus=0)

    """
        self.create_gui()

        
    def create_gui(self):
        main_paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # ==================== LEFT: CODE EDITOR ====================
        left_frame = ttk.Frame(main_paned, width=650)
        main_paned.add(left_frame, weight=2)

        toolbar = ttk.Frame(left_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="▶ Run Code (Ctrl+R)", command=self.on_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Clear Scene", command=self.on_clear).pack(side=tk.LEFT, padx=5)

        ttk.Label(left_frame, text="Python Code Editor (Panda3D)").pack(anchor=tk.W, padx=5)

        self.code_text = scrolledtext.ScrolledText(
            left_frame, wrap=tk.NONE, font=("Consolas", 11), undo=True, tabs=('4c',)
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        # Horizontal scrollbar
        x_scroll = ttk.Scrollbar(
            left_frame,
            orient=tk.HORIZONTAL,
            command=self.code_text.xview
        )

        x_scroll.pack(fill=tk.X, padx=5, pady=(0,5))

        # Connect text widget to scrollbar
        self.code_text.config(xscrollcommand=x_scroll.set)
        self.code_text.insert("1.0", self.initial_code)
        
        self.setup_syntax_highlighting()

        # Keyboard shortcuts
        self.code_text.bind("<Control-r>", lambda e: (self.run_code(), "break"))
        self.code_text.bind("<Control-Return>", lambda e: (self.run_code(), "break"))

        # Status bar
        self.status = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def setup_syntax_highlighting(self):
        try:
            from idlelib.colorizer import ColorDelegator
            from idlelib.percolator import Percolator
            cd = ColorDelegator()
            Percolator(self.code_text).insertfilter(cd)
        except Exception:
            # Fallback simple highlighting
            self.code_text.tag_configure("keyword", foreground="#0000FF")
            self.code_text.tag_configure("string", foreground="#008000")
            
    def load_example(self):
        # Load built-in sphere primitive
        try:
            sphere = self.loader.loadModel("models/sphere")
            if sphere:
                sphere.reparentTo(self.scene)
                sphere.setPos(0, 0, 0)
                sphere.setScale(1)
                sphere.setColor(0, 1, 0, 1)  # Green for initial visibility
                print("Initial sphere loaded successfully.")
            else:
                print("Failed to load initial sphere model.")
        except Exception as e:
            print(f"Error loading initial sphere: {e}")

    def update_loop(self, task):
        self.root.update_idletasks()
        return task.cont
        

    def clear_all(self):
        # Clear scene
        children = list(self.scene.getChildren())
        for child in children:
            if isinstance(child, Actor):
                child.cleanup()
            if type(child)==type(NodePath()):
                child.removeNode()
            del child
            del children
        self.status.set("Status: Scene cleared")
        print("Scene cleared.")
        # Clear all children of aspect2d
        for child in aspect2d.getChildren():
            child.removeNode()
        print("Gui cleared.")
    
    def on_clear(self):
        self.clear_all()

    def on_run(self):
        code = self.code_text.get("1.0", tk.END).strip()
        if not code:
            self.status.set("Status: No code to execute")
            messagebox.showwarning("Warning", "No code to execute.")
            return

        try:
            # Clear previous content
            self.clear_all()
            #self.scene.removeNode()
            #self.scene = self.render.attachNewNode("Scene")
            self.status.set("Status: Executing code...")

            local_dict = {
                'loader': self.loader,
                'scene': self.scene,
                'base': self,
                'render': self.render,
                'camera': self.camera,
                'NodePath': NodePath,
                'Vec3': Vec3,
                'LPoint3f': LPoint3f,
            }
            # Execute user code
            #print("Executing code:\n", code)
            exec(code, globals(), local_dict)
            print("Code executed successfully.")

            # Force render
            self.render.clear()
            self.graphicsEngine.renderFrame()
            self.status.set("Status: Code executed successfully")

        except Exception as e:
            error_msg = f"Error executing code:\n{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(error_msg)
            self.status.set(f"Status: Error: {str(e)}")
            messagebox.showerror("Execution Error", error_msg)

if __name__ == "__main__":
    try:
        app = LiveCoder()
        app.run()
    except Exception as e:
        print(f"Startup error: {e}")
        traceback.print_exc()
        sys.exit(1)