"""
seirpinski.py

Description:

A program that draws the Sierpinski triangle.

Author: Mahesh Venkitachalam
Website: electronut.in

"""

import time
import turtle
import math
import sys, argparse
import numpy as np

def draw_triangle(t, A, B, C):
    if np.linalg.norm(A-B) > 10.0 :
        draw_triangle(t, A, 0.5*(A + B), 0.5*(A + C))
        draw_triangle(t, 0.5*(A + B), B, 0.5*(B + C))
        draw_triangle(t, 0.5*(A + C), 0.5*(B + C), C)
    else:
        # start fill 
        t.begin_fill()
        # draw 
        t.up()
        t.setpos(A[0], A[1])
        t.down()
        t.setpos(B[0], B[1])
        t.setpos(C[0], C[1])
        t.setpos(A[0], A[1])
        t.up()
        # end fill
        t.end_fill()

# main() function
def main():
    print('Drawing the Sierpinski triangle...')

    # draw 
    a = 200
    t = turtle.Turtle()
    t.hideturtle()
    A = np.array([-a/2, 0])
    B = np.array([a/2, 0]) 
    C = np.array([0, a*math.sqrt(3)/2.0])
    draw_triangle(t, A, B, C)

    win = turtle.Screen()
    win.exitonclick()

# call main
if __name__ == '__main__':
    main()
    
