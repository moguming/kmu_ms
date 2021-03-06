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

import matplotlib.pyplot as plt
import LaneRecognize as LR

#=============================================
# 터미널에서 Ctrl-C 키입력으로 프로그램 실행을 끝낼 때
# 그 처리시간을 줄이기 위한 함수
#=============================================
def signal_handler(sig, frame):
    import time
    time.sleep(3)
    os.system('killall -9 python rosout')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

#=============================================
# 프로그램에서 사용할 변수, 저장공간 선언부
#=============================================
image = np.empty(shape=[0]) # 카메라 이미지를 담을 변수
bridge = CvBridge() 
motor = None # 모터 토픽을 담을 변수

#=============================================
# 프로그램에서 사용할 상수 선언부
#=============================================
CAM_FPS = 30    # 카메라 FPS - 초당 30장의 사진을 보냄
width, height = 640, 480    # 카메라 이미지 가로x세로 크기

#=============================================
# 콜백함수 - 카메라 토픽을 처리하는 콜백함수
# 카메라 이미지 토픽이 도착하면 자동으로 호출되는 함수
# 토픽에서 이미지 정보를 꺼내 image 변수에 옮겨 담음.
#=============================================
def img_callback(data):
    global image
    image = bridge.imgmsg_to_cv2(data, "bgr8")

#=============================================
# 모터 토픽을 발행하는 함수  
# 입력으로 받은 angle과 speed 값을 
# 모터 토픽에 옮겨 담은 후에 토픽을 발행함.
#=============================================
def drive(angle, speed):

    global motor

    motor_msg = xycar_motor()
    motor_msg.angle = angle
    motor_msg.speed = speed

    motor.publish(motor_msg)

#=============================================
# 실질적인 메인 함수 
# 카메라 토픽을 받아 각종 영상처리와 알고리즘을 통해
# 차선의 위치를 파악한 후에 조향각을 결정하고,
# 최종적으로 모터 토픽을 발행하는 일을 수행함. 
#=============================================
def start():

    # 위에서 선언한 변수를 start() 안에서 사용하고자 함
    global motor, image

    #=========================================
    # ROS 노드를 생성하고 초기화 함.y
    # 카메라 토픽을 구독하고 모터 토픽을 발행할 것임을 선언
    #=========================================
    rospy.init_node('driving')
    motor = rospy.Publisher('xycar_motor', xycar_motor, queue_size=1)
    image_sub = rospy.Subscriber("/usb_cam/image_raw/",Image,img_callback)

    print ("----- Xycar self driving -----")

    # 첫번째 카메라 토픽이 도착할 때까지 기다림.
    while not image.size == (width * height * 3):
        continue
 
    #=========================================
    # 메인 루프 
    # 카메라 토픽이 도착하는 주기에 맞춰 한번씩 루프를 돌면서 
    # "이미지처리 +차선위치찾기 +조향각결정 +모터토픽발행" 
    # 작업을 반복적으로 수행함.
    #=========================================
    while not rospy.is_shutdown():

        # 이미지처리를 위해 카메라 원본이미지를 img에 복사 저장
        img = image.copy()  
        
        # 디버깅을 위해 모니터에 이미지를 디스플레이
        cv2.imshow("CAM View", img)
        cv2.waitKey(1)       
       
        InterestArea = LR.InterestRegion(img, width, height)
        #print(InterestArea)
        canny = LR.Canny(InterestArea)
        dst = LR.top_view(img, width, height)
        src1 = LR.Canny(dst)
        speed = 20

        lines = cv2.HoughLinesP(src1, 1.2, np.pi / 180, 100, minLineLength=100, maxLineGap=60)
        #print(lines)
        #차량
        cv2.line(dst, (int(width / 2), height), (int(width / 2), int(height / 1.3)), (255, 255, 0), 8) 
        if (lines is not None):
            direction = ""
            for i in lines:
                cv2.line(dst, (i[0][0], i[0][1]), (i[0][2], i[0][3]), (0, 0, 255), 2)
                if (i[0][2] < int(width / 2)):
                    angle = 5
                    drive(angle, speed)
                    direction = "Turn Right " + str(abs(width / 2 + i[0][2]))
                elif (i[0][2] > int(width / 2)):
                    angle = -5
                    drive(angle, speed)
                    direction = "Turn Left " + str(abs(width / 2 - i[0][0]))
                elif (i[0][2] == int(width / 2)):
                    angle = 0
                    drive(angle, speed + 5)
                    direction = "Go straight" + str(ads(width / 2))
                    
        dst = cv2.putText(dst, '[Driving Info] : ' + direction, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                          (0, 255, 255), 2, cv2.LINE_AA)       
        #cv2.imshow("img", img)
        cv2.imshow("dst", dst)

#=============================================
# 메인 함수
# 가장 먼저 호출되는 함수로 여기서 start() 함수를 호출함.
# start() 함수가 실질적인 메인 함수임. 
#=============================================
if __name__ == '__main__':
    start()

