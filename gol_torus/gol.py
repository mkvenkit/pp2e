"""
    gol.py

    Implements Conway's Game of Life.

    Author: Mahesh Venkitachalam
    
"""

import numpy as np

class GOL:
    """GOL - class that implements Conway's Game of Life
    """
    def __init__(self, NX, NY, glider):
        """GOL constructor
        """
        # a grid of NX x NY random values
        self.NX, self.NY = NX, NY
        if glider:
            self.addGlider(1, 1, NX, NY)
        else:
            self.grid = np.random.choice([1, 0], NX * NY, p=[0.2, 0.8]).reshape(NX, NY) 

    def addGlider(self, i, j, NX, NY):
        """adds a glider with top left cell at (i, j)"""
        self.grid = np.zeros(NX * NY).reshape(NX, NY)
        glider = np.array([[0,    0, 1], 
                        [1,  0, 1], 
                        [0,  1, 1]])
        self.grid[i:i+3, j:j+3] = glider

    def update(self):
        """Update the GOL simulation by one time step.
        """
        # copy grid since we require 8 neighbors for calculation
        # and we go line by line 
        newGrid = self.grid.copy()
        NX, NY = self.NX, self.NY
        for i in range(NX):
            for j in range(NY):
                # compute 8-neghbor sum
                # using toroidal boundary conditions - x and y wrap around 
                # so that the simulaton takes place on a toroidal surface.
                total = (self.grid[i, (j-1) % NY] + self.grid[i, (j+1) % NY] + 
                        self.grid[(i-1) % NX, j] + self.grid[(i+1) % NX, j] + 
                        self.grid[(i-1) % NX, (j-1) % NY] + self.grid[(i-1) % NX, (j+1) % NY] + 
                        self.grid[(i+1) % NX, (j-1) % NY] + self.grid[(i+1) % NX, (j+1) % NY])
                # apply Conway's rules
                if self.grid[i, j]  == 1:
                    if (total < 2) or (total > 3):
                        newGrid[i, j] = 0
                else:
                    if total == 3:
                        newGrid[i, j] = 1
        # update data
        self.grid[:] = newGrid[:]

    def get_colors(self):
        """returns a dictionary of colors
        """
        colors = {}
        c1 = np.array([1.0, 1.0, 1.0], np.float32)
        c2 = np.array([0.0, 0.0, 0.0], np.float32)
        for i in range(self.NX):
            for j in range (self.NY):
                if self.grid[i, j] == 1:
                    colors[(i, j)] = c2
                else :
                    colors[(i, j)] = c1 
        return colors
