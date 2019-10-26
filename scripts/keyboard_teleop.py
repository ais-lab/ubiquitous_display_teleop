#!/usr/bin/env python

import rospy
from geometry_msgs.msg import Twist
import sys, select, os
if os.name == 'nt':
  import msvcrt
else:
  import tty, termios

MAX_LIN_VEL = 0.74
MAX_ANG_VEL = 2.56

LIN_VEL_STEP_SIZE = 0.01
ANG_VEL_STEP_SIZE = 0.1

msg = """
---------------------------
Moving around:
        w
   a    s    d
        x

w/x : increase/decrease linear velocity ( ~ 0.22)
a/d : increase/decrease angular velocity ( ~ 2.84)

space key, s : force stop

CTRL-C to quit
"""

e = """
Communications Failed
"""

def getKey():
    if os.name == 'nt':
      return msvcrt.getch()

    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel):
    return "currently:\tlinear x vel %s\t linear y vel %s\tangular vel %s " % (target_linear_x_vel, target_linear_y_vel, target_angular_vel)

def makeSimpleProfileBoth(output1, output2, input1, input2, slop):
    if input1 > output1:
        output1 = min( input1, output1 + slop )
    elif input1 < output1:
        output1 = max( input1, output1 - slop )
    else:
        output1 = input1

    if input2 > output2:
        output2 = min( input2, output2 + slop )
    elif input2 < output2:
        output2 = max( input2, output2 - slop )
    else:
        output2 = input2
    return output1, output2

def makeSimpleProfile(output, input, slop):
    if input > output:
        output = min( input, output + slop )
    elif input < output:
        output = max( input, output - slop )
    else:
        output = input
    return output
def constrain(input, low, high):
    if input < low:
      input = low
    elif input > high:
      input = high
    else:
      input = input

    return input

def checkLinearLimitVelocity(vel):
    vel = constrain(vel, -MAX_LIN_VEL, MAX_LIN_VEL)

    return vel

def checkAngularLimitVelocity(vel):
    vel = constrain(vel, -MAX_ANG_VEL, MAX_ANG_VEL)

    return vel

if __name__=="__main__":
    if os.name != 'nt':
        settings = termios.tcgetattr(sys.stdin)

    rospy.init_node('ubiquitous_display_keyboard_teleop')
    pub = rospy.Publisher('cmd_vel', Twist, queue_size=10)


    status = 0
    target_linear_x_vel   = 0.0
    target_linear_y_vel   = 0.0
    target_angular_vel  = 0.0

    control_linear_x_vel  = 0.0
    control_linear_y_vel  = 0.0
    control_angular_vel = 0.0

    try:
        print msg
        while(1):
            key = getKey()
            if key == 'w' :
                target_linear_x_vel = checkLinearLimitVelocity(target_linear_x_vel + LIN_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == 'x' :
                target_linear_x_vel = checkLinearLimitVelocity(target_linear_x_vel - LIN_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == 'a' :
                target_linear_y_vel = checkAngularLimitVelocity(target_linear_y_vel + LIN_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == 'd' :
                target_linear_y_vel = checkAngularLimitVelocity(target_linear_y_vel - LIN_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == 'h' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel + ANG_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == 'k' :
                target_angular_vel = checkAngularLimitVelocity(target_angular_vel - ANG_VEL_STEP_SIZE)
                status = status + 1
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            elif key == ' ' or key == 's' :
                target_linear_x_vel   = 0.0
                target_linear_y_vel   = 0.0
                control_linear_x_vel  = 0.0
                control_linear_y_vel  = 0.0
                target_angular_vel  = 0.0
                control_angular_vel = 0.0
                print vels(target_linear_x_vel, target_linear_y_vel, target_angular_vel)
            else:
                if (key == '\x03'):
                    break


            if status == 20 :
                print msg
                status = 0

            twist = Twist()

            control_linear_x_vel, control_linear_y_vel = makeSimpleProfileBoth(control_linear_x_vel, control_linear_y_vel, target_linear_x_vel, target_linear_y_vel, (LIN_VEL_STEP_SIZE/2.0))
            twist.linear.x = control_linear_x_vel; twist.linear.y = control_linear_y_vel; twist.linear.z = 0.0

            control_angular_vel = makeSimpleProfile(control_angular_vel, target_angular_vel, (ANG_VEL_STEP_SIZE/2.0))
            twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = control_angular_vel

            pub.publish(twist)

    except:
        print e

    finally:
        twist = Twist()
        twist.linear.x = 0.0; twist.linear.y = 0.0; twist.linear.z = 0.0
        twist.angular.x = 0.0; twist.angular.y = 0.0; twist.angular.z = 0.0
        pub.publish(twist)

    if os.name != 'nt':
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
