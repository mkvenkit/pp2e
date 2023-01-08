"""
gol_torus.py

Python OpenGL program that displays a torus.

Author: Mahesh Venkitachalam
"""

import OpenGL
from OpenGL.GL import *

import numpy, math, sys, os
import argparse
import glutils

import glfw

from torus import Torus
from camera import OrbitCamera
from gol import GOL

class RenderWindow:
    """GLFW Rendering window class"""
    def __init__(self, glider):

        # save current working directory
        cwd = os.getcwd()

        # initialize glfw - this changes cwd
        glfw.glfwInit()
        
        # restore cwd
        os.chdir(cwd)

        # version hints
        glfw.glfwWindowHint(glfw.GLFW_CONTEXT_VERSION_MAJOR, 3)
        glfw.glfwWindowHint(glfw.GLFW_CONTEXT_VERSION_MINOR, 3)
        glfw.glfwWindowHint(glfw.GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE)
        glfw.glfwWindowHint(glfw.GLFW_OPENGL_PROFILE, 
                            glfw.GLFW_OPENGL_CORE_PROFILE)
    
        # make a window
        self.width, self.height = 640, 480
        self.aspect = self.width/float(self.height)
        self.win = glfw.glfwCreateWindow(self.width, self.height, 
                                         b'gol_torus')
        # make context current
        glfw.glfwMakeContextCurrent(self.win)
        
        # initialize GL
        glViewport(0, 0, self.width, self.height)
        glEnable(GL_DEPTH_TEST)
        #glClearColor(0.2, 0.2, 0.2,1.0)
        glClearColor(0.11764706, 0.11764706, 0.11764706, 1.0)

        # set window callbacks
        glfw.glfwSetMouseButtonCallback(self.win, self.onMouseButton)
        glfw.glfwSetKeyCallback(self.win, self.onKeyboard)

        # create 3D
        NX = 64
        NY = 64
        R = 4.0
        r = 1.0
        self.torus = Torus(R, r, NX, NY)
        self.gol = GOL(NX, NY, glider)

        # create a camera
        self.camera = OrbitCamera(5.0, 10.0)

        # exit flag
        self.exitNow = False

        # rotation flag
        self.rotate = True

        # skip count
        self.skip = 0
        
    def onMouseButton(self, win, button, action, mods):
        #print 'mouse button: ', win, button, action, mods
        pass

    def onKeyboard(self, win, key, scancode, action, mods):
        #print 'keyboard: ', win, key, scancode, action, mods
        if action == glfw.GLFW_PRESS:
            # ESC to quit
            if key == glfw.GLFW_KEY_ESCAPE: 
                self.exitNow = True
            elif key == glfw.GLFW_KEY_R:
                self.rotate = not self.rotate 
    

    def run(self):
        # initializer timer
        glfw.glfwSetTime(0)
        t = 0.0
        while not glfw.glfwWindowShouldClose(self.win) and not self.exitNow:
            # update every x seconds
            currT = glfw.glfwGetTime()
            if currT - t > 0.05:
                # update time
                t = currT

                # set viewport
                self.width, self.height = glfw.glfwGetFramebufferSize(self.win)
                self.aspect = self.width/float(self.height)
                glViewport(0, 0, self.width, self.height)

                # clear
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                
                # build projection matrix
                pMatrix = glutils.perspective(60.0, self.aspect, 0.1, 100.0)
                
                mvMatrix = glutils.lookAt(self.camera.eye, self.camera.center, 
                                          self.camera.up)
                
                # render
                self.torus.render(pMatrix, mvMatrix)
                
                # step 
                if self.rotate: 
                    self.step()

                glfw.glfwSwapBuffers(self.win)
                # Poll for and process events
                glfw.glfwPollEvents()
        # end
        glfw.glfwTerminate()

    def step(self):    

        if self.skip == 9:
            # update GOL
            self.gol.update()
            colors = self.gol.get_colors()
            self.torus.set_colors(colors)
            # step 
            self.torus.step()
            # reset 
            self.skip = 0
        
        # update skip
        self.skip += 1
        # rotate camera
        self.camera.rotate()

# main() function
def main():
    print("Starting GOL. Press ESC to quit.")
    # parse arguments
    parser = argparse.ArgumentParser(description="Runs Conway's Game of Life simulation on a Torus.")
    # add arguments
    parser.add_argument('--glider', action='store_true', required=False)
    args = parser.parse_args()

    # set args
    glider = False
    if args.glider:
        glider = True
        
    rw = RenderWindow(glider)
    rw.run()

# call main
if __name__ == '__main__':
    main()
