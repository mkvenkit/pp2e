"""
boids

Loops vs. Numpy

Author: Mahesh Venkitachalam
"""

import math 
import numpy as np
from scipy.spatial.distance import squareform, pdist
from timeit import timeit

N = 100
width, height = 640, 480
pos = np.array(list(zip(width*np.random.rand(N), height*np.random.rand(N))))

def test1(pos, radius):
    # fill output with zeros
    vel = np.zeros(2*N).reshape(N, 2)
    # for each pos
    for (i1, p1) in enumerate(pos):
        # velocity contribution
        val = np.array([0.0, 0.0])
        # for each other pos
        for (i2, p2) in enumerate(pos):
            if i1 != i2:
                # calculate distance from p1
                dist = math.sqrt((p2[0]-p1[0])*(p2[0]-p1[0]) + 
                                 (p2[1]-p1[1])*(p2[1]-p1[1]))
                # apply threshold
                if dist < radius:
                    val += (p2 - p1)
        # set velocity
        vel[i1] = val
    # return computed velocity
    return vel

def test2(pos, radius):
    # get distance matrix
    distMatrix = squareform(pdist(pos))
    # apply threshold
    D = distMatrix < radius
    # compute velocity
    vel = pos*D.sum(axis=1).reshape(N, 1) - D.dot(pos)
    return vel

def main():    
    print(timeit('test1(pos, 100)', 'from test import test1, N, pos, width, height', number=100))
    print(timeit('test2(pos, 100)', 'from test import test2, N, pos, width, height', number=100))

if __name__ == '__main__':
    main()