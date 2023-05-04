from algorithm import scenes
from algorithm import shots
from algorithm import subshots


def get_scene_shot_subshot(video_file, audio_file):
    frame_width = 480
    frame_height = 270
    frame_per_second = 30

    shotList = shots.getshots(video_file, frame_width, frame_height)
    sceneList = scenes.detect_scenes(
        video_file, frame_width, frame_height, frame_per_second
    )
    subshotList = subshots.getsubshots(video_file, frame_width, frame_height)

    scene_count = 1
    shot_count = 1
    subshot_count = 1

    result = {}
    # print(sceneList)
    for scene in sceneList:
        result["Scene" + str(scene_count)] = scene[0]
        scene_count += 1
    for shot in shotList:
        result["Shot" + str(shot_count)] = shot[0]
        shot_count += 1
    for subshot in subshotList:
        result["Subshot" + str(subshot_count)] = subshot
        subshot_count += 1

    # filter list to remove similar timestamps
    x = sorted(result.items(), key=lambda item: item[1])
    phantomShots = []
    todel = []

    prev_shot_count = 0
    for i in range(len(x)):
        label, timestamp = x[i]

        if(label.find("Shot") != -1):
            labelCp = label.replace("Shot", "")
            prev_shot_count = int(labelCp)

        if(label.find("Subshot") != -1):
            # if the timestamp of the next item is within 0.1 second of the current item, delete the current item
            if(i < len(x) - 1 and x[i + 1][1] - timestamp < 0.1):
                todel.append(label)
            elif(i > 1 and timestamp - x[i - 1][1] < 0.1):
                todel.append(label)

            # if the previous item is not a subshot but is a scene, insert a phantom subshot with the same timestamp as the scene
            if(i > 1 and x[i - 1][0].find("Scene") != -1):
                # shot_count+=1
                print("inserting phantom subshot at " + str(prev_shot_count+0.5))
                phantomShots.append(("Shot"+str(prev_shot_count+0.5), x[i - 1][1]))

    for el in phantomShots:
        x.append(el)

    x = sorted(x, key=lambda item: item[1])

    
    result1 = {k: v for k, v in x}
    #delete all labels in x if the index is in todel
    for i in todel:
        del result1[i]
    
    return result1


