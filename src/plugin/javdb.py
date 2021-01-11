# coding: utf-8

import random

from .comm.crawler import CrawlerBase, GSearch
from .comm.registry import plug, func


# from core.config import cfg


@plug
class Javdb(CrawlerBase, GSearch):
    _url = ["https://javdb.com", "https://javdb4.com", "https://javdb6.com"]

    def __init__(self, number, config):
        super().__init__(number, config)

        self.base_url = random.choice(self._url)

        # cfg = set_config()
        headers = {
            # "Cookie": cfg.request.cookie.get["javdb"],
            "referer": self.base_url,
        }
        url = self.search(self.number, self.base_url.replace("https://", ""))
        if url is not None:
            self.html = self.get_parser_html(url, headers=headers)
        else:
            self.html = self.search_url(headers)
        if self.html is None:
            return

    def search_url(self, headers):
        """

        Returns: parser html

        """
        search_url = self.base_url + "/search?q=" + self.number + "&f=all"
        xpath = [
            '//div[@class="grid-item column"]',
            '//a/div[@class="uid"]/text()',
            "//a/@href",
        ]
        real_url = self.default_search(
            self.number, search_url, xpath[0], xpath[1], xpath[2], headers=headers
        )
        if real_url is not None:
            return self.get_parser_html(
                self.base_url + real_url, headers=headers
            )

    @func
    def small_cover(self):
        pass

    # def cover(self):
    #     try:
    # self.data.cover = self.html.xpath('//img[@class="video-cover"]/@src')
    # except IndexError:
    #     self.data.cover = ""
    @func
    def outline(self):
        self.data.outline = self.get_outline(self.number)

    @func
    def info(self):
        """
        number, release, length, actor, director, studio, label, series, genre
        """
        self.data.title = self.html.xpath(
            '//h2[@class="title is-4"]/strong/text()', first=True
        )

        info = self.html.xpath(
            '//nav[@class="panel video-panel-info"]', first=True
        )
        self.data.number = info.xpath(
            "//div[1]/a/@data-clipboard-text", first=True
        )
        self.data.release = info.xpath(
            '//div/strong[contains(., "日期")]/../span/text()', first=True
        )
        runtime = info.xpath(
            '//div/strong[contains(., "時長")]/../span/text()', first=True
        )
        self.data.runtime = runtime.replace("分鍾", "") if runtime is not None else ""
        self.data.director = info.xpath(
            '//div/strong[contains(., "導演")]/../span/a/text()', first=True
        )
        self.data.studio = info.xpath(
            '//div/strong[contains(., "片商")]/../span/a/text()', first=True
        )
        self.data.series = info.xpath(
            '//div/strong[contains(., "系列")]/../span/a/text()', first=True
        )
        self.data.tags = info.xpath(
            '//div/strong[contains(., "類別")]/../span/a/text()'
        )
        self.data.actor = info.xpath(
            '//div/strong[contains(., "演員")]/../span/a/text()'
        )
