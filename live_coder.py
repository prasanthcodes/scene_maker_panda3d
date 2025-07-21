import os
import sys
import builtins

from direct.showbase.ShowBase import ShowBase
from panda3d.core import NodePath
from panda3d.core import *

# Reset ShowBase so updated code has a clean slate.
def reset():
    # Needs a lot more resetting.
    # Like aspect2d, render2d, accept, etc.
    print("Resetting showbase...")
    builtins.render = base.render = NodePath("render")
    """
    for task in base.task_mgr.getTasks():
        if not task in base.base_tasks:
            task.remove()
    base.camera.reparent_to(base.render)
    base.cam.reparent_to(base.camera)
    base.cam.clear_transform()
    base.camera.clear_transform()
    base.win.set_clear_color((0.1,0.1,0.1,1))
    """


#
def update(filename, task):
    stamp = os.stat(filename).st_mtime
    if stamp != base.old_stamp:
        print("File modified.")
        base.old_stamp = stamp
        reset()
        try:
            print("Executing.")
            exec(open(filename, 'r').read())
        except Exception as e:
            print(e)
            base.win.set_clear_color((0.3,0.1,0.1,1))
        finally:
            print("Execution succesful.\n")
    return task.cont


# Wrap the task in a task that looks for exceptions.
# This way ShowBase keeps running even when adding a broken task.
def new_add(func, name=None, sort=None, extraArgs=[], priority=None, uponDeath=None, appendTask=False, taskChain=None, owner=None, delay=None):
    def task(func, extraArgs, task=None):
        try:
            if task:
                return func(*extraArgs, task)
            else:
                return func(*extraArgs)
        except Exception as e:
            print("Error in task: "+str(func), e)
            return task.done
    base.task_mgr.og_add(task, name, sort, extraArgs=[func, extraArgs], priority=priority, uponDeath=uponDeath, appendTask=True, taskChain=taskChain, owner=owner, delay=delay)


base = ShowBase()
base.old_stamp = 0

try:
    file = sys.argv[1]
    dirname = os.path.dirname(file)
    basename = os.path.basename(file)
    sys.path.append(dirname)
except:
    raise NameError("No filename.")

base.task_mgr.add(update, extraArgs=[file], appendTask=True)
base.base_tasks = []
for task in base.task_mgr.getTasks():
    base.base_tasks.append(task)
base.task_mgr.og_add = base.task_mgr.add
base.task_mgr.add = new_add

base.run()