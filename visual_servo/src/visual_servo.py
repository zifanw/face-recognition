#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2008, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Revision $Id$

## Simple talker demo that listens to std_msgs/Strings published 
## to the 'chatter' topic
import cv2
import rospy
from std_msgs.msg import String, Bool, Float32
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from geometry_msgs.msg import Twist
import numpy as np


class visual_servo():
    def __init__(self):
    # In ROS, nodes are uniquely named. If two nodes with the same
    # name are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    

        self.app = SimpleKeyTeleop()
    
        rospy.Subscriber('vrep/image', Image, self.callback, queue_size=1)
    
        pub = rospy.Publisher('/vrep/laser_switch', Bool, queue_size=1)
        pub.publish("true")
        
        self.bridge = CvBridge()


    def callback(self, data):
        #rospy.loginfo(rospy.get_caller_id() + 'I got image')
        cv_img = self.bridge.imgmsg_to_cv2(data, "bgr8")
        cv_img = cv2.flip(cv_img, 1)
        #print(cv_img.shape)
        m_x, m_y, ar = self.image_info(cv_img)
        #print(m_x, m_y, ar)
        linear, angular = self.imginfo_movement(m_x, m_y, ar)
        self.app._set_velocity(linear, angular)
        #if linear!=0 or angular!=0:
        self.app._publish()

    def image_info(self, img): 
        m_x = 0.0
        m_y = 0.0
        area_ratio = 0.0
        counter = 0
        for row_idx, row in enumerate(img):
            for col_idx, pix in enumerate(row):
               r,g,b = pix[2], pix[1], pix[0]
               #Y = 0.299*r+0.578*g+0.114*b
               #Cr = (r-Y)*0.713 + 128
               #Cb = (b-Y)*0.564 + 128
               if r>170 and g>170 and b<20:
               #if Y>200 and Cb<20 and 160>Cr>140:
                   m_x += col_idx
                   m_y += row_idx
                   counter += 1
        if counter>0:
            m_x /= counter #len(ball_pix)
            m_y /= counter #len(ball_pix)
        area_ratio = counter*1.0/(512*512)    
        if counter>0:
            print("find ball", area_ratio)
        return m_x, m_y, area_ratio

    def imginfo_movement(self, m_x, m_y, ar):    
        linear = 0.0
        angular = 0.0
        
        if ar!=0:
            if 270<m_x:
                    angular = -0.6
            elif m_x<200:
                    angular = 0.6
            else: 
                    angular = 0
            if ar < 0.012:
                    linear = 0.8
            elif ar > 0.016:
                    linear = -0.8
            else:
                    linear = 0;

            print("m_x", m_x, "angular", angular, "linear", linear)
            #print("m_x", m_x, "angular", angular)
        return linear, angular 

class SimpleKeyTeleop():
    def __init__(self):
        self._pub_cmd = rospy.Publisher('/vrep/cmd_vel', Twist, queue_size=1)

        self._forward_rate = rospy.get_param('~forward_rate', 8)
        self._backward_rate = rospy.get_param('~backward_rate', 5)
        self._rotation_rate = rospy.get_param('~rotation_rate', 1.0)
        self._angular = 0
        self._linear = 0

    def run(self):
        self._running = True
        while self._running:
            #self._set_velocity()
            self._publish()
            rate.sleep()

    def _get_twist(self, linear, angular):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        return twist

    def _set_velocity(self, linear, angular):
        #if linear > 0:
         #   linear = linear * self._forward_rate
        #else:
         #   linear = linear * self._backward_rate
        #angular = angular * self._rotation_rate
        self._angular = angular
        self._linear = linear

    def _publish(self):
        twist = self._get_twist(self._linear, self._angular)
        self._pub_cmd.publish(twist)


if __name__ == '__main__':
    #listener()
    rospy.init_node('visual_servo', anonymous=True)
    vs = visual_servo()
    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()

