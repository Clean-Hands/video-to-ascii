
import cv2
import os
from math import floor
from time import sleep, perf_counter

os.system('cls')

dark_to_light = " .:;!iI8@"[::-1]
usable_chars = [dark_to_light[::-1][i] for i in range(len(dark_to_light))]

def to_symbol(value):
    mid = value/255
    if mid == 1:
        mid -= 0.00001
    g = len(usable_chars) * mid
    return usable_chars[int(g)]
    # return str(int(g))



print(usable_chars)
videos = ["IMG-20231002-WA0006.mp4", "VID-20231009-WA0001.mp4"]

cam = cv2.VideoCapture(videos[1])
fps = cam.get(cv2.CAP_PROP_FPS)

try:
    if not os.path.exists('data'):
        os.makedirs('data')
except OSError:
    print("Error Creating Directory of Data")



r, frame = cam.read()
vid_height, vid_width = frame.shape[0], frame.shape[1]*2.2
term_width, term_height = os.get_terminal_size().columns, os.get_terminal_size().lines-1

if (vid_width/vid_height) > (term_width/term_height):
    width = term_width
    height = int(width*vid_height/vid_width)
else:
    height = term_height
    width = int(height*vid_width/vid_height)

lim = 1000
frames = []
j = 0
while(True):
    print(f"pulling frame {j+1}. (limit = {lim})", end = "\r")
    ret,frame = cam.read()
    if not ret or j >= lim:
        break
    frames.append(frame)
    j += 1
cam.release()
cv2.destroyAllWindows()

os.system('cls')


for i, frame in enumerate(frames):
    
    print(f"preparing frame {i+1}/{j}.", end = "\r")
    resized = cv2.resize(frame, dsize=(width, height))
    monochromatic = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

    lst2d = [[""]*width for i in range(height)]
    for x in range(height):
        for y in range(width):
            lst2d[x][y] = to_symbol(monochromatic[x][y])

    lines = ""
    for lsty in lst2d:
        line = "".join(lsty)
        lines+=line+"\n"
    
    frames[i] = lines[:-1]

os.system('cls')

for i in range(10):
    for frame in frames:
        start = perf_counter()
        
        os.system('cls')
        print(frame)

        elapsed = perf_counter()-start
        sleep(max(0,(1/fps)-elapsed))