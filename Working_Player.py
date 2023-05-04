import sys
import cv2
import threading
import tkinter as tk
import numpy as np
from PIL import Image, ImageTk
from pydub import AudioSegment
from just_playback import Playback
from algorithm.combine import get_scene_shot_subshot as algo


class VideoPlayer:
    def __init__(self, video_path, audio_path, width, height, fps, timestamp_dict):
        self.timestamp_dict = timestamp_dict
        self.video_path = video_path
        self.audio_path = audio_path
        self.width = width
        self.height = height
        self.fps = fps
        self.playing = False
        self.paused = False
        self.frame_index = 0
        self.frames = []

        self.playback = (
            Playback()
        )  # creates an object for managing playback of a single audio file
        self.playback.load_file(audio_path)

        self.__flag = threading.Event()  # The flag used to pause the thread
        self.__flag.set()  # Set to True
        self.__running = threading.Event()  # Used to stop the thread identification
        self.__running.set()  # Set running to True

        # Start the audio playback in a separate thread

        # Load the video frames into memory
        with open(self.video_path, "rb") as file:
            while True:
                # Read a single frame
                raw_frame_data = file.read(self.width * self.height * 3)

                # Break the loop if we reach the end of the video
                if not raw_frame_data:
                    break

                # Convert the raw frame data to a NumPy array and reshape it
                frame = np.frombuffer(raw_frame_data, dtype=np.uint8).reshape(
                    self.height, self.width, 3
                )

                # Add the frame to the list of frames
                self.frames.append(frame)

        # Create the main window and canvas for displaying the video
        self.window = tk.Tk()
        self.window.title("Index Player")

        # Create the frame for the side menu
        self.side_menu_frame = tk.Frame(
            self.window, width=200, height=self.height, bg="grey"
        )
        self.side_menu_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create the listbox for displaying the scenes
        self.scene_listbox = tk.Listbox(self.side_menu_frame, width=20, height=20)
        self.scene_listbox.pack(side=tk.TOP, padx=10, pady=10)

        self.populate_scenes()

        self.canvas = tk.Canvas(
            self.window, width=self.width, height=self.height, bg="black"
        )
        self.canvas.pack()

        # Create the playback control buttons
        self.play_button = tk.Button(self.window, text="Play", command=self.play_video)
        self.pause_button = tk.Button(
            self.window, text="Pause", command=self.pause_video
        )
        self.stop_button = tk.Button(self.window, text="Stop", command=self.stop_video)
        self.prev_button = tk.Button(self.window, text="<<", command=self.prev_frame)
        self.next_button = tk.Button(self.window, text=">>", command=self.next_frame)
        self.play_button.pack(side=tk.LEFT)
        self.pause_button.pack(side=tk.LEFT)
        self.stop_button.pack(side=tk.LEFT)
        self.prev_button.pack(side=tk.LEFT)
        self.next_button.pack(side=tk.LEFT)

        self.scene_listbox.bind("<<ListboxSelect>>", self.select_scene)

        # Start the main event loop
        self.window.mainloop()

    def synchronize_audio_video(self):
        # self.highlight_current_item()
        if self.playing and not self.paused:
            current_audio_time = self.playback.curr_pos
            current_video_time = self.frame_index / self.fps

            if abs(current_audio_time - current_video_time) > 0.01:
                self.frame_index = int(current_audio_time * self.fps)

    def select_scene(self, event):
        # Get the selected item from the listbox

        selected_item = self.scene_listbox.curselection()
        if selected_item:
            # Get the label and timestamp for the selected item
            label = self.scene_listbox.get(selected_item[0])
            label = label.strip("-")
            label = label.strip("|")
            timestamp = self.timestamp_dict[label]

            # Set the current frame index based on the timestamp
            self.frame_index = int(timestamp * self.fps)
            self.show_frame()
            self.playback.seek(timestamp)
            
            if(not self.paused):
                self.play_video()

    def populate_scenes(self):
        scenes = [(label, timestamp) for label, timestamp in self.timestamp_dict.items()]
        for i, (label, timestamp) in enumerate(scenes):
            if(label.find("Shot") != -1):
                label = "--|" + label
            if(label.find("Subshot") != -1):
                label = "----|" + label
            start_frame = int(timestamp * self.fps)
            end_frame = min((i + 1) * self.fps * 10, len(self.frames))
            self.scene_listbox.insert("end", label)

    def prev_frame(self):
        if self.frame_index > 0:
            self.frame_index -= 90
            self.show_frame()
            self.playback.seek(self.playback.curr_pos - 3)
            self.highlight_current_item()

    def next_frame(self):
        if self.frame_index < len(self.frames) - 1:
            self.frame_index += 90
            self.show_frame()
            self.playback.seek(self.playback.curr_pos + 3)
            self.highlight_current_item()

    def play_video(self):
        if not self.playing:
            if self.paused:
                self.paused = False
                self.playback.resume()
            else:
                self.playback.play()
                selected_item = self.scene_listbox.curselection()
                if selected_item:
                    label = self.scene_listbox.get(selected_item[0])
                    label = label.strip("-")
                    label = label.strip("|")
                    timestamp = self.timestamp_dict[label]
                    self.frame_index = int(timestamp * self.fps)
                    self.show_frame()
                    self.playback.seek(timestamp)
                    self.playing = True
                    self.paused = False
                else:
                    self.frame_index = 0

            self.playing = True
            self.play_frames()

    def pause_video(self):
        if self.playing:
            self.paused = True
            self.playing = False
            self.playback.pause()

    def stop_video(self):
        self.playing = False
        self.paused = False
        # self.frame_index = 0
        self.show_frame()
        self.playback.stop()

    def play_frames(self):
        if self.playing:
            if self.paused:
                self.window.after(100, self.play_frames)
            else:
                self.synchronize_audio_video()
                self.show_frame()
                self.frame_index += 1
                if self.frame_index >= len(self.frames):
                    self.stop_video()
                else:
                    self.window.after(int(1000 / self.fps), self.play_frames)

    def show_frame(self):
        if self.frame_index >= len(self.frames):
            self.frame_index = 0
            self.playback.seek(0)
            self.show_frame()

        frame = self.frames[self.frame_index]

        # Create a PhotoImage from the frame
        photo = ImageTk.PhotoImage(image=Image.fromarray(frame))

        # Display the PhotoImage in the canvas
        self.canvas.create_image(0, 0, anchor=tk.NW, image=photo)
        self.canvas.image = photo
        self.highlight_current_item()

    def play_audio(self):
        audio = AudioSegment.from_wav(self.audio_path)
        play(audio)

    def highlight_current_item(self):
        current_time = self.frame_index / self.fps
        current_label = None

        for label, timestamp in self.timestamp_dict.items():
            if timestamp <= current_time:
                current_label = label
            else:
                break

        if current_label:

            if(current_label.find("Shot") != -1):
                current_label = "--|" + current_label
            if(current_label.find("Subshot") != -1):
                current_label = "----|" + current_label

            # Find the index of the current_label in the listbox
            listbox_index = self.scene_listbox.get(0, tk.END).index(current_label)
            # Clear the previous selection
            self.scene_listbox.selection_clear(0, tk.END)
            # Select the current item
            self.scene_listbox.selection_set(listbox_index)
            # Ensure the selected item is visible in the listbox
            self.scene_listbox.see(listbox_index)



if __name__ == "__main__":
    
#     n = len(sys.argv)
#     print("Total arguments passed:", n)
 
# # Arguments passed
#     print("\nName of Python script:", sys.argv[0])
#     print("\n Video File used : ",sys.argv[1])
#     print("\n Audio File used : ",sys.argv[2])

    # video_path = "The_Long_Dark_rgb/InputVideo.rgb"
    # audio_path = "The_Long_Dark_rgb/InputAudio.wav"
    video_path = "The_Great_Gatsby_rgb/InputVideo.rgb"
    audio_path = "The_Great_Gatsby_rgb/InputAudio.wav"
    # video_path = "Ready_Player_One_rgb/InputVideo.rgb"
    # audio_path = "Ready_Player_One_rgb/InputAudio.wav"
    
    # video_path = sys.argv[1]
    # audio_path = sys.argv[2]
    width = 480  # Replace with the actual width of the video
    height = 270  #
    fps = 30

    timestamp_dict = algo(video_path, audio_path)
    print(timestamp_dict)
    # print("did this work?")



    # Create a VideoPlayer object and show it
    player = VideoPlayer(video_path, audio_path, width, height, fps, timestamp_dict)
    player.playback.stop()
