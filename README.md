# scene_maker_panda3d
A simple scene maker for panda3d

## features
1. move using wasd keys
2. load and transform models live
3. easy shortcut keys

![Screenshot of window](Screenshot.jpg)

## shortcuts

### mouse controls
right click and drag to view 3d scene

### keyboard shortcuts

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
1. model files should loaded from current relative path. when loading from outside of current folder, there is a error occurs
2. when clicking on 'remove animation' in GUI, animation names are not immediately removed, but it will not shown next restart.

### Disclaimer
1. the functionalities used in this program may not represent full or true functionalities of panda3d engine. some functions may partially used. some may twisted for specific use cases. for true explanations, refer panda3d documentation.
2. all assets used in this program are freely obtained from various sources. see references section.

### References
1. https://docs.panda3d.org/1.10/python/more-resources/samples/roaming-ralph#roaming-ralph

2. https://www.poliigon.com/texture/flat-grass-texture/4585

3. https://ambientcg.com/view?id=DaySkyHDRI059A
