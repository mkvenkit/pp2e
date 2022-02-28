/*

    motor_flange2.scad

    
    Flange for motor used in laser audio project. The top of the cylinder is tilted and that's the surface to stick the mirror onto.
    
    
    Author: Mahesh Venkitachalam (electronut.in)
*/

// set smoothness
$fn=100;

// tilt angle 
a = 5;

// top cylinder module 
module top_cyl(a = 5, r = 9, h = 20, t = 3) {
// mirror support
difference() {
    // top cylinder 
    linear_extrude(h) {
        circle(r);
    }

    // cutting solid 
    rotate(a, [1, 0, 0]) {
        translate([-h, -h, t]) {
            linear_extrude(h) {
                square(2*h);
            }
        }
    }
}
}

// bottom cylinder with hole 
module bot_cyl(r = 4, h = 4) {
difference() {
    // shaft support
    translate([0, 0, -2]) {
        linear_extrude(h) {
            circle(r);
        }
    }   
}
}

module hole(r = 1.25) {
    // shaft hole
    translate([0, 0, -8]) {
        #linear_extrude(10) {
            circle(r);  
        }
    }   
}

difference() {
union() {
    #top_cyl(a = 5, r = 9, h = 20, t = 3);
    bot_cyl();
}

hole();

}