# coding: utf-8
import random
import re

from .comm.crawler import CrawlerBase
from .comm.registry import plug, func


@plug
class Javbus(CrawlerBase):
    _url = [
        "https://www.fanbus.us/",
        "https://www.javbus.com/",
        "https://www.busdmm.one/"
    ]

    def __init__(self, number, config):
        super().__init__(number, config)
        base_url = random.choice(self._url)
        self.html = self.get_parser_html(base_url + number)
        # check self.html pass to registry, to decide whether to continue running the following functions
        if self.html is None:
            return

    @func
    def info(self):
        """
        title, number, year, length, actor, director, maker, genre, series
        """
        title = self.html.xpath(
            '//div[@class="container"]/h3/text()', first=True
        )
        self.data.title = title.lstrip(self.number + "-_ ")
        info = self.html.xpath(
            '//div[@class="col-md-3 info"]', first=True
        )
        self.data.number = info.xpath('//p[1]/span[2]/text()', first=True)
        self.data.release = info.xpath('//p[2]/text()', first=True)
        self.data.runtime = info.xpath('//p[3]/text()', first=True).replace("分鐘", "")
        self.data.director = info.xpath(
            '//p/span[contains(., "導演")]/../a/text()', first=True
        )
        self.data.studio = info.xpath(
            '//p/span[contains(., "製作商")]/../a/text()', first=True
        )
        self.data.publisher = info.xpath(
            '//p/span[contains(., "發行商")]/../a/text()', first=True
        )

        self.data.tags = info.xpath(
            '//p[position()<last()]/span[@class="genre"]/a/text()'
        )
        self.data.actor = info.xpath(
            '//p[last()]/span[@class="genre"]/a/text()'
        )

    @func
    def cover(self):
        """
        cover
        """
        self.data.cover = self.html.xpath('//a[@class="bigImage"]/img/@src', first=True)

    @func
    def cid(self):
        string = self.html.xpath("//a[contains(@class,'sample-box')][1]/@href", first=True)
        if string:
            cid = string.replace('https://pics.dmm.co.jp/digital/video/', '')
            self.data.cid = re.sub('/.*?.jpg', '', cid)

    # @func
    def outline(self):
        self.data.outline = self.get_outline(self.number)
