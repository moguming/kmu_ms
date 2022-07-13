#!/usr/bin/env python
# -*- coding: utf-8 -*-

#=============================================
# 함께 사용되는 각종 파이썬 패키지들의 import 선언부
#=============================================
import numpy as np
import cv2, math
import rospy, rospkg, time
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from xycar_msgs.msg import xycar_motor
from math import *
import signal
import sys
import os
import random
import threading

class driving_auto():
    def __init__(self):
        rospy.init_node('driving')
        self.motor = rospy.Publisher('xycar_motor', xycar_motor, queue_size = 1)
        image_sub = rospy.Subscriber("/usb_cam/image_raw/", Image, self.img_callback)

        print("----- Xycar self driving -----")
        self.main()
        rospy.spin()

    
    def signal_handler(self, sig, frame):
        import time
        time.sleep(3)
        os.system('killall -9 python rosout')
        sys.exit(0)

    
    def img_callback(self, data):
        global image
        bridge = CvBridge() 
        image = bridge.imgmsg_to_cv2(data, "bgr8")
    

    def drive(self, angle, speed):

        global motor

        motor_msg = xycar_motor()
        motor_msg.angle = angle
        motor_msg.speed = speed
        #print("B")
        print(motor_msg)

        self.motor.publish(motor_msg)

    def start(self):

        CAM_FPS = 30    # 카메라 FPS - 초당 30장의 사진을 보냄
        width, height = 640, 480    # 카메라 이미지 가로x세로 크기

        while not image.size == (width * height * 3):
            continue
 
        while not rospy.is_shutdown():  
                
            # 이미지처리를 위해 카메라 원본이미지를 img에 복사 저장
            img = image.copy()  
            
            # 디버깅을 위해 모니터에 이미지를 디스플레이
            cv2.imshow("CAM View", img)
            cv2.waitKey(1)        
            #print("A")
            
            speed = 20
            angle = 0
            self.drive(angle, speed)

            threading.Timer(20, self.turn_right).start()

    def turn_right(self):
        speed = 10
        angle = 15
        self.drive(angle, speed)

    def main(self):
        global motor, image
        
        signal.signal(signal.SIGINT, self.signal_handler)

        image = np.empty(shape=[0]) # 카메라 이미지를 담을 변수
        motor = None # 모터 토픽을 담을 변수

        self.start()


if __name__ == '__main__':
    try:
        driving_auto()
    except rospy.ROSInterruptException:
        pass