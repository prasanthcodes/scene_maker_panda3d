# Scene Maker Panda3D
A simple scene maker for panda3d

## features
1. Move using WASD keys
2. Load and transform models in real-time
3. Easy-to-use shortcut keys

![Screenshot of window](Screenshot.jpg)

## Shortcuts

### Mouse controls
Right click and drag to view the 3D scene

### Keyboard shortcuts

w - move forward <br/>
s - move backward <br/>
a - move left <br/>
d - move right <br/> <br/>

q - change property <br/>
z - switch models <br/> <br/>

b - gravity on <br/>
o - load model <br/>
c - set camera position to the center of current selected model <br/>
v - camera look at current selected model <br/>
m - to hide all GUI <br/> <br/>

r - x increase <br/>
f - x decrease <br/>
t - y increase <br/>
g - y decrease <br/>
y - z increase <br/>
h - z decrease <br/> <br/>

delete - delete the current model <br/>

### Notes
1. Model files should be loaded from the current relative path. When loading from the outside current folder, there is an error occurs.
2. when clicking on "remove animation" in GUI, animation names are not immediately removed, but they will not appear after the next restart.

### Disclaimer
1. The functionalities used in this program may not represent the full or true capabilities of Panda3D engine. Some functions may partially used. Some may twisted for specific use cases. For true details, refer Panda3D documentation.
2. All assets used in this program are freely obtained from various sources. See the References section.

### References
1. https://docs.panda3d.org/1.10/python/more-resources/samples/roaming-ralph#roaming-ralph

2. https://www.poliigon.com/texture/flat-grass-texture/4585

3. https://ambientcg.com/view?id=DaySkyHDRI059A
