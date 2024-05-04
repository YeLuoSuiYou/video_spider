import os
import subprocess
import yt_dlp
import cv2
import argparse
import openpyxl

from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm


class VideoDownloader:
    def __init__(self, video_links, output_path, max_threads=4):
        self.video_links = video_links
        self.video_output_path = output_path
        self.max_threads = max_threads

    def download_clip(self, video_link):
        if "youtube" in video_link:
            video_id = video_link.split("=")[-1]
        elif "bilibili" in video_link:
            video_id = video_link.split("/")[-1]

        output_filename = f"{video_id}.mp4"
        output_path = os.path.join(self.video_output_path, output_filename)
        if os.path.exists(output_path):
            print(f"Clip {video_id} already exists. Skipping download.")
            return

        print(f"Downloading clip: {video_id}")
        try:
            # Download the clip using yt-dlp
            command = [
                "yt-dlp",
                "--verbose",
                "--no-progress",
                "--format",
                "bv*[height<=720]/mp4",
                "--output",
                output_path,
                video_link,
            ]
            subprocess.check_call(command)

        except subprocess.CalledProcessError as e:
            print(f"Error occurred while downloading {video_link}: {str(e)}")
            return
        except Exception as ex:
            print(f"Unknown error occurred while downloading {video_link}: {str(ex)}")
            return

    def download_clips(self):
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [
                executor.submit(self.download_clip, video_link)
                for video_link in self.video_links
            ]
            for future in tqdm(as_completed(futures), total=len(futures)):
                future.result()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download YouTube videos")
    parser.add_argument(
        "--max_threads",
        type=int,
        default=4,
        help="Maximum number of threads to use for downloading videos",
    )
    parser.add_argument(
        "--video_output_path",
        type=str,
        default="videos",
        help="Path to save the downloaded videos",
    )
    parser.add_argument(
        "--xlsx_paths",
        type=str,
        default="./",
        help="Path to the xlsx file containing video linksk",
    )

    args = parser.parse_args()
    max_threads = args.max_threads
    video_output_path = args.video_output_path
    xlsxs = args.xlsx_paths
    video_links = []

    # get all xlsxs in the directory
    for dirs, _, files in os.walk(xlsxs):
        for file in files:
            if file.endswith(".xlsx"):
                file_path = os.path.join(dirs, file)
                table = openpyxl.load_workbook(file_path).active
                # 获取table的前十行的url列, 跳过表头
                for row in table.iter_rows(min_row=2, max_row=20, max_col=1):
                    for cell in row:
                        video_links.append(cell.value)

    print(len(video_links))
    downloader = VideoDownloader(video_links, video_output_path, max_threads)

    downloader.download_clips()
