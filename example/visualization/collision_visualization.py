import sys

from pykin.robots.bimanual import Bimanual
from pykin.utils import plot_utils as plt

file_path = '../../asset/urdf/baxter/baxter.urdf'

if len(sys.argv) > 1:
    robot_name = sys.argv[1]
    file_path = '../../asset/urdf/' + robot_name + '/' + robot_name + '.urdf'
robot = Bimanual(file_path)

if "baxter" in file_path:
    from pykin.robots.bimanual import Bimanual
    robot = Bimanual(file_path)
else:
    from pykin.robots.single_arm import SingleArm
    robot = SingleArm(file_path)

fig, ax = plt.init_3d_figure("URDF")

"""
Only baxter and sawyer robots can see collisions.
It is not visible unless sphere, cylinder, and box are defined in collision/geometry tags in urdf.
"""
# If visible_collision is True, visualize collision
plt.plot_robot(robot, 
               ax=ax, 
               visible_collision=True)
ax.legend()
plt.show_figure()