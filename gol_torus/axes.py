"""
axes.py

Python OpenGL program that draws XYZ axes

Author: Mahesh Venkitachalam
"""

import OpenGL
from OpenGL.GL import *

import numpy as np  
import math, sys, os
import glutils

import glfw


strVS = """
#version 330 core

in vec3 aVert;
in vec3 aCol;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

out vec4 vColor;

void main() {
  // transform vertex
  gl_Position = uPMatrix * uMVMatrix * vec4(aVert, 1.0); 

  vColor = vec4(aCol.rgb, 1.0); 
}
"""
strFS = """
#version 330 core

in vec4 vColor;
out vec4 fragColor;

void main() {
  fragColor = vColor;
}
"""

class Axes3D:    
    """ OpenGL 3D scene class"""
    # initialization
    def __init__(self, axes_len):
        # create shader
        self.program = glutils.loadShaders(strVS, strFS)

        glUseProgram(self.program)

        self.pMatrixUniform = glGetUniformLocation(self.program, 
                                                   b'uPMatrix')
        self.mvMatrixUniform = glGetUniformLocation(self.program, 
                                                  b'uMVMatrix')
       
        # axis length 
        self.axes_len = axes_len

        # create axes geometry 
        (vertices, colours) = self.create_axes(15)
    
        #print(vertices.shape)
        #print(colours.shape)

        # set up vertex array object (VAO)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        # vertices
        self.vertexBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexBuffer)
        # set buffer data 
        glBufferData(GL_ARRAY_BUFFER, 4*len(vertices), vertices, 
                     GL_STATIC_DRAW)

        # colors
        self.colorBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.colorBuffer)
        # set buffer data 
        glBufferData(GL_ARRAY_BUFFER, 4*len(colours), colours, 
                     GL_STATIC_DRAW)

        # get locations
        self.vertLoc = glGetAttribLocation(self.program, b"aVert")
        self.colLoc = glGetAttribLocation(self.program, b"aCol")

        # enable vertex arrays
        glEnableVertexAttribArray(self.vertLoc)
        # bind
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexBuffer)
        # set buffer data pointer
        glVertexAttribPointer(self.vertLoc, 3, GL_FLOAT, GL_FALSE, 0, None)
        # enable vertex arrays
        glEnableVertexAttribArray(self.colLoc)
        # bind
        glBindBuffer(GL_ARRAY_BUFFER, self.colorBuffer)
        # set buffer data pointer
        glVertexAttribPointer(self.colLoc, 3, GL_FLOAT, GL_FALSE, 0, None)

        # unbind VAO
        glBindVertexArray(0)
        
    def create_axes(self, axes_len):
        # vertices 
        vertices = np.array([   0.0, 0.0, 0.0, axes_len, 0.0, 0.0,
                                0.0, 0.0, 0.0, 0.0, axes_len, 0.0,
                                0.0, 0.0, 0.0, 0.0, 0.0, axes_len],
                            np.float32)

        # colours
        colours = np.array([ 1.0, 0.0, 0.0, 1.0, 0.0, 0.0,
                            0.0, 1.0, 0.0, 0.0, 1.0, 0.0,
                            0.0, 0.0, 1.0, 0.0, 0.0, 1.0],
                            np.float32)

        return (vertices, colours)

    # render 
    def render(self, pMatrix, mvMatrix):        
        # use shader
        glUseProgram(self.program)
        
        # set proj matrix
        glUniformMatrix4fv(self.pMatrixUniform, 1, GL_FALSE, pMatrix)

        # set modelview matrix
        glUniformMatrix4fv(self.mvMatrixUniform, 1, GL_FALSE, mvMatrix)

        # bind VAO
        glBindVertexArray(self.vao)
        # draw        
        glPointSize(10)
        glDrawArrays(GL_LINES, 0, 6)
    
        # unbind VAO
        glBindVertexArray(0)

        #glUseProgram(0)

    
