from direct.showbase.ShowBase import ShowBase
from panda3d.core import GraphicsOutput, Texture, FrameBufferProperties, WindowProperties
from panda3d.core import Shader


class MyGame(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        # Create a framebuffer with floating-point precision
        fb_props = FrameBufferProperties()
        fb_props.setFloatColor(True)  # Enable floating-point color buffer
        fb_props.setRgbaBits(16, 16, 16, 16)  # Use 16-bit or 32-bit per channel
        fb_props.setDepthBits(24)  # Optional: Depth buffer precision

        # Set up window properties (optional, match main window size)
        win_props = WindowProperties()
        win_props.setSize(self.win.getXSize(), self.win.getYSize())
        
        # Create an offscreen buffer
        self.hdr_buffer = self.graphicsEngine.makeOutput(
            pipe=self.pipe,              # Graphics pipe
            name="hdr_buffer",           # Buffer name
            sort=-2,                     # Render priority
            fb_prop=fb_props,           # Framebuffer properties
            win_prop=win_props,         # Window properties
            flags=GraphicsOutput.RTMBindOrCopy,  # Render mode
            gsg=self.win.getGsg(),       # Graphics state guardian
            host=self.win                # Host window (use self.win, not getWindowHandle())        
            )

        # Set up a texture to store the HDR render
        self.hdr_texture = Texture()
        self.hdr_texture.setFormat(Texture.F_rgba16)  # 16-bit float per channel
        self.hdr_buffer.addRenderTexture(
            self.hdr_texture, GraphicsOutput.RTM_copy_texture
        )

        # Set up a camera for the buffer
        self.hdr_camera = self.makeCamera(self.hdr_buffer)
        self.hdr_camera.reparentTo(self.render)

        # Load a scene (example)
        self.scene = self.loader.loadModel("models/environment")
        self.scene.reparentTo(self.render)


        # Bind a key to save the HDR image
        self.accept("s", self.save_hdr_image)

    def save_hdr_image(self):
        # Save the HDR texture to a file
        self.hdr_texture.write("output.hdr")
        print("HDR image saved as output.hdr")

app = MyGame()
app.run()