import cv2
import numpy as np


def read_rgb_file(file_path, frame_width, frame_height):
    with open(file_path, "rb") as f:
        data = f.read()

    frame_size = frame_width * frame_height * 3
    num_frames = len(data) // frame_size
    frames = []

    for i in range(num_frames):
        frame_data = data[i * frame_size : (i + 1) * frame_size]
        frame = np.frombuffer(frame_data, dtype=np.uint8)
        frame = frame.reshape(frame_height, frame_width, 3)
        frames.append(frame)

    return frames


def calculate_dynamic_threshold(frames, multiplier=2.0):
    diffs = []
    prev_frame_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)

    for frame in frames[1:]:
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_frame_gray, frame_gray)
        mean_diff = np.mean(diff)
        diffs.append(mean_diff)

        prev_frame_gray = frame_gray

    diffs = np.array(diffs)
    mean_diff = diffs.mean()
    std_diff = diffs.std()

    threshold = mean_diff + multiplier * std_diff

    return threshold


def background_difference(frames, min_shot_duration=4):
    frame_rate = 30
    threshold = calculate_dynamic_threshold(frames)
    prev_frame_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    shot_start = 0
    shot_timings = []

    for frame_idx, frame in enumerate(frames[1:], start=1):
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(prev_frame_gray, frame_gray)
        mean_diff = np.mean(diff)

        if mean_diff > threshold:
            shot_end = frame_idx
            if (shot_end - shot_start) >= min_shot_duration:
                start_time = shot_start / frame_rate
                end_time = shot_end / frame_rate
                shot_timings.append((start_time, end_time))
                shot_start = shot_end

        prev_frame_gray = frame_gray

    return shot_timings


def getshots(video_file, frame_width, frame_height):
    frames = read_rgb_file(video_file, frame_width, frame_height)
    shot_timings = background_difference(frames)
    i = 1
    while i < len(shot_timings):
        if shot_timings[i][0] - shot_timings[i - 1][1] < 1.5:
            del shot_timings[i]
        else:
            i += 1
    return shot_timings


if __name__ == "__main__":
    video_file = "Ready_Player_One_rgb/InputVideo.rgb"
    frame_width = 480
    frame_height = 270

    shot_timings = getshots(video_file, frame_width, frame_height)
    print(shot_timings)

    # for idx, (start, end) in enumerate(shot_timings):
    # print(f"Shots {idx + 1}: {start:.2f} - {end:.2f}")
