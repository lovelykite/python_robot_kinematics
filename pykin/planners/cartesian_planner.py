import numpy as np
import signal

def handler(signum, frame):
    exit()
# Set the signal handler
signal.signal(signal.SIGINT, handler)

from pykin.planners.planner import Planner
from pykin.utils.error_utils import OriValueError, CollisionError
from pykin.utils.kin_utils import ShellColors as sc
from pykin.utils.log_utils import create_logger
import pykin.utils.transform_utils as t_utils
import pykin.utils.kin_utils as k_utils
import pykin.kinematics.jacobian as jac

logger = create_logger('Cartesian Planner', "debug",)

class CartesianPlanner(Planner):
    """
    path planner in Cartesian space

    Args:
        robot(SingleArm or Bimanual): The manipulator robot type is SingleArm or Bimanual
    """
    def __init__(
        self,
        robot,
        self_collision_manager=None,
        obstacle_collision_manager=None,
        n_step=500,
        dimension=7,
        waypoint_type="Linear"
    ):
        super(CartesianPlanner, self).__init__(robot, self_collision_manager, dimension)
        self.obstacle_collision_manager = obstacle_collision_manager
        self.n_step = n_step
        self.waypoint_type = waypoint_type
        self.eef_name = self.robot.eef_name
        self.arm = None
        self._dimension = dimension

        super()._setup_q_limits()
        super()._setup_eef_name()
    

    def __repr__(self):
        return 'pykin.planners.cartesian_planner.{}()'.format(type(self).__name__)
        
    def get_path_in_joinst_space(
        self, 
        current_q=None,
        goal_pose=None,
        waypoints=None,
        resolution=1, 
        damping=0.5,
        epsilon=1e-12,
        pos_sensitivity = 0.03,
        is_slerp=False
    ):
        self._cur_qpos = super()._change_types(current_q)
        self._goal_pose = super()._change_types(goal_pose)
        is_get_path = False
        init_fk = self.robot.kin.forward_kinematics(self.robot.desired_frames, self._cur_qpos)
        self._cur_pose = self.robot.get_eef_pose(init_fk)

        if waypoints is None:
            waypoints = self.genearte_waypoints(is_slerp)

        paths, target_posistions = self._compute_path_and_target_pose(waypoints, resolution, damping, epsilon, pos_sensitivity)
        
        if paths is not None:
            is_get_path = True
        
        return paths, is_get_path, target_posistions

    def _compute_path_and_target_pose(
        self, 
        waypoints, 
        resolution, 
        damping, 
        epsilon,
        pos_sensitivity
    ):
        cnt = 0
        total_cnt = 10

        while True:
            cnt += 1
            cur_fk = self.robot.kin.forward_kinematics(self.robot.desired_frames, self._cur_qpos)

            current_transform = cur_fk[self.eef_name].h_mat
            eef_position = cur_fk[self.eef_name].pos

            paths = [self._cur_qpos]
            target_posistions = [eef_position]

            for step, (pos, ori) in enumerate(waypoints):
                target_transform = t_utils.get_h_mat(pos, ori)
                err_pose = k_utils.calc_pose_error(target_transform, current_transform, epsilon) 
                J = jac.calc_jacobian(self.robot.desired_frames, cur_fk, self._dimension)
                Jh = np.dot(np.linalg.pinv(np.dot(J.T, J) + damping**2 * np.identity(self._dimension)), J.T)

                dq = damping * np.dot(Jh, err_pose)
                self._cur_qpos = np.array([(self._cur_qpos[i] + dq[i]) for i in range(self._dimension)]).reshape(self._dimension,)

                collision_free = self.collision_free(self._cur_qpos, visible_name=False)

                if not collision_free:
                    continue

                if not self._check_q_in_limits(self._cur_qpos):
                    continue

                cur_fk = self.robot.kin.forward_kinematics(self.robot.desired_frames, self._cur_qpos)
                current_transform = cur_fk[self.robot.eef_name].h_mat

                if step % (1/resolution) == 0 or step == len(waypoints)-1:
                    paths.append(self._cur_qpos)
                    target_posistions.append(pos)

            err = t_utils.compute_pose_error(self._goal_pose[:3], cur_fk[self.eef_name].pos)

            if err < pos_sensitivity:
                logger.info(f"Generate Path Successfully!! Error is {err:6f}")
                break

            if cnt > total_cnt:
                logger.error(f"Failed Generate Path.. The number of retries of {cnt} exceeded")
                paths, target_posistions = None, None
                break

            logger.error(f"Failed Generate Path.. Position Error is {err:6f}")
            print(f"{sc.BOLD}Retry Generate Path, the number of retries is {cnt}/{total_cnt} {sc.ENDC}\n")
            
        return paths, target_posistions

    def collision_free(self, new_q, visible_name=False):
        """
        Check collision free between robot and obstacles
        If visible name is True, return collision result and collision object names
        otherwise, return only collision result

        Args:
            new_q(np.array): new joint angles
            visible_name(bool)

        Returns:
            result(bool): If collision free, return True
            names(set of 2-tup): The set of pairwise collisions. 
        """

        if self.self_collision_manager is None:
            return True

        transformations = self._get_transformations(new_q)
        for link, transformations in transformations.items():
            if link in self.self_collision_manager._objs:
                transform = transformations.h_mat
                self.self_collision_manager.set_transform(name=link, transform=transform)
        is_collision = self.self_collision_manager.in_collision_internal(return_names=False, return_data=False)

        name = None
        if visible_name:
            if is_collision:
                return False, name
            return True, name

        if is_collision:
            return False
        return True

    # TODO
    # generate cubic, circular waypoints
    def genearte_waypoints(self, is_slerp):
        if self.waypoint_type == "Linear":
            waypoints = [path for path in self._get_linear_path(is_slerp)]
        if self.waypoint_type == "Cubic":
            pass
        if self.waypoint_type == "Circular":
            pass
        return waypoints

    def get_waypoints(self):
        return self.waypoints

    def _change_pose_type(self, pose):
        ret = np.zeros(7)
        ret[:3] = pose[:3]
        
        if isinstance(pose, (list, tuple)):
            pose = np.asarray(pose)
        ori = pose[3:]

        if ori.shape == (3,):
            ori = t_utils.get_quaternion_from_rpy(ori)
            ret[3:] = ori
        elif ori.shape == (4,):
            ret[3:] = ori
        else:
            raise OriValueError(ori.shape)

        return ret

    def _get_linear_path(self, is_slerp):
        for step in range(1, self.n_step + 1):
            delta_t = step / self.n_step
            pos = t_utils.get_linear_interpoation(self._cur_pose[:3], self._goal_pose[:3], delta_t)
            ori = self._cur_pose[3:]
            if is_slerp:
                ori = t_utils.get_quaternion_slerp(self._cur_pose[3:], self._goal_pose[3:], delta_t)

            yield (pos, ori)

    def _get_cubic_path(self):
        pass

    def _get_cicular_path(self):
        pass

    # @property
    # def dimension(self):
    #     return self._dimension

    # @dimension.setter
    # def dimension(self, dimesion):
    #     self._dimension = dimesion