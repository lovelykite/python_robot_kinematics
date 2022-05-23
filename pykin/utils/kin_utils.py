import numpy as np
import time
import trimesh
import pykin.utils.plot_utils as plt

# from pykin.kinematics.transform import Transform

JOINT_TYPE_MAP = {'revolute'  : 'revolute',
                  'fixed'     : 'fixed',
                  'prismatic' : 'prismatic'}

LINK_TYPE_MAP = {'cylinder' : 'cylinder',
                 'sphere'   : 'sphere',
                 'box'      : 'box',
                 'mesh'     : 'mesh'}

LINK_TYPES = ['box', 'cylinder', 'sphere', 'capsule', 'mesh']

class ShellColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    MAGENTA = '\033[95m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def convert_thetas_to_dict(active_joint_names, thetas):
    """
    Check if any pair of objects in the manager collide with one another.
    
    Args:
        active_joint_names (list): actuated joint names
        thetas (sequence of float): If not dict, convert to dict ex. {joint names : thetas}
    
    Returns:
        thetas (dict): Dictionary of actuated joint angles
    """
    if not isinstance(thetas, dict):
        assert len(active_joint_names) == len(thetas
        ), f"""the number of robot joint's angle is {len(active_joint_names)},
                but the number of input joint's angle is {len(thetas)}"""
        thetas = dict((j, thetas[i]) for i, j in enumerate(active_joint_names))
    return thetas


def logging_time(original_fn):
    """
    Decorator to check time of function
    """
    def wrapper_fn(*args, **kwargs):
        start_time = time.time()
        result = original_fn(*args, **kwargs)
        end_time = time.time()
        print(f"WorkingTime[{original_fn.__name__}]: {end_time-start_time:.4f} sec\n")
        return result
    return wrapper_fn

def convert_string_to_narray(str_input):
    """
    Args:
        str_input (str): string

    Returns:
        np.array: Returns string to np.array
    """
    if str_input is not None:
        return np.array([float(data) for data in str_input.split()])


def calc_pose_error(tar_pose, cur_pose, EPS):
    """
    Args:
        tar_pos (np.array): target pose
        cur_pos (np.array): current pose
        EPS (float): epsilon

    Returns:
        np.array: Returns pose error
    """

    pos_err = np.array([tar_pose[:3, -1] - cur_pose[:3, -1]])
    rot_err = np.dot(cur_pose[:3, :3].T, tar_pose[:3, :3])
    w_err = np.dot(cur_pose[:3, :3], rot_to_omega(rot_err, EPS))

    return np.vstack((pos_err.T, w_err))


def rot_to_omega(R, EPS):
    # referred p36
    el = np.array(
            [[R[2, 1] - R[1, 2]],
            [R[0, 2] - R[2, 0]],
            [R[1, 0] - R[0, 1]]]
    )
    norm_el = np.linalg.norm(el)
    if norm_el > EPS:
        w = np.dot(np.arctan2(norm_el, np.trace(R) - 1) / norm_el, el)
    elif (R[0, 0] > 0 and R[1, 1] > 0 and R[2, 2] > 0):
        w = np.zeros((3, 1))
    else:
        w = np.dot(np.pi/2, np.array([[R[0, 0] + 1], [R[1, 1] + 1], [R[2, 2] + 1]]))
    return w


def limit_joints(joint_angles, lower, upper):
    """
    Set joint angle limit

    Args:
        joint_angles (sequence of float): joint angles
        lower (sequence of float): lower limit
        upper (sequence of float): upper limit

    Returns:
        joint_angles (sequence of float): Returns limited joint angle 
    """
    if lower is not None and upper is not None:
        for i in range(len(joint_angles)):
            if joint_angles[i] < lower[i]:
                joint_angles[i] = lower[i]
            if joint_angles[i] > upper[i]:
                joint_angles[i] = upper[i]
    return joint_angles


def apply_objects_to_scene(trimesh_scene=None, objs=None):
    if trimesh_scene is None:
        trimesh_scene = trimesh.Scene()

    for name, info in objs.items():
        mesh = info.gparam
        color = np.array(info.color)
        mesh.visual.face_colors = color
        trimesh_scene.add_geometry(mesh, transform=info.h_mat)

    return trimesh_scene

def apply_gripper_to_scene(trimesh_scene=None, robot=None):
    if trimesh_scene is None:
        trimesh_scene = trimesh.Scene()

    for link, info in robot.gripper.info.items():
        if info[1] == 'mesh':
            mesh_color = plt.get_mesh_color(robot, link, 'collision')
            if len(info) > 4 :
                mesh_color = info[4]
            mesh = info[2]
            h_mat= info[3]
            mesh.visual.face_colors = mesh_color
            trimesh_scene.add_geometry(mesh, transform=h_mat)

    return trimesh_scene

def apply_robot_to_scene(trimesh_scene=None, robot=None, geom="collision"):
    if trimesh_scene is None:
        trimesh_scene = trimesh.Scene()

    for link, info in robot.info[geom].items():
        mesh = info[2]
        h_mat = info[3]

        if info[1] == "mesh":
            mesh_color = plt.get_mesh_color(robot, link, geom)
            if len(info) > 4:
                mesh_color = info[4]
            print(link, mesh_color)
            mesh.visual.face_colors = mesh_color
            trimesh_scene.add_geometry(mesh, transform=h_mat)
    
        if info[1] == "box":
            box_mesh = trimesh.creation.box(extents=info[2])
            trimesh_scene.add_geometry(box_mesh, transform=h_mat)

        if info[1] == "cylinder":
            capsule_mesh = trimesh.creation.cylinder(height=info[2][0], radius=info[2][1])
            trimesh_scene.add_geometry(capsule_mesh, transform=h_mat)

        if info[1] == "sphere":
            sphere_mesh = trimesh.creation.icosphere(radius=info[2])
            trimesh_scene.add_geometry(sphere_mesh, transform=h_mat)
    return trimesh_scene


def get_mesh_param(link_type):
    file_name = str(link_type.gparam.get('filename'))
    color = link_type.gparam.get('color')
    color = np.array([color for color in color.values()]).flatten()
    return (file_name, color)


def get_cylinder_param(link_type):
    radius = float(link_type.gparam.get('radius'))
    length = float(link_type.gparam.get('length'))
    return (radius, length)


def get_spehre_param(link_type):
    radius = float(link_type.gparam.get('radius'))
    return radius


def get_box_param(link_type):
    size = list(link_type.gparam.get('size'))
    return size