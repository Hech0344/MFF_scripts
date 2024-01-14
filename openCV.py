import cv2
import os
import base64
import numpy as np
import subprocess
from subprocess import Popen
import settings
import adb
import time
import signal

def test( target_path,template_path ) :
    target = cv2.imread(target_path)     #原始圖像
    template = cv2.imread(template_path) #模板圖像
    h, w = template.shape[:2] #height, width
    result = cv2.matchTemplate( target, template, cv2.TM_SQDIFF_NORMED )

    len1, len2 = result.shape[:2]
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle( target, top_left, bottom_right, (0, 255, 0), 2)
    cv2.imshow("windows_name",target)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return min_loc

def sub_match_template( template_path,threshold = 0.05,return_center = True
                    ,print_debug = True,scope = None,except_locs = None):
    time.sleep(1)
    if(print_debug):
        print("-------------------------------------------------")
        print("Template Matching: start to match screenshot.png by " + template_path )

    command = "\"" + settings.adb_path + "\"" + " -s " + settings.device_address + " shell screencap -p "
    pipe = subprocess.Popen( command, stdin = subprocess.PIPE, stdout = subprocess.PIPE, shell = False )
    image_bytes = pipe.stdout.read().replace(b'\r\n', b'\n')
    target = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    template = cv2.imread(template_path)
    theight, twidth = template.shape[:2]

    #Popen("TASKKILL /F /PID {pid} /T".format(pid=pipe.pid))
    pipe.terminate()
    pipe.kill()
    pipe.wait()
    """
    command = "\"" + settings.adb_path + "\"" + " -s " + settings.device_address + "\"screencap -p | busybox base64\""
    pcommand = os.popen(command)
    png_screenshot_data = pcommand.read()
    png_screenshot_data = base64.b64decode(png_screenshot_data)
    pcommand.close()
    target = cv2.imdecode(np.frombuffer(png_screenshot_data, np.uint8), cv2.IMREAD_COLOR)
    template = cv2.imread(template_path)
    theight, twidth = template.shape[:2]
    """
    if(scope != None):
        target = target[scope[0]:scope[1],scope[2]:scope[3]]

    result = cv2.matchTemplate(target,template,cv2.TM_SQDIFF_NORMED)

    len1, len2 = result.shape[:2]
    if(except_locs != None):
        for except_loc in except_locs:
            if(except_loc == None):
                continue
            for j in range(except_loc[0] - settings.except_dist,except_loc[0] + settings.except_dist):
                for k in range(except_loc[1] - settings.except_dist,except_loc[1] + settings.except_dist):
                    if(j>=0 and j<len2 and k>=0 and k<len1):
                        result[k][j] = 1

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if(print_debug):
        print("ImageProcessor: best match value :"+str(min_val)+"   match location:"+str(min_loc[0])+" "+str(min_loc[1]))

    if(min_val > threshold):
        if(print_debug):
            print("ImageProcessor: match failed")
        return None
    else:
        if(print_debug):
            print("ImageProcessor: match succeeded")

    last_match_loc = min_loc

    if(return_center):
        min_loc = (min_loc[0] + twidth/2,min_loc[1] + theight/2)

    if(scope != None):
        min_loc = (min_loc[0] + scope[2],min_loc[1] + scope[0])

    return min_loc


def match_template(target_path,template_path,threshold = 0.05,return_center = True
                    ,print_debug = True,scope = None,except_locs = None):

    if(print_debug):
        print("-------------------------------------------------")
        print("Template Matching: start to match "+target_path+" by "+template_path)

    if(print_debug and except_locs != None):
        print("ImageProcessor: except_locs: "+str(except_locs))

    target = cv2.imread(target_path)
    #target = adb.screenshot2()
    template = cv2.imread(template_path)
    theight, twidth = template.shape[:2]

    if(scope != None):
        target = target[scope[0]:scope[1],scope[2]:scope[3]]

    result = cv2.matchTemplate(target,template,cv2.TM_SQDIFF_NORMED)

    len1, len2 = result.shape[:2]
    if(except_locs != None):
        for except_loc in except_locs:
            if(except_loc == None):
                continue
            for j in range(except_loc[0] - settings.except_dist,except_loc[0] + settings.except_dist):
                for k in range(except_loc[1] - settings.except_dist,except_loc[1] + settings.except_dist):
                    if(j>=0 and j<len2 and k>=0 and k<len1):
                        result[k][j] = 1

    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    if(print_debug):
        print("ImageProcessor: best match value :"+str(min_val)+"   match location:"+str(min_loc[0])+" "+str(min_loc[1]))

    if(min_val > threshold):
        if(print_debug):
            print("ImageProcessor: match failed")
        return None
    else:
        if(print_debug):
            print("ImageProcessor: match succeeded")

    last_match_loc = min_loc

    if(return_center):
        min_loc = (min_loc[0] + twidth/2,min_loc[1] + theight/2)

    if(scope != None):
        min_loc = (min_loc[0] + scope[2],min_loc[1] + scope[0])

    return min_loc