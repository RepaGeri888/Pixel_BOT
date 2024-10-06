import PIL
import numpy as np
import pyautogui
import win32gui, win32ui, win32con
import subprocess
import os
import win32api, win32com.client, win32con
import time
from PIL import Image

class WindowCapture:

    # properties
    w = 0
    h = 0
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0
    
    # constructor
    def __init__(self, window_name=None):
        # open modded WarUniverse
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        subprocess.call([desktop + '\\ModdedWU_Client'])

        # find the handle for the window we want to capture.
        # if no window name is given, capture the entire screen
        while self.hwnd == None or self.hwnd == 0:
            self.hwnd = win32gui.FindWindow(None, window_name)

        #if window_name is None:
        #    self.hwnd = win32gui.GetDesktopWindow()
        #else:
        #    self.hwnd = win32gui.FindWindow(None, window_name)
        #    if not self.hwnd:
        #        raise Exception('Window not found: {}'.format(window_name))

        # get the window size
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        # set window size and position
        time.sleep(0.3)
        if win32gui.GetForegroundWindow() != self.hwnd: 
            win32gui.SetForegroundWindow(self.hwnd)
            time.sleep(0.3)

        #while window_rect[0] > 0:
        pyautogui.keyDown("win")
        time.sleep(0.3)
        pyautogui.press("left")
        time.sleep(0.3)
        pyautogui.keyUp("win")
        time.sleep(1)
        #win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOP, 0, 0, 418, 447, win32con.SWP_SHOWWINDOW)
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        # click on start button
        start_button = None
        unscaled_img = Image.open("Start_button.png")
        start_button = pyautogui.locateOnScreen(unscaled_img,grayscale=True,confidence=0.7)
        while start_button == None:
            #if win32gui.GetForegroundWindow() != self.hwnd: 
            #    #shell = win32com.client.Dispatch("WScript.Shell")
            #    #shell.SendKeys('%')
            #    win32gui.SetForegroundWindow(self.hwnd)
            for i in range(10):
                
                scaled_img = unscaled_img.resize((int(unscaled_img.width*(0.8**(i+1))), int(unscaled_img.height*(0.8**(i+1)))), Image.ANTIALIAS)
                start_button = pyautogui.locateOnScreen(scaled_img,grayscale=True,confidence=0.7, region=(abs(window_rect[0]),window_rect[1],window_rect[2],window_rect[3]))
                if start_button != None:
                    break

            if start_button == None:
                for i in range(10):
                    if win32gui.GetForegroundWindow() != self.hwnd: 
                        win32gui.SetForegroundWindow(self.hwnd)
                    scaled_img = unscaled_img.resize((int(unscaled_img.width*(1.1**(i+1))), int(unscaled_img.height*(1.1**(i+1)))), Image.ANTIALIAS)
                    start_button = pyautogui.locateOnScreen(scaled_img,grayscale=True,confidence=0.7, region=(abs(window_rect[0]),window_rect[1],window_rect[2],window_rect[3]))
                    if start_button != None:
                        break
            time.sleep(0.3)

        start_button_x, start_button_y = pyautogui.center(start_button)
        win32api.SetCursorPos((start_button_x,start_button_y))
        time.sleep(0.3)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,0,0)
        time.sleep(0.2)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,0,0)

        # account for the window border and titlebar and cut them off
        border_pixels_left = int(self.w/25)
        border_pixels_right = border_pixels_left#220
        titlebar_pixels = 40+int(self.h/25)
        border_pixels_down = 15
        self.w = self.w - border_pixels_left - border_pixels_right
        self.h = self.h - titlebar_pixels - border_pixels_down
        self.cropped_x = border_pixels_left
        self.cropped_y = titlebar_pixels

        # set the cropped coordinates offset so we can translate screenshot
        # images into actual screen positions
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

    def get_screenshot(self):
        if win32gui.GetForegroundWindow() != self.hwnd: 
            win32gui.SetForegroundWindow(self.hwnd)

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() 
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img#, self.offset_x, self.offset_y, self.w, self.h

    def get_screenshot_region(self,x,y,w,h):

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, w, h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (w, h), dcObj, (int(x), int(y)), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        #dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (h, w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type() 
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[...,:3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img#, self.offset_x, self.offset_y, self.w, self.h

    # find the name of the window you're interested in.
    # once you have it, update window_capture()
    # https://stackoverflow.com/questions/55547940/how-to-get-a-list-of-the-name-of-every-open-window
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))
        win32gui.EnumWindows(winEnumHandler, None)

    # translate a pixel position on a screenshot image to a pixel position on the screen.
    # pos = (x, y)
    # WARNING: if you move the window being captured after execution is started, this will
    # return incorrect coordinates, because the window position is only calculated in
    # the __init__ constructor.
    def get_screen_position(self, pos):
        return (pos[0] + self.offset_x, pos[1] + self.offset_y)

    def get_screen_dimensions(self):
        return self.offset_x, self.offset_y, self.w, self.h
    def CloseWindow(self):
        win32gui.PostMessage(self.hwnd,win32con.WM_CLOSE,0,0)