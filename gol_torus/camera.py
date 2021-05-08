"""
camera.py

A simple camera class for OpenGL rendering.

Author: Mahesh Venkitachalam
"""

import numpy as np
import math 

class OrbitCamera:
    """helper class for viewing"""
    def __init__(self, height, radius, beta_step=1):
        self.radius = radius
        self.beta = 0
        self.beta_step = beta_step
        self.height = height
        # initial eye vector is (-R, 0, -H)
        rr = radius/math.sqrt(2.0)
        self.eye = np.array([rr, rr, height], np.float32)
        # compute up vector
        self.up = self.__compute_up_vector(self.eye )
        # center is origin 
        self.center = np.array([0, 0, 0], np.float32)

    def __compute_up_vector(self, E):
        """Compute up vector.
        N = (E x k) x E
        """
        # N = (E x k) x E
        Z = np.array([0, 0, 1], np.float32)
        U = np.cross(np.cross(E, Z), E)
        # normalize
        U = U / np.linalg.norm(U)
        return U

    def rotate(self):
        """Rotate by one step and compute new camera parameters."""
        self.beta = (self.beta + self.beta_step) % 360
        # recalculate eye E 
        self.eye = np.array([self.radius*math.cos(math.radians(self.beta)), 
                    self.radius*math.sin(math.radians(self.beta)), 
                    self.height], np.float32)
        # up vector 
        self.up = self.__compute_up_vector(self.eye)

        
