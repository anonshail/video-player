import cv2
import numpy as np
import numpy as np


def read_rgb_frame(file, width, height):
    data = file.read(width * height * 3)
    if not data:
        return None
    img = np.frombuffer(data, dtype=np.uint8)
    img = img.reshape(height, width, 3)
    return img


def detect_fast_moving_objects(
    video_file, width, height, threshold=60.0, changed_pixel_ratio=0.009
):
    pixel_list = []
    with open(video_file, "rb") as f:
        frame1 = read_rgb_frame(f, width, height)
        frame2 = read_rgb_frame(f, width, height)

        frame_counter = 0
        time_counter = 0

        fast_moving_scenes = []
        fps = 30

        while frame1 is not None and frame2 is not None:
            frame_counter += 1
            time_counter += 1 / fps

            gray1 = cv2.cvtColor(frame1, cv2.COLOR_RGB2GRAY)
            gray2 = cv2.cvtColor(frame2, cv2.COLOR_RGB2GRAY)

            diff = cv2.absdiff(gray1, gray2)

            _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)

            num_changed_pixels = np.sum(thresh > 0)

            if num_changed_pixels > gray1.size * changed_pixel_ratio:
                fast_moving_scenes.append(time_counter)
                pixel_list.append(num_changed_pixels)

            frame1 = frame2
            frame2 = read_rgb_frame(f, width, height)

    return fast_moving_scenes, pixel_list


def getsubshots(video_file, width, height):
    fast_moving_scenes, pixel_list = detect_fast_moving_objects(
        video_file, width, height
    )
    # print("Fast-moving scenes detected at the following times (in seconds):")
    threshold_percentile = np.percentile(pixel_list, 98)

    subshots = []

    for i in range(len(pixel_list)):
        if pixel_list[i] > threshold_percentile:
            subshots.append(fast_moving_scenes[i])
            # print("Time: " + str(fast_moving_scenes[i]))

    return subshots


if __name__ == "__main__":
    video_file = "The_Long_Dark_rgb/InputVideo.rgb"
    width = 480
    height = 270
    subshot_timing = getsubshots(video_file, width, height)
    # print(subshot_timing)
