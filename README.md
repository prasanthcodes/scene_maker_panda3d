# Scene Maker Panda3D
A simple scene maker for panda3d

## Features
1. Move using WASD keys
2. Load and transform models in real-time
3. Easy-to-use shortcut keys

![Screenshot of window](Screenshot.jpg)

## Shortcuts

### Mouse Controls
Right click and drag to view the 3D scene

### Keyboard Shortcuts

W - Move Forward <br/>
S - Move Backward <br/>
A - Move Left <br/>
D - Move Right <br/> <br/>

Q - Change property <br/>
Z - Switch models <br/> <br/>

B - Gravity on <br/>
O - Load model <br/>
C - Set camera position to the center of current selected model <br/>
V - Camera look at current selected model <br/>
M - Hide all GUI <br/> <br/>

R - X increase <br/>
F - X decrease <br/>
T - Y increase <br/>
G - Y decrease <br/>
Y - Z increase <br/>
H - Z decrease <br/> <br/>

Delete - Delete the current model <br/>

### Notes
1. Model files should be loaded from the current relative path. When loading from the outside current folder, there is an error occurs.
2. when clicking on "Remove Animation" in GUI, animation names are not immediately removed, but they will not appear after the next restart.

### Disclaimer
1. The functionalities used in this program may not represent the full or true capabilities of Panda3D engine. Some functions may partially used. Some may twisted for specific use cases. For true details, refer Panda3D documentation.
2. All assets used in this program are freely obtained from various sources. See the References section.

### References
1. https://docs.panda3d.org/1.10/python/more-resources/samples/roaming-ralph#roaming-ralph

2. https://www.poliigon.com/texture/flat-grass-texture/4585

3. https://ambientcg.com/view?id=DaySkyHDRI059A
