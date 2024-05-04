import argparse
import concurrent.futures
import re
import time

import requests
from openpyxl import Workbook
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from tqdm import tqdm


class GetInfo:
    def __init__(self, edge: webdriver.Edge, user_id: int, first_time=False):
        self.d = edge
        self.user_id = user_id
        self.base_url = f"https://space.bilibili.com/{user_id}/video"
        self.d.get(self.base_url)
        self.data_list = []
        self.urls = set()
        if first_time:
            time.sleep(10)
            print("速度扫码登入")

    def get_url(self):
        # 从当前页面获取所有视频的URL并保存到本地文件
        ul = WebDriverWait(self.d, 10).until(
            lambda x: x.find_element(By.XPATH, '//*[@id="submit-video-list"]/ul[1]')
        )
        lis = ul.find_elements(By.XPATH, "li")
        for li in lis:
            self.urls.add(li.get_attribute("data-aid"))

    def next_page(self):
        # 遍历所有页面，获取所有视频的URL）
        total = WebDriverWait(self.d, 10).until(
            lambda x: x.find_element(
                By.XPATH, '//*[@id="submit-video-list"]/ul[3]/span[1]'
            )
        )
        number = re.findall(r"\d+", total.text)
        total = int(number[0])

        for page in range(1, total):
            try:
                self.d.find_element(By.LINK_TEXT, "下一页").click()
                time.sleep(1)  # 等待页面加载
                self.get_url()  # 修复方法名错误
            except Exception as e:
                print(f"Failed to click next page: {e}")

    def get_single_video(self, url):
        with requests.Session() as session:
            session.headers.update(
                {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
                }
            )
            base_url = "http://www.bilibili.com/video/"
            title_pattern = re.compile(
                r'<title data-vue-meta="true">([^&amp;]+)</title>'
            )
            play_count_pattern = re.compile(r"视频播放量 (\d+)")
            full_url = base_url + url
            try:
                response = session.get(full_url)
                if response.status_code == 200:
                    string = response.text
                    title_match = title_pattern.search(string)
                    title = title_match.group(1) if title_match else "未找到匹配的内容"
                    play_count = (
                        play_count_pattern.search(string).group(1)
                        if play_count_pattern.search(string)
                        else "0"
                    )
                    video_info = {
                        "url": full_url,
                        "title": title,
                        "play_count": play_count,
                    }
                    return video_info
            except Exception as e:
                print(f"Failed to get video info for url {full_url}: {e}")
                return None

    def save_to_excel(self, filename):
        wb = Workbook()
        ws = wb.active
        ws.append(["url", "标题", "播放量"])  # 添加表头
        for video_info in self.data_list:
            ws.append(
                [
                    video_info["url"],
                    video_info["title"],
                    video_info["play_count"],
                ]
            )
            wb.save(filename)

    def run(self, save_path):
        # 运行整个流程
        self.get_url()  # 获取当前页面的视频URL
        self.next_page()  # 遍历所有页面获取视频URL

        data = self.urls

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(self.get_single_video, url) for url in data]
            for future in tqdm(
                concurrent.futures.as_completed(futures), total=len(futures)
            ):
                video_info = future.result()
                if video_info is not None:
                    self.data_list.append(video_info)

        # 所有线程完成后，保存数据到Excel
        self.save_to_excel(save_path)


args = argparse.ArgumentParser()
args.add_argument("--user_id", type=int, default=14781001)
args.add_argument("--save_path", type=str, default="./bilibili/")

args = args.parse_args()
user_id = args.user_id
save_path = args.save_path


if __name__ == "__main__":
    user_ids = [14781001, 401742377]
    edge = webdriver.Edge()
    for user_id in user_ids:
        obj = GetInfo(edge, user_id)
        info_save_path = save_path + f"{user_id}.xlsx"
        obj.run(info_save_path)
