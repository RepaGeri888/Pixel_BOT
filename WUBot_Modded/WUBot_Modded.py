
from PIL import Image
from pyautogui import *
import pyautogui
import time
import keyboard
import win32api, win32con
import numpy as np
import math
import threading, time
import cv2
import skimage.io
import skimage.color
from sewar.full_ref import ssim
from windowcapture import WindowCapture

global minimap_x1,minimap_y1, minimap_x2,minimap_y2
global _screenshot
global reset
global roaming
global collecting

wincap = WindowCapture('WarUniverse')
window_x, window_y, window_w, window_h = wincap.get_screen_dimensions()
window_center = int((window_x+window_w/2)), int((window_y+window_h/2))

click_start = 0

roaming = True
collecting = False

def clickMinimap():
    current_x = np.random.randint(minimap_x1,minimap_x2+minimap_x1)
    current_y = np.random.randint(minimap_y1,minimap_y2+minimap_y1)
    click(current_x,current_y)

def recognizeMap():
    global minimap_x1,minimap_y1, minimap_x2,minimap_y2
    time.sleep(3)
    minimap = None
    i = 1
    while minimap == None and i < 6:
        minimap_img = Image.open("minimap" + str(i) + ".png")
        minimap = pyautogui.locateOnScreen(minimap_img,grayscale=True,confidence=0.7)
        i += 1

    t = 0
    map_w = minimap[2]-72
    map_h = minimap[3]-34
    map_w_half = int(map_w/2)
    map_h_half = int(map_h/2)

    x, y = pyautogui.center(minimap)

    minimap_x1, minimap_x2, minimap_y1, minimap_y2 = x-map_w_half+8, map_w, y-map_h_half, map_h
    
def calibrateMap():
    global minimap_x1,minimap_y1, minimap_x2,minimap_y2
    minimap_x1 = 0
    minimap_x2 = 0

    right_click = -10
    left_click = -10

    print("Enter map top left corner!")
    while minimap_x1 == 0:
        right_click = win32api.GetKeyState(0x02)&0x8000
        if right_click > 0:
            minimap_x1,minimap_y1 = pyautogui.position()
    print(minimap_x1, " ,", minimap_y1)

    time.sleep(0.1)

    print("Enter map down right corner!")
    while minimap_x2 == 0:
        left_click = win32api.GetKeyState(0x02)&0x8000
        if left_click == 0:
            minimap_x2,minimap_y2 = pyautogui.position()
    print(minimap_x2, " ,", minimap_y2)

    time.sleep(1)

def click(x,y):
    win32api.SetCursorPos((x,y))
    time.sleep(0.01)
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
    time.sleep(np.random.uniform(0.1,0.3))
    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)

def checkIfCollectedModded():
    elapsed = 0
    start = time.time()
    global _screenshot
    global reset
    global collecting
    global roaming
    frame_x, frame_y = int(window_w*0.33)+wincap.cropped_x, int(window_h*0.38)+wincap.cropped_y
    frame_w, frame_h = int(window_w*0.34), int(window_h*0.24)
    while collecting:
        trimmed_img = wincap.get_screenshot_region(frame_x,frame_y,frame_w,frame_h)
        _screenshot = wincap.get_screenshot()
        gray_image = cv2.cvtColor(trimmed_img, cv2.COLOR_BGR2GRAY)
        coll_green = np.count_nonzero(gray_image==220)
        trav_rose = np.count_nonzero(gray_image==175)

        elapsed = time.time() - start
        if coll_green > 500 or elapsed > 2:
            collecting = False
        elif trav_rose < 500:
            collecting = False
            
        time.sleep(0.01)
    click_start = time.time()
    reset = True
           
def getContours(gray_image, gray_value):
    gray_image[gray_image != gray_value] = 0
    blur = cv2.GaussianBlur(gray_image, (5, 5), cv2.BORDER_DEFAULT)
    ret,thresh = cv2.threshold(blur,30,255,0)
    contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return contours

def collectBoxModded():
    global _screenshot
    global reset
    global collecting
    global roaming
    clickMinimap()
    reset = False
    click_start = time.time()
    while keyboard.is_pressed('q')==False:
        time.sleep(0.1)
        
        measure1 = time.time()

        if not collecting:
            _screenshot = wincap.get_screenshot()
            
            gray_image = cv2.cvtColor(_screenshot, cv2.COLOR_BGR2GRAY)
            box_contours = getContours(gray_image.copy(), 68)

            if len(box_contours) > 0:
                boxes = []
                for c in box_contours:
                    M = cv2.moments(c)
 
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                    else:
                        cX, cY = 0, 0

                    if cX != 0 and cY != 0:
                        boxes.append([cX+window_x,cY+window_y])            
                
                coordinates = 0,0
                closest = math.inf

                for x in boxes:
                    distance = math.dist(window_center, x)
                    if closest > distance:
                        closest = distance
                        coordinates = x

                if closest != math.inf:
                    measure2 = time.time()
                    print(measure2-measure1)
                    click(coordinates[0], coordinates[1])
                    collecting=True
                    
                    time.sleep(0.3)
                    checkIfCollectedModded()

            else:
                trimmed_image = _screenshot[int(window_w*0.45):int(window_w*0.45)+301, int(window_h*0.35):int(window_h*0.35)+301]
                trimmed_image = cv2.cvtColor(trimmed_image, cv2.COLOR_BGR2GRAY)
                trav_rose = np.count_nonzero(trimmed_image==175)

                if trav_rose < 100 or reset:
                    clickMinimap()
                    click_start = time.time()
                    reset = False


def killNpcs():
    while keyboard.is_pressed('q')==False:
        global _screenshot

        if True:
            gray_image = cv2.cvtColor(_screenshot, cv2.COLOR_BGR2GRAY)
            box_contours = getContours(gray_image.copy(), 50)

            if len(box_contours) > 0:
                boxes = []
                for c in box_contours:
                    M = cv2.moments(c)
 
                    if M["m00"] != 0:
                        cX = int(M["m10"] / M["m00"])
                        cY = int(M["m01"] / M["m00"])
                    else:
                        cX, cY = 0, 0

                    if cX != 0 and cY != 0:
                        boxes.append([cX+window_x,cY+window_y])

                coordinates = 0,0
                closest = math.inf

                for x in boxes:
                    distance = math.dist(window_center, x)
                    if closest > distance:
                        closest = distance
                        coordinates = x

                if closest < window_w/2:
                    click(coordinates[0], coordinates[1])
                    time.sleep(0.1)
                    pyautogui.press("ctrl")

        time.sleep(1)

recognizeMap()

collectBoxThread = threading.Thread(target=collectBoxModded)
killNpcsThread = threading.Thread(target=killNpcs)
collectBoxThread.start()
time.sleep(2)
killNpcsThread.start()