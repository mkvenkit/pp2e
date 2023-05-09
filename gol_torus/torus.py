"""
torus.py

Python OpenGL program that generates a torus.

Author: Mahesh Venkitachalam
"""

import OpenGL
from OpenGL.GL import *

import numpy as np  
import math, sys, os
import glutils

import glfw


strVS = """
#version 410 core

layout(location = 0) in vec3 aVert;
layout(location = 1) in vec3 aColor;
layout(location = 2) in vec3 aNormal;

uniform mat4 uMVMatrix;
uniform mat4 uPMatrix;

flat out vec3 vColor;
out vec3 vNormal;
out vec3 fragPos;

void main() {
  // transform vertex
  gl_Position = uPMatrix * uMVMatrix * vec4(aVert, 1.0); 
  fragPos = aVert;
  vColor = aColor;
  vNormal = aNormal;
}
"""
strFS = """
#version 410 core

flat in vec3 vColor;
in vec3 vNormal;
in vec3 fragPos;

out vec4 fragColor;

void main() {
  vec3 lightPos = vec3(10.0, 10.0, 10.0);
  vec3 lightColor = vec3(1.0, 1.0, 1.0);
  vec3 lightDir = normalize(lightPos - fragPos);
  float diff = max(dot(vNormal, lightDir), 0.0);
  vec3 diffuse = diff * lightColor;
  float ambient = 0.1;
  vec3 result = (ambient + diffuse) * vColor.xyz;
  fragColor = vec4(result, 1.0);
}
"""

class Torus:    
    """ OpenGL 3D scene class"""
    # initialization
    def __init__(self, R, r, NX, NY):
        global strVS, strFS

        # create shader
        self.program = glutils.loadShaders(strVS, strFS)

        glProvokingVertex(GL_FIRST_VERTEX_CONVENTION)

        self.pMatrixUniform = glGetUniformLocation(self.program, 
                                                   b'uPMatrix')
        self.mvMatrixUniform = glGetUniformLocation(self.program, 
                                                  b'uMVMatrix')
       
        # torus geometry 
        self.R = R
        self.r = r
        # grid size 
        self.NX = NX
        self.NY = NY
        # no of points 
        self.N = self.NX
        self.M = self.NY 

        # time
        self.t = 0 

        # compute parameters for glMultiDrawArrays
        M1 = 2*self.M + 2 
        self.first_indices = [2*M1*i for i in range(self.N)]
        self.counts = [2*M1 for i in range(self.N)]

        # colors: {(i, j) : (r, g, b)}
        # with NX * NY entries 
        self.colors_dict = self.init_colors(self.NX, self.NY)
        
        # create an empty array to hold colors
        self.colors = np.zeros((3*self.N*(2*self.M + 2), ), np.float32)

        # get vertices, normals, indices
        vertices, normals = self.compute_vertices()
        self.compute_colors()
        # set up vertex buffer objects
        self.setup_vao(vertices, normals, self.colors)
    
    def init_colors(self, NX, NY):
        """initialise color dictionary
        """
        colors = {}
        c1 = [1.0, 1.0, 1.0]
        for i in range(NX):
            for j in range (NY):
                colors[(i, j)] = c1
        return colors

    def compute_rt(self, R, alpha):
        # compute position of ring 
        Tx = R*math.cos(alpha)
        Ty = R*math.sin(alpha)
        Tz = 0.0

        # rotation matrix
        RM = np.array([
            [math.cos(alpha), -math.sin(alpha), 0.0, 0.0], 
            [math.sin(alpha), math.cos(alpha), 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0], 
            [0.0, 0.0, 0.0, 1.0]
            ], dtype=np.float32)

        # translation matrix
        TM = np.array([
            [1.0, 0.0, 0.0, Tx], 
            [0.0, 1.0, 0.0, Ty], 
            [0.0, 0.0, 1.0, Tz], 
            [0.0, 0.0, 0.0, 1.0]
            ], dtype=np.float32)

        return (RM, TM)

    def compute_pt(self, r, theta, RM, TM):
        # compute point coords
        P = np.array([r*math.cos(theta), 0.0, r*math.sin(theta), 1.0], dtype=np.float32)
        #print(P)
        # apply rotation - this also gives us the vertex normals
        NV = np.dot(RM, P)
        # normalize 
        #NV = NV / np.linalg.norm(NV)
        # apply translation 
        Pt = np.dot(TM, NV)

        return (Pt, NV)

    def compute_vertices(self):
        """ Compute vertices for the torus. 
            returns np float32 array of n coords (x, y, z): shape (3*n, )
        """

        R, r, N, M = self.R, self.r, self.N, self.M
        
        # create an empty array to hold vertices/normals
        vertices = []
        normals = []

        # The points on the ring are generated on the X-Z plane.
        # Then they are rotated and translated into the correct 
        # position on the torus.

        # for all N rings around the torus 
        for i in range(N):

            # for all M points around a ring 
            for j in range(M+1):

                # compute angle theta of point 
                theta = (j % M) *2*math.pi/M

                #---ring #1------

                # compute angle
                alpha1 = i*2*math.pi/N
                # compute transforms 
                RM1, TM1 = self.compute_rt(R, alpha1)
                # compute points 
                Pt1, NV1 = self.compute_pt(r, theta, RM1, TM1)

                #---ring #2------
                # index of next ring 
                ip1 = (i + 1) % N

                # compute angle
                alpha2 = ip1*2*math.pi/N
                # compute transforms 
                RM2, TM2 = self.compute_rt(R, alpha2)
                # compute points 
                Pt2, NV2 = self.compute_pt(r, theta, RM2, TM2)
                
                # store vertices/normals in correct order for GL_TRIANGLE_STRIP
                vertices.append(Pt1[0:3])
                vertices.append(Pt2[0:3])

                # add normals
                normals.append(NV1[0:3])
                normals.append(NV2[0:3])

        # return vertices and colors in correct format 
        vertices = np.array(vertices, np.float32).reshape(-1)
        normals = np.array(normals, np.float32).reshape(-1)
        #print(vertices.shape)
        return vertices, normals

    def compute_colors(self):
        """ Compute vertices for the torus. 
            returns np float32 array of n coords (x, y, z): shape (3*n, )
        """

        R, r, N, M = self.R, self.r, self.N, self.M

        # The points on the ring are generated on the X-Z plane.
        # Then they are rotated and translated into the correct 
        # position on the torus.

        # for all N rings around the torus 
        for i in range(N):

            # for all M points around a ring 
            for j in range(M+1):

                # j value 
                jj = j % M

                # store colors - same color applies to (V_i_j, V_ip1_j)
                col = self.colors_dict[(i, jj)]
                # get index into array                 
                index = 3*(2*i*(M+1) + 2*j)
                # set color 
                self.colors[index:index+3] = col
                self.colors[index+3:index+6] = col


    def setup_vao(self, vertices, normals, colors):
        # set up vertex array object (VAO)
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # --------
        # vertices
        # --------
        self.vertexBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexBuffer)
        # set buffer data 
        glBufferData(GL_ARRAY_BUFFER, 4*len(vertices), vertices, 
                     GL_STATIC_DRAW)
        # enable vertex attribute array
        glEnableVertexAttribArray(0)
        # set buffer data pointer
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

        # normals
        # --------
        self.normalBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.normalBuffer)
        # set buffer data 
        glBufferData(GL_ARRAY_BUFFER, 4*len(normals), normals, 
                     GL_STATIC_DRAW)
        # enable vertex attribute array
        glEnableVertexAttribArray(2)
        # set buffer data pointer
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, 0, None)

        # --------
        # colors
        # --------
        self.colorBuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.colorBuffer)
        # set buffer data 
        glBufferData(GL_ARRAY_BUFFER, 4*len(colors), colors, 
                     GL_STATIC_DRAW)
        # enable color attribute array
        glEnableVertexAttribArray(1)
        # set buffer data pointer
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
   
        # unbind VAO
        glBindVertexArray(0)

    def set_colors(self, colors):
        self.colors_dict = colors
        self.recalc_colors()

    def recalc_colors(self):

        # get colors 
        self.compute_colors()

        # bind VAO
        glBindVertexArray(self.vao)
        # --------
        # colors
        # --------
        glBindBuffer(GL_ARRAY_BUFFER, self.colorBuffer)
        # set buffer data 
        glBufferSubData(GL_ARRAY_BUFFER, 0, 4*len(self.colors), self.colors)
        # unbind VAO
        glBindVertexArray(0)

    # step
    def step(self):
        # recompute colors
        self.recalc_colors()

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
        glMultiDrawArrays(GL_TRIANGLE_STRIP, self.first_indices, self.counts, self.N)
        # unbind VAO
        glBindVertexArray(0)

    
