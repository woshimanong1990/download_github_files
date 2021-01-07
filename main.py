# coding:utf-8
import os
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


class DownloadFile:
    def __init__(self, url, download_directory):
        """
        url: The url will be download
        download_directory: dir to save files
        """
        self.url = url
        self.download_directory = download_directory

    def get_html(self, url, use_proxy=False):
        # get html content
        headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.111 Safari/537.36",
        }
        if use_proxy:
            proxy = {"http": "socks5://127.0.0.1:1080", "https": "socks5://127.0.0.1:1080"}
        else:
            proxy = None
        res = requests.get(url, headers=headers, verify=False, timeout=60, proxies=proxy)
        res.raise_for_status()
        return res.content

    def get_parse_soup(self, content):
        return BeautifulSoup(content, "html.parser")

    def parse(self, url):
        # parse file url. if it is dir_urls, continue to parse
        content = self.get_html(url)
        soup = self.get_parse_soup(content)
        rows = soup.find_all("div", role="row", class_="Box-row")
        dir_urls = []
        file_urls = []
        for r in rows:
            if r.svg is None:
                continue
            file_type = r.svg.attrs["aria-label"]
            link = r.find("a", class_="js-navigation-open")
            url = urljoin("https://github.com", link["href"])
            if file_type == "Directory":
                dir_urls.append(url)
            else:
                file_urls.append(url)
        for url in dir_urls:
            file_urls.extend(self.parse(url))
        return file_urls

    def parse_relative_path(self, url):
        # get relative_path according to the url
        _url = self.url if self.url.endswith("/") else self.url + "/"
        branch_url = urljoin(_url,  "tree/master/") if "/tree/" not in self.url else self.url
        child_url = urlparse(url).path
        root_url = urlparse(branch_url).path
        if "/blob/" in child_url:
            child_url = child_url.replace("/blob/", "/tree/", 1)
        relative_path = child_url.split(root_url)[1]
        return relative_path[1:] if relative_path.startswith("/") else relative_path

    def download_file(self, file_path, url, need_proxy=True):
        # for china user, need proxy :ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 1005
        if "/blob/" in url:
            url = url.replace("/blob/", "/")
        content = self.get_html(url, use_proxy=need_proxy)
        dir_path = os.path.dirname(file_path)
        if not os.path.isdir(dir_path):
            os.makedirs(dir_path)
        with open(file_path, "wb") as f:
            f.write(content)

    def run(self):
        file_urls = self.parse(self.url)
        for file_url in file_urls:
            raw_file_url = urljoin("https://raw.githubusercontent.com/", urlparse(file_url).path)
            relative_path = self.parse_relative_path(file_url)
            file_path = os.path.join(self.download_directory, relative_path)
            self.download_file(file_path, raw_file_url)


def main():
    url = "https://github.com/aosabook/500lines/tree/master/blockcode"
    dir_path = r'D:\tmp'
    raw_url = "https://raw.githubusercontent.com/aosabook/500lines/master/tex/ieee.csl"
    d = DownloadFile(url, dir_path)
    d.run()


if __name__ == "__main__":
    main()
