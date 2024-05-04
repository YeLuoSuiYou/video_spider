import yt_dlp
from openpyxl import Workbook


class YouTubeInfoExtractor:
    def __init__(self, video_list_id):
        self.video_list_id = video_list_id
        if "PL" in video_list_id:
            self.url = f"https://www.youtube.com/playlist?list={video_list_id}"
        else:
            self.url = f"https://www.youtube.com/{video_list_id}/videos"

    def get_video_info(self):
        ydl_opts = {
            "skip_download": True,
            "dump_single_json": True,
            "extract_flat": True,
            "ignoreerrors": True,
            "noprogress": True,
            "writesubtitles": False,
            "writeinfojson": False,
            "writeannotations": False,
            "write_all_thumbnails": False,
            "simulate": False,
            "youtube_include_dash_manifest": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            self.video_info = ydl.extract_info(self.url, download=False)

    def extract_video_data(self):
        video_urls = [video["url"] for video in self.video_info["entries"]]
        video_titles = [video["title"] for video in self.video_info["entries"]]
        video_duration = [video["duration"] for video in self.video_info["entries"]]

        self.data_list = []
        for data in zip(video_urls, video_titles, video_duration):
            self.data_list.append(
                {
                    "url": data[0],
                    "title": data[1],
                    "duration": data[2],
                }
            )

    def save_to_excel(self, filename):
        wb = Workbook()
        ws = wb.active
        ws.append(["url", "title", "duration"])  # 添加表头
        for video_info in self.data_list:
            ws.append(
                [
                    video_info["url"],
                    video_info["title"],
                    video_info["duration"],
                ]
            )
        wb.save(filename)

    def run(self, filename):
        self.get_video_info()
        self.extract_video_data()
        self.save_to_excel(filename)


if __name__ == "__main__":
    video_list_id = "PLu7K6PY4km6pSv3yMJE9YJMq3NKUMaDRC"
    output_dir = "youtube"
    output_filename = f"{output_dir}/{video_list_id}.xlsx"
    extractor = YouTubeInfoExtractor(video_list_id)
    extractor.run(output_filename)
