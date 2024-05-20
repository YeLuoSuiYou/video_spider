import os

from tqdm import tqdm

import decord
import imageio


class VideoReaderWrapper(decord.VideoReader):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seek(0)

    def __getitem__(self, key):
        frames = super().__getitem__(key)
        self.seek(0)
        return frames


# Save the keyframes with type I
def save_i_keyframes(video_fn, v_id, s_path):
    decord_vr = VideoReaderWrapper(video_fn, num_threads=1)
    i_frames = decord_vr.get_key_indices()
    if len(i_frames) == 0:
        print("No I-frames in " + video_fn)
        del decord_vr, i_frames
        return
    keyframes = decord_vr.get_batch(i_frames).asnumpy()
    milliseconds = decord_vr.get_frame_timestamp(i_frames)
    milliseconds = [int(x[0] * 1000) for x in milliseconds]
    for i, keyframe in enumerate(keyframes):
        # Calculate the timestamp of the keyframe
        millisecond = milliseconds[i]
        seconds = millisecond // 1000
        millisecond = millisecond % 1000
        minutes = 0
        hours = 0
        if seconds >= 60:
            minutes = seconds // 60
            seconds = seconds % 60

        if minutes >= 60:
            hours = minutes // 60
            minutes = minutes % 60
        # timestamp of the keyframe
        frame_time = (
            str(int(hours))
            + "-"
            + str(int(minutes))
            + "-"
            + str(int(seconds))
            + "-"
            + str(int(millisecond))
        )
        # Save the image
        outname = str(v_id) + "_keyframe_" + str(frame_time) + ".jpg"
        save_name = s_path + "/" + outname
        imageio.imwrite(save_name, keyframe)
    # release the video reader
    del decord_vr, keyframes, i_frames, milliseconds


def process_video(v_path, save_path, video_id):
    save_name = video_id
    s_path = save_path + "/" + save_name
    if os.path.exists(s_path):
        return
    os.makedirs(s_path, exist_ok=True)
    # Save the keyframes to the target dir
    save_i_keyframes(v_path, save_name, s_path)


if __name__ == "__main__":
    video_dir = ""
    save_path = ""
    video_paths = []
    for file in os.listdir(video_dir):
        if file.endswith(".mp4"):
            video_paths.append((os.path.join(video_dir, file), file.split(".")[0]))

    for video_path in tqdm(video_paths, total=len(video_paths)):
        try:
            process_video(video_path[0], save_path, video_path[1])
        except Exception as e:
            print(e)
