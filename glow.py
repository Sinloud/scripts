#!/bin/python3
import cv2
import os
import sys
import time
import json
#Скрипт определения засветов камеры
try:
    os.remove('/tmp/glow_front.jpg')
except:
    pass
try:
    os.remove('/tmp/glow_side.jpg')
except:
    pass
#function to check if cams is busy
def CheckCameras():
    global Busy
    videoint = os.popen("lsof -w /dev/video-int").read()
    videoout = os.popen("lsof -w /dev/video-out").read()
    if (not videoint) and (not videoout):
        Busy = 0
    else:
        Busy = 1
#function to measure percentage of black pixels
def LuxMeasure():
    #set default black percentake to 1 to avoid division by 0
    percent_black_front = 1
    percent_black_side = 1
    #screenshots from front and side cams
    os.system("echo y | ffmpeg -r 1 -i /dev/video-int -f image2 /tmp/glow_front.jpg -t 1  2> /dev/null & echo y | ffmpeg -r 1 -i /dev/video-out -f image2 /tmp/glow_side.jpg -t 1  2> /dev/null")
    #determine percentage of black pixels on front cam
    if os.path.isfile('/tmp/glow_front.jpg'):
        img_bgr = cv2.imread('/tmp/glow_front.jpg')
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        only_img_bgr = cv2.inRange(img_bgr, (0,0,0), (50,50,50))
        only_img_hsv = cv2.inRange(img_hsv, (0,0,0), (180,255,50))
        ratio_black_bgr = cv2.countNonZero(only_img_bgr)/(img_bgr.size/3)
        ratio_black_hsv = cv2.countNonZero(only_img_hsv)/(img_hsv.size/3)
        ratio_black_front = (ratio_black_bgr + ratio_black_hsv)/2
        percent_black_front = (ratio_black_front * 100)
    #determine percentage of black pixels on side cam
    if os.path.isfile('/tmp/glow_side.jpg'):
        img_bgr = cv2.imread('/tmp/glow_side.jpg')
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        only_img_bgr = cv2.inRange(img_bgr, (0,0,0), (50,50,50))
        only_img_hsv = cv2.inRange(img_hsv, (0,0,0), (360,255,50))
        ratio_black_bgr = cv2.countNonZero(only_img_bgr)/(img_bgr.size/3)
        ratio_black_hsv = cv2.countNonZero(only_img_hsv)/(img_hsv.size/3)
        ratio_black_side = (ratio_black_bgr + ratio_black_hsv)/2
        percent_black_side = (ratio_black_side * 100)
    percent_black_front = round(percent_black_front)
    percent_black_side = round(percent_black_side)
    Glow = ('{{"Front": {},\n"Side": {}}}'.format(percent_black_front, percent_black_side))
    #send results to zabbix in json format
    os.system('zabbix_sender -c /etc/zabbix/zabbix_agentd.conf -s "$(hostname -s)" -k glow -o \'{}\''.format(json.dumps({"Front": percent_black_front, "Side": percent_black_side})))
    sys.exit(0)
#loop to check if cams is busy and make screenshots and check black pixels percentage if not (loop runs for 5 min)
for i in range(1, 31):
    CheckCameras()
    if Busy == 1:
        time.sleep(10)
    else:
        LuxMeasure()
