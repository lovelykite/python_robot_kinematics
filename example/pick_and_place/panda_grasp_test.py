import numpy as np
import trimesh
import sys, os

pykin_path = os.path.dirname(os.path.dirname(os.getcwd()))
sys.path.append(pykin_path)

from pykin.robots.single_arm import SingleArm
from pykin.kinematics.transform import Transform
from pykin.collision.collision_manager import CollisionManager
from pykin.utils.task_utils import PnPManager
from pykin.utils.obstacle_utils import Obstacle
from pykin.utils.collision_utils import apply_robot_to_collision_manager
import pykin.utils.plot_utils as plt

fig, ax = plt.init_3d_figure(figsize=(10,6), dpi=120)

file_path = '../../asset/urdf/panda/panda.urdf'
robot = SingleArm(file_path, Transform(rot=[0.0, 0.0, 0.0], pos=[0, 0, 0.913]))
robot.setup_link_name(eef_name="panda_right_hand")

init_qpos = [0.0, np.pi/6, 0.0, -np.pi*12/24, 0.0, np.pi*5/8,0.0]
fk = robot.forward_kin(np.array(init_qpos))

mesh_path = pykin_path+"/asset/urdf/panda/"
c_manager = CollisionManager(mesh_path)
c_manager = apply_robot_to_collision_manager(c_manager, robot, fk, geom="collision")
c_manager.filter_contact_names(robot, fk)

obs = Obstacle()
o_manager = CollisionManager()
obs_pos1 = Transform(np.array([0.6, 0, 0.78]))
obs_pos2 = Transform(np.array([0.4, 0.24, 0.0]))

obj_mesh1 = trimesh.load(pykin_path+'/asset/objects/meshes/can.stl')
obj_mesh2 = trimesh.load(pykin_path+'/asset/objects/meshes/custom_table.stl')
obj_mesh2.apply_scale(0.01)
# print(obj_mesh1.bounding_box.extents)
# print(obj_mesh2.bounding_box.extents)

obs(name="can", gtype="mesh", gparam=obj_mesh1, transform=obs_pos1)
obs(name="table", gtype="mesh", gparam=obj_mesh2, transform=obs_pos2)
o_manager.add_object("can", gtype="mesh", gparam=obj_mesh1, transform=obs_pos1.h_mat)
o_manager.add_object("table", gtype="mesh", gparam=obj_mesh2, transform=obs_pos2.h_mat)
plt.plot_mesh(ax=ax, mesh=obj_mesh1, A2B=obs_pos1.h_mat, alpha=0.2)
# plt.plot_mesh(ax=ax, mesh=obj_mesh2, A2B=Transform(pos=obs_pos2).h_mat, alpha=0.2)

pnp = PnPManager(gripper_max_width=0.08, self_c_manager=c_manager, obstacle_c_manager=o_manager)



# pnp.get_only_gripper()
# post_transforms, pre_transforms = pnp.get_all_grasp_transforms(robot, obj_mesh1, obs_pos1.h_mat, 0.08, 0.05, 5)

# eef_pose = robot.get_eef_pose(post_transforms)
# pre_eef_pose = robot.get_eef_pose(pre_transforms)

# qpos = robot.get_result_qpos(init_qpos, eef_pose)
# pre_qpos = robot.get_result_qpos(init_qpos, pre_eef_pose)
# transforms = robot.forward_kin(qpos)
# pre_transforms = robot.forward_kin(pre_qpos)

# gripper_name = ["right_gripper", "leftfinger", "rightfinger"]
# pnp.visualize_grasp_pose(ax)
# pnp.visualize_robot(ax, robot, transforms, mesh_path, gripper_name , 0.3, True)
# pnp.visualize_robot(ax, robot, pre_transforms, mesh_path, gripper_name,1, True)
# pnp.visualize_axis(ax, transforms, "panda_right_hand")
# pnp.visualize_axis(ax, pre_transforms, "panda_right_hand")

# plt.show_figure()

