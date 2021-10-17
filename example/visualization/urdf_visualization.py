import os, sys
pykin_path = os.path.abspath(os.path.dirname(__file__)+"../../" )
sys.path.append(pykin_path)

import sys
file_path = '../../asset/urdf/baxter/baxter.urdf'
if len(sys.argv) > 1:
    robot_name = sys.argv[1]
    file_path = '../../asset/urdf/' + robot_name + '/' + robot_name + '.urdf'

if "baxter" in file_path:
    from pykin.robots.bimanual import Bimanual
    robot = Bimanual(file_path)
else:
    from pykin.robots.single_arm import SingleArm
    robot = SingleArm(file_path)
from pykin.utils import plot_utils as plt


fig, ax = plt.init_3d_figure("URDF")

# For Baxter robots, the name argument to the plot_robot function must be baxter.
plt.plot_robot(robot, 
               ax=ax, 
               visible_visual=False, 
               visible_collision=False, 
               mesh_path='../../asset/urdf/baxter/')
plt.show_figure()