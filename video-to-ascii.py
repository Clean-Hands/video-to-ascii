print("Importing libraries...")

import os
from sys import argv
import cv2
from moviepy.editor import VideoFileClip
import tempfile
import curses
from time import sleep, perf_counter, time

# prevent the pygame splash text from printing before we import it 
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame

print("Imported!")

def to_symbol(value):
    mid = value/255
    if mid == 1:
        mid -= 0.00001
    g = len(usable_chars) * mid
    return usable_chars[int(g)]

def print_usage_statement():
    print("\nUsage: video-to-ascii.py -[modifiers] [file]\n\n" +
          
          "Modifiers:\n" +
          "    g: Generate ascii frames from video file [file].\n" +
          "    p: Load and play frames saved in text file [file].\n" +
          "    gp: Generate and play frames from video file [file].\n" +
          "    r: Real-time render and display frames from video file [file].\n" +
          "    ra: Real-time render and display frames from video file [file] with audio.\n")
    exit(1)

if len(argv) < 3:
    print_usage_statement()

dark_to_light = " ·:;!iIH#N@"
usable_chars = [dark_to_light[i] for i in range(len(dark_to_light))]


if argv[1][0] !=  "-" or len(argv[1]) < 2 or len(argv[1]) > 3:
    print_usage_statement()
else:
    want_generate = "g" in argv[1]
    want_play = "p" in argv[1]
    want_realtime = "r" in argv[1]
    want_audio = "a" in argv[1]

    if not (want_generate or want_play or want_realtime or want_audio):
        print_usage_statement()
    if want_audio and ((want_play or want_generate) or not want_realtime):
        print_usage_statement()
    if want_play and (want_realtime or want_audio):
        print_usage_statement()
    if want_generate and want_realtime:
        print_usage_statement()



if want_realtime:

    if len(argv) < 3:
        print("Incorrect number of arguments.")
        exit(1)

    video = argv[2]

    if not os.path.exists(video):
        print(f"Video \"{video}\" does not exist.")
        exit(1)

    # load video file
    cap = cv2.VideoCapture(video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # calculate frame height and width
    r, frame = cap.read()
    vid_height, vid_width = frame.shape[0], frame.shape[1]*2.2
    term_width, term_height = os.get_terminal_size().columns-1, os.get_terminal_size().lines-1

    if (vid_width/vid_height) > (term_width/term_height):
        width = term_width
        height = int(width*vid_height/vid_width)
    else:
        height = term_height
        width = int(height*vid_width/vid_height)

    # if the user wants audio, prepare the audio
    if want_audio:
        print("EXTRACTING AUDIO:")

        # Load the video clip
        video_clip = VideoFileClip(video)

        # Extract the audio from the video
        audio_clip = video_clip.audio

        # Save audio to a temporary file
        temp_audio_file = tempfile.NamedTemporaryFile(suffix=".wav")
        temp_audio_file.close()
        audio_clip.write_audiofile(temp_audio_file.name)
        audio_clip.close()
        

    pygame.init()
    stdscr = curses.initscr()

    try:
        # if the user wants audio, load and play the audio file
        if want_audio:
            pygame.mixer.init()
            pygame.mixer.music.load(temp_audio_file.name)
            pygame.mixer.music.play()

        # use current time to figure out which frame should be shown at any moment
        start_time = time()

        curr_frame = 0
        for i in range(totalFrames):

            curr_frame += 1

            # read the next frame
            ret,frame = cap.read()
            if not ret:
                break
            
            # prepare the frame for conversion
            resized = cv2.resize(frame, dsize=(width, height))
            monochromatic = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

            # convert the frame to ascii characters
            lst2d = [[""] * width for i in range(height)]
            for x in range(height):
                for y in range(width):
                    lst2d[x][y] = to_symbol(monochromatic[x][y])

            # join the lines together
            lines = ""
            for lsty in lst2d:
                line = "".join(lsty)
                lines += line + "\n"
            
            # display the frame
            stdscr.move(0, 0)
            stdscr.addstr(lines)
            stdscr.refresh()
            
            # make sure that the next frame we render is the correct
            # frame based on the time passed and the frame rate
            # i.e. skip frames in order to get back up to speed
            while time() - start_time >= 1/fps * curr_frame:
                cap.read()
                curr_frame += 1

            # if this frame took shorter than 1/fps seconds,
            # spin for the remaining amount of time
            while time() - start_time <= 1/fps * curr_frame:
                pass


    finally:
        # Restore the terminal to its original state
        curses.endwin()
        cap.release()

        # delete the temp file
        if want_audio:
            pygame.mixer.music.unload()
            os.remove(temp_audio_file.name)
            print(f"Deleted temp file {temp_audio_file.name}")


else:

    if want_generate:

        video = argv[2]

        if not os.path.exists(video):
            print(f"Video \"{video}\" does not exist.")
            exit(1)

        # load video file
        cap = cv2.VideoCapture(video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # if the data directory doesn't exist, create it 
        try:
            if not os.path.exists('data'):
                os.makedirs('data')
        except OSError:
            print("Error Creating Directory of Data")
        
        # create output file
        video_fixed = video.replace(".\\", "")
        output_file = f".\data\{video_fixed} output.txt"
        f = open(output_file, "w")

        # save the video's fps within the text file
        f.write(f"FRAME_RATE: {fps}\n")

        # calculate the frame's height and width
        r, frame = cap.read()
        vid_height, vid_width = frame.shape[0], frame.shape[1]*2.2
        term_width, term_height = os.get_terminal_size().columns, os.get_terminal_size().lines-1

        if (vid_width/vid_height) > (term_width/term_height):
            width = term_width
            height = int(width*vid_height/vid_width)
        else:
            height = term_height
            width = int(height*vid_width/vid_height)


        framesRendered = 0
        frameRead = True
        bufSize = 1

        # while we are able to read more frames, continue reading
        while frameRead:

            # try to read the next frame
            ret, frame = cap.read()
            if not ret:
                frameRead = False
                break

            # prepare the frame for conversion
            resized = cv2.resize(frame, dsize=(width, height))
            monochromatic = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)

            # convert the frame to ascii characters
            lst2d = [[""]*width for i in range(height)]
            for x in range(height):
                for y in range(width):
                    lst2d[x][y] = to_symbol(monochromatic[x][y])

            # format and write the converted frame to our output file
            lines = ""
            for lsty in lst2d:
                line = "".join(lsty)
                lines += line + "\t"
            f.write(lines[:-1] + "\n")

            framesRendered += 1

            print(f"Total frames rendered: {framesRendered}/{totalFrames-1} frames.", end = "\r")

        cap.release()
        f.close()

        # if the user wants the generated frames to be played, continue and play it
        if not want_play:
            print(f"{framesRendered} frames rendered and saved to \"{output_file}\"")
            exit(0)

        input(f"\nRender of \"{video}\" complete! Press enter to play... ")
        f = open(f"data\{video} output.txt", "r")


    elif want_play:

        if len(argv) < 3:
            print("Incorrect number of arguments.")
            exit(1)

        if not os.path.exists(argv[2]):
            print(f"ASCII file \"{argv[2]}\" does not exist.")
            exit(1)

        # load the text file
        f = open(f"{argv[2]}", "r")
        framesRendered = len(f.readlines()) - 1
        f.seek(0)


    # read the video's framerate
    fps_info = f.readline().split(" ")
    if fps_info[0] == "FRAME_RATE:":
        fps = float(fps_info[1])

    stdscr = curses.initscr()

    try:
        # Clear the screen
        stdscr.clear()
        
        # use current time to figure out which frame should be shown at any moment
        start_time = time()

        curr_frame = 0
        for i in range(framesRendered):
            
            curr_frame += 1

            # read the frame from file
            frame = f.readline()
            frame = frame.replace("\t", "\n")

            # display the frame
            stdscr.move(0, 0)
            stdscr.addstr(frame)
            stdscr.refresh()
            
            # make sure that the next frame we render is the correct
            # frame based on the time passed and the frame rate
            # i.e. skip frames in order to get back up to speed
            while time() - start_time >= 1/fps * curr_frame:
                frame = f.readline()
                curr_frame += 1

            # if this frame took shorter than 1/fps seconds,
            # spin for the remaining amount of time
            while time() - start_time <= 1/fps * curr_frame:
                pass

    finally:
        # Restore the terminal to its original state
        curses.endwin()

    f.close()