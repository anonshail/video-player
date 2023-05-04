import cv2
import numpy as np


def read_rgb_video(file_path, width, height):
    with open(file_path, "rb") as file:
        while True:
            buffer = file.read(width * height * 3)
            if not buffer:
                break

            frame = np.frombuffer(buffer, dtype=np.uint8).reshape(height, width, 3)
            yield frame


def detect_scenes(video_path, width, height, frame_rate, threshold=25):
    frame_duration = 1 / frame_rate
    prev_frame = None
    scene_start_time = 0
    frame_count = 0
    scene_timings = []

    for frame in read_rgb_video(video_path, width, height):
        if prev_frame is not None:
            frame_diff = cv2.absdiff(frame, prev_frame)
            avg_diff = frame_diff.mean()

            if avg_diff > threshold:
                scene_start_time = frame_count * frame_duration
                print(f"Scene start time: {scene_start_time:.2f}s")
                scene_timings.append(scene_start_time)

        prev_frame = frame
        frame_count += 1
    total_time = frame_count / frame_rate
    result = [
        (scene_timings[i - 1], scene_timings[i]) if i > 0 else (0, scene_timings[i])
        for i in range(len(scene_timings))
    ] + [(scene_timings[-1], total_time)]

    i = 1
    while i < len(result):
        if result[i][0] - result[i - 1][1] < 4:
            del result[i]
        else:
            i += 1

    print(result)
    return result


if __name__ == "__main__":
    video_path = "Ready_Player_One_rgb/InputVideo.rgb"
    width, height = 480, 270
    frame_rate = 30

    detect_scenes(video_path, width, height, frame_rate)
