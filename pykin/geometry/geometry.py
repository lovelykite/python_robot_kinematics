from pykin.kinematics.transform import Transform


class Visual:
    """
    class of Visual

    Args:
        offset (Transform): visual offset
        geom_type (str): visual type (box, cylinder, spehre, mesh)
        geom_param (dict): visual parameters 
    """
    TYPES = ['box', 'cylinder', 'sphere', 'mesh']
    def __init__(
        self, 
        offset=Transform(), 
        geom_type=None, 
        geom_param=None
    ):
        self.offset = offset
        self.gtype = geom_type
        self.gparam = geom_param

    def __repr__(self):
        return f"""Visual(offset={self.offset},
                           geom_type={self.gtype}, 
                           geom_param={self.gparam})"""

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = Transform(offset.rot, offset.pos)


class Collision:
    """
    class of Collision

    Args:
        offset (Transform): collision offset
        geom_type (str): collision type (box, cylinder, spehre, mesh)
        geom_param (dict): collision parameters 
    """
    TYPES = ['box', 'cylinder', 'sphere', 'mesh']
    def __init__(
        self, 
        offset=Transform(), 
        geom_type=None, 
        geom_param=None
    ):
        self.offset = offset
        self.gtype = geom_type
        self.gparam = geom_param

    def __repr__(self):
        return f"""Collision(offset={self.offset},
                              geom_type={self.gtype}, 
                              geom_param={self.gparam})"""

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, offset):
        self._offset = Transform(offset.rot, offset.pos)