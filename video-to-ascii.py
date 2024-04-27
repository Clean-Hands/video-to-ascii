import os
from sys import argv
import cv2
import pygame
from moviepy.editor import VideoFileClip
import tempfile
import curses
from time import sleep, perf_counter, time

def to_symbol(value):
    mid = value/255
    if mid == 1:
        mid -= 0.00001
    g = len(usable_chars) * mid
    return usable_chars[int(g)]

if len(argv) < 2:
    print("Incorrect number of arguments.")
    exit(1)

dark_to_light = " ·:;!iIH#N@"[::-1]
usable_chars = [dark_to_light[::-1][i] for i in range(len(dark_to_light))]



if argv[1] == "-r":

    if len(argv) < 3:
        print("Incorrect number of arguments.")
        exit(1)

    video = argv[2]

    if not os.path.exists(video):
        print(f"Video \"{video}\" does not exist.")
        exit(1)

    cam = cv2.VideoCapture(video)
    fps = cam.get(cv2.CAP_PROP_FPS)
    totalFrames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
    
    r, frame = cam.read()
    vid_height, vid_width = frame.shape[0], frame.shape[1]*2.2
    term_width, term_height = os.get_terminal_size().columns-1, os.get_terminal_size().lines-1

    if (vid_width/vid_height) > (term_width/term_height):
        width = term_width
        height = int(width*vid_height/vid_width)
    else:
        height = term_height
        width = int(height*vid_width/vid_height)
    
    # Load the video clip
    video_clip = VideoFileClip(video)

    # Extract the audio from the video
    audio_clip = video_clip.audio

    # Save audio to a temporary file
    temp_audio_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_audio_file.close()
    audio_clip.write_audiofile(temp_audio_file.name)

    # Initialize Pygame
    pygame.init()

    # Initialize curses
    stdscr = curses.initscr()

    try:

        curr_frame = 0

        # Initialize Pygame's mixer module
        pygame.mixer.init()

        # Load audio file into Pygame's mixer
        pygame.mixer.music.load(temp_audio_file.name)

        # Play the audio
        pygame.mixer.music.play()

        # use current time to figure out which frame should be shown at any moment
        start_time = time()

        for i in range(totalFrames):

            curr_frame += 1

            ret,frame = cam.read()
            if not ret:
                break
                
            resized = cv2.resize(frame, dsize=(width, height))
            monochromatic = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

            lst2d = [[""]*width for i in range(height)]
            for x in range(height):
                for y in range(width):
                    lst2d[x][y] = to_symbol(monochromatic[x][y])
                    if lst2d[x][y] not in usable_chars:
                        input(f"{lst2d}")

            lines = ""
            for lsty in lst2d:
                line = "".join(lsty)
                lines+=line+"\n"
            
            stdscr.move(0, 0)
            
            stdscr.addstr(lines)
            stdscr.refresh()
            
            # make sure that the next frame we render is the correct
            # frame based on the time passed and the frame rate
            # i.e. skip frames in order to get back up to speed
            while time() - start_time >= 1/fps * curr_frame:
                cam.read()
                curr_frame += 1

            # if this frame took shorter than 1/fps seconds,
            # sleep the remaining amount of time
            # sleep(max(0,(1/fps)-elapsed))
            while time() - start_time <= 1/fps * curr_frame:
                pass


    finally:
        # Restore the terminal to its original state
        curses.endwin()
        cam.release()


else:

    if argv[1] == "-p":

        if len(argv) < 3:
            print("Incorrect number of arguments.")
            exit(1)

        if not os.path.exists(argv[2]):
            print(f"ASCII file \"{argv[2]}\" does not exist.")
            exit(1)

        f = open(f"{argv[2]}", "r")
        framesRendered = len(f.readlines()) - 1
        f.seek(0)

    else:

        video = argv[1]

        if not os.path.exists(video):
            print(f"Video \"{video}\" does not exist.")
            exit(1)

        cam = cv2.VideoCapture(video)
        fps = cam.get(cv2.CAP_PROP_FPS)
        totalFrames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))

        try:
            if not os.path.exists('data'):
                os.makedirs('data')
        except OSError:
            print("Error Creating Directory of Data")

        f = open(f"data/{video} output.txt", "w")

        f.write(f"FRAME_RATE: {fps}\n")

        r, frame = cam.read()
        vid_height, vid_width = frame.shape[0], frame.shape[1]*2.2
        term_width, term_height = os.get_terminal_size().columns, os.get_terminal_size().lines-1

        if (vid_width/vid_height) > (term_width/term_height):
            width = term_width
            height = int(width*vid_height/vid_width)
        else:
            height = term_height
            width = int(height*vid_width/vid_height)

        framesRendered = 0
        framesRead = 1
        bufSize = 1000

        while framesRead != 0:

            os.system('cls')

            framesRead = 0
            frames = []
            while True:
                print(f"Reading frame {framesRead+1}. (buffer size = {bufSize})", end = "\r")
                ret,frame = cam.read()
                if not ret or framesRead >= bufSize:
                    break
                frames.append(frame)
                framesRead += 1

            os.system('cls')

            for i, frame in enumerate(frames):
                
                print(f"Rendering frame {i+1}/{framesRead}. Total frames rendered: {framesRendered+1}/{totalFrames-1} frames.", end = "\r")
                resized = cv2.resize(frame, dsize=(width, height))
                monochromatic = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

                lst2d = [[""]*width for i in range(height)]
                for x in range(height):
                    for y in range(width):
                        lst2d[x][y] = to_symbol(monochromatic[x][y])

                lines = ""
                for lsty in lst2d:
                    line = "".join(lsty)
                    lines+=line+"\t"
                
                f.write(lines[:-1] + "\n")

                framesRendered += 1

        cam.release()
        f.close()

        os.system('cls')

        input(f"Render of \"{video}\" complete! Press enter to play... ")

        f = open(f"data/{video} output.txt", "r")

    fps_info = f.readline().split(" ")

    if fps_info[0] == "FRAME_RATE:":
        fps = float(fps_info[1])

    os.system('cls')

    # Initialize curses
    stdscr = curses.initscr()

    try:
        # Clear the screen
        stdscr.clear()

        for i in range(framesRendered):
            start = perf_counter()
            
            frame = f.readline()
            frame = frame.replace("\t", "\n")

            stdscr.move(0, 0)
            
            stdscr.addstr(frame)
            stdscr.refresh()

            elapsed = perf_counter()-start
            sleep(max(0,(1/fps)-elapsed))

    finally:
        # Restore the terminal to its original state
        curses.endwin()

    f.close()