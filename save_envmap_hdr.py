from direct.showbase.ShowBase import ShowBase
from panda3d.core import (
    PNMImage, Camera, PerspectiveLens, NodePath, FrameBufferProperties,
    WindowProperties, DisplayRegion, PandaSystem
)
import numpy as np
import imageio
import os

class EnvMapSaver(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)
        
        # Debug: Print system information
        print(f"Panda3D Version: {PandaSystem.getVersionString()}")
        print(f"Graphics Pipe: {self.pipe.getType().getName()}")
        print(f"Driver Version: {self.pipe.getInterfaceName()}")
        print(f"Default Framebuffer Properties: {FrameBufferProperties.getDefault()}")
        print(f"Main Window Size: {self.win.getXSize()}x{self.win.getYSize()}")
        
        # Check imageio FreeImage plugin
        try:
            imageio.plugins.freeimage.download()
            print("FreeImage plugin is available")
        except Exception as e:
            print(f"Failed to load FreeImage plugin: {e}")
        
        # Set up a simple scene
        self.scene = self.loader.loadModel("models/environment")  # Simple model for testing
        self.scene.reparentTo(self.render)
        self.scene.setPos(0, 0, 0)
        
        # Disable default camera
        self.disableMouse()
        
        # Set up cubemap rendering
        self.setup_cubemap()
        
        # Capture and save the cubemap
        self.capture_cubemap()
        
        # Exit after capturing
        self.taskMgr.stop()
        
    def setup_cubemap(self):
        """Set up six cameras for cubemap faces."""
        self.cubemap_size = 64  # Low resolution for compatibility
        self.buffer = self.win  # Use main window buffer
        print(f"Using buffer: {self.buffer.getType().getName()}, Size: {self.buffer.getXSize()}x{self.buffer.getYSize()}")
        
        # Camera directions for cubemap faces: +X, -X, +Y, -Y, +Z, -Z
        self.cameras = []
        self.display_regions = []
        directions = [
            (90, 0), (-90, 0), (0, 90), (0, -90), (0, 0), (180, 0)
        ]
        
        for i, (h, p) in enumerate(directions):
            # Create camera
            cam = Camera(f"cubemap_cam_{i}")
            lens = PerspectiveLens()
            lens.setFov(90)  # 90-degree FOV for cubemap
            cam.setLens(lens)
            cam_np = NodePath(cam)
            cam_np.setHpr(h, p, 0)
            cam_np.setPos(0, 0, 0)  # Center of the scene
            cam_np.reparentTo(self.render)
            self.cameras.append(cam_np)
        
    def capture_cubemap(self):
        """Capture each cubemap face sequentially using framebuffer."""
        faces = []
        for i in range(6):
            # Clear previous display regions
            for dr in self.display_regions:
                self.buffer.removeDisplayRegion(dr)
            self.display_regions = []
            
            # Create display region for this camera
            dr = self.buffer.makeDisplayRegion((0, 1, 0, 1))
            dr.setCamera(self.cameras[i])
            dr.setActive(True)
            self.display_regions.append(dr)
            
            # Render frame and flush pipeline
            self.graphicsEngine.renderFrame()
            self.graphicsEngine.syncFrame()
            
            # Capture framebuffer
            screenshot = self.buffer.getScreenshot()
            if screenshot is None:
                print(f"Failed to capture framebuffer for face {i}")
                self.buffer.removeDisplayRegion(dr)
                self.display_regions = []
                continue
            
            # Convert Texture to PNMImage
            screenshot_img = PNMImage()
            if not screenshot.store(screenshot_img):
                print(f"Failed to store screenshot to PNMImage for face {i}")
                self.buffer.removeDisplayRegion(dr)
                self.display_regions = []
                continue
            
            img = PNMImage(self.cubemap_size, self.cubemap_size, 4)
            img.copySubImage(screenshot_img, 0, 0, 0, 0, self.cubemap_size, self.cubemap_size)
            
            # Extract pixel data to NumPy array
            data = np.zeros((self.cubemap_size, self.cubemap_size, 4), dtype=np.float32)
            for y in range(self.cubemap_size):
                for x in range(self.cubemap_size):
                    pixel = img.getPixel(x, y)
                    data[y, x] = np.array([pixel[0], pixel[1], pixel[2], pixel[3]], dtype=np.float32) / 255.0
            faces.append(data)
            
            # Clean up display region
            self.buffer.removeDisplayRegion(dr)
            self.display_regions = []
        
        # Save each face as an HDR image
        output_dir = "cubemap_faces"
        os.makedirs(output_dir, exist_ok=True)
        
        for i, face in enumerate(faces):
            # Remove alpha channel
            face = face[:, :, :3]
            
            # Save as HDR using imageio
            output_path = os.path.join(output_dir, f"cubemap_face_{i}.hdr")
            try:
                imageio.imwrite(output_path, face, format="HDR-FI")
                print(f"Saved cubemap face {i} to {output_path}")
            except Exception as e:
                print(f"Failed to save cubemap face {i} as HDR: {e}")
                # Fallback to PNG
                png_path = os.path.join(output_dir, f"cubemap_face_{i}.png")
                try:
                    imageio.imwrite(png_path, (face * 255).astype(np.uint8))
                    print(f"Saved cubemap face {i} as PNG to {png_path}")
                except Exception as e:
                    print(f"Failed to save cubemap face {i} as PNG: {e}")
        
        # Combine faces into a single HDR cubemap (cross layout)
        if faces:
            self.combine_faces_to_cubemap(faces)
        
    def combine_faces_to_cubemap(self, faces):
        """Combine cubemap faces into a single HDR image (cross layout)."""
        # Create a cross layout: 4 faces in a row, 3 in a column
        cross_width = self.cubemap_size * 4
        cross_height = self.cubemap_size * 3
        cross_image = np.zeros((cross_height, cross_width, 3), dtype=np.float32)
        
        # Layout: 
        #   [  ][+Y][  ][  ]
        #   [-X][+Z][-Z][+X]
        #   [  ][-Y][  ][  ]
        placements = [
            (3, 1, 0),  # +X
            (1, 1, 1),  # -X
            (2, 0, 2),  # +Y
            (2, 2, 3),  # -Y
            (2, 1, 4),  # +Z
            (1, 1, 5),  # -Z
        ]
        
        for (x, y, face_idx) in placements:
            if face_idx < len(faces):
                x_start = x * self.cubemap_size
                y_start = y * self.cubemap_size
                cross_image[y_start:y_start+self.cubemap_size, x_start:x_start+self.cubemap_size] = faces[face_idx][:, :, :3]
        
        # Save the combined cubemap
        output_path = "cubemap_cross.hdr"
        try:
            imageio.imwrite(output_path, cross_image, format="HDR-FI")
            print(f"Saved combined cubemap to {output_path}")
        except Exception as e:
            print(f"Failed to save combined cubemap as HDR: {e}")
            # Fallback to PNG
            png_path = "cubemap_cross.png"
            try:
                imageio.imwrite(png_path, (cross_image * 255).astype(np.uint8))
                print(f"Saved combined cubemap as PNG to {png_path}")
            except Exception as e:
                print(f"Failed to save combined cubemap as PNG: {e}")

if __name__ == "__main__":
    try:
        app = EnvMapSaver()
        app.run()
    except Exception as e:
        print(f"Application failed: {e}")