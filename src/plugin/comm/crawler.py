# coding: utf-8
import logging
import re
import shutil
from collections import defaultdict
from http.cookiejar import LWPCookieJar
from pathlib import Path
from urllib.parse import parse_qs, urlparse, quote_plus
from urllib.request import getproxies

import requests
from requests.adapters import HTTPAdapter, Retry
from requests_html import HTML, HTMLSession


class Metadata(defaultdict):
    """
    A dictionary supporting dot notation. and nested access
    do not allow to convert existing dict object recursively
    """

    def __init__(self):
        super(Metadata, self).__init__(Metadata)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            return ""

    def __setattr__(self, key, value):
        self[key] = value


class RequestHandler:
    """
    RequestHandler
    # https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
    """

    def __init__(self, config, *args, **kwargs):
        """
        Instantiates a new request handler object.
        """
        self._status_forcelist = ["413", "429", "500", "502", "503", "504"]
        self._total = 3
        self._backoff_factor = 1
        self.timeout = config.network.timeout
        self.delay = config.network.delay
        self.enable_proxy = config.network.enable_proxy
        self.proxy_type = config.network.proxy_type
        self.proxy_host = config.network.proxy_host

    @property
    def proxy_strategy(self):
        # proxy in config file
        if self.enable_proxy and self.proxy_type in ["http", "socks5", "socks5h"]:
            proxy = "{}://{}".format(
                self.proxy_type, self.proxy_host
            )
            return {"http": proxy, "https": proxy}
        # logger.debug('using system proxy')
        return getproxies()

    @property
    def retry_strategy(self) -> Retry:
        """
        Using Transport Adapters we can set a default timeout for all HTTP calls
        Add a retry strategy to your HTTP client is straightforward.
        We create a HTTPAdapter and pass our strategy to the adapter.
        """
        return Retry(
            total=self._total,
            status_forcelist=self._status_forcelist,
            backoff_factor=self._backoff_factor,
        )

    @property
    def session(self):
        """
        Often when using a third party API you want to verify that the returned response is indeed valid.
        Requests offers the shorthand helper raise_for_status()
        which asserts that the response HTTP status code is not a 4xx or a 5xx,
        """
        session = HTMLSession()
        adapter = HTTPAdapter(max_retries=self.retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        assert_status_hook = (
            lambda response, *args, **kwargs: response.raise_for_status()
        )
        # the requests library offers a 'hooks' interface
        # where you can attach callbacks on certain parts of the request process.
        session.hooks["response"] = [assert_status_hook]
        return session

    def get(self, url: str, **kwargs):
        """
        Returns the GET request encoded in `utf-8`.
        """
        try:
            response = self.session.get(
                url, timeout=self.timeout, proxies=self.proxy_strategy, **kwargs
            )
            self.session.close()
            response.encoding = "utf-8"
            return response
        except requests.exceptions.RequestException as exc:
            logging.info(f"RequestError: {exc}")

    def post(self, url, data, **kwargs):
        """
        Returns the POST request
        """
        try:
            response = self.session.post(
                url, timeout=self.timeout, data=data, proxies=self.proxy_strategy, **kwargs,
            )
            self.session.close()
            return response
        except requests.exceptions.RequestException as exc:
            logging.info(f"RequestError: {exc}")


class CrawlerBase(RequestHandler):

    def __init__(self, number, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.number = number
        self._data = Metadata()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        self._data = data

    def get_parser_html(self, url: str, **kwargs):
        """
        Return the parser element
        """
        res = self.get(url, **kwargs)
        if res is not None:
            return HTML(html=res.text)

    def default_search(
            self, number, search_url, waterfall_xpath, id_xpath, url_xpath, **kwargs
    ):
        """
        get html by default search

        """
        search_page = self.get_parser_html(search_url, **kwargs)
        parents = search_page.xpath(waterfall_xpath)

        for element in parents:
            num = element.xpath(id_xpath, first=True)
            if num is not None:
                res = re.match(
                    "".join(filter(str.isalnum, number)),
                    "".join(filter(str.isalnum, num)),
                    flags=re.I,
                )
                if res is not None:
                    return element.xpath(url_xpath, first=True)

    def get_outline(self, number):
        # jav321
        res = self.post("https://www.jav321.com/search", data={"sn": number})
        if res is not None:
            res.encoding = "utf-8"
            html = HTML(html=res.text)
            outline = html.xpath(
                '//div[@class="panel-body"]/div[@class="row"]/div[@class="col-md-12"]/text()', first=True
            )
            if outline is not None:
                return outline

        # dmm
        g = GSearch()
        dmm_link = g.search(number, "dmm.co.jp")
        if dmm_link is not None:
            res = self.get_parser_html(dmm_link)
        else:
            # default search
            ...
        if res is not None:
            outline = res.xpath(
                '//div[@class="mg-b20 lh4"]/p[@class="mg-b20"]/text()', first=True
            )
            if outline is not None:
                return outline
        return ""

    def download(self, url, file_name):
        r = self.get(url, stream=True)
        if r.status_code == 200:
            r.raw.decode_content = True

            with open(file_name, "wb") as f:
                shutil.copyfileobj(r.raw, f)
            logging.info(f"sucessfully download: {file_name}")
        logging.info(f"fail download: {file_name}")

    def download_all(self, img_url: dict, folder):
        for name, url in img_url.items():
            self.download(url, folder.joinpath(name + "jpg"))


class GSearch(RequestHandler):
    """
    mainly used to reduce the number of access to the target site,
    it should be a better way
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cookie = Path(__file__).parent.parent.joinpath(".google-cookie")
        if cookie.exists():
            self.cookie_jar = LWPCookieJar(str(cookie))
            # noinspection PyBroadException
            try:
                self.cookie_jar.load(ignore_discard=True, ignore_expires=True)
            except Exception:
                pass
        else:
            self.cookie_jar = None
            self.get_page("https://www.google.com/")

    def get_page(self, url):
        """
        load cookie, if not ,get page and save

        """
        response = self.session.get(
            url,
            timeout=self.timeout,
            proxies=self.proxy_strategy,
            cookies=self.cookie_jar,
        )
        response.encoding = "utf-8"
        html = response.text
        # noinspection PyBroadException
        try:
            self.cookie_jar.save(ignore_discard=True, ignore_expires=True)
        except Exception:
            pass
        return html

    @staticmethod
    def filter(link):
        """
        get original url
        """
        # refer to https://github.com/MarioVilas/googlesearch
        # noinspection PyBroadException
        try:
            if link.startswith("/url?"):
                link = parse_qs(urlparse(link, "http").query)["q"][0]
            url = urlparse(link, "http")
            if url.netloc and "google" not in url.netloc:
                return link
        except Exception:
            ...

    @staticmethod
    def extract(html, number):
        """
        extract url and title

        """
        html = HTML(html=html)
        link_content = html.xpath("//a")
        # this list needs to be maintained
        title_xpath = ["//h3/div/text()", "//h3/span/text()"]
        for content in link_content:
            link = content.xpath("//@href", first=True)
            if link is not None:
                if re.search(
                        "".join(filter(str.isalnum, number)),
                        "".join(filter(str.isalnum, link)),
                        flags=re.I,
                ):
                    return link
                # else check title
                for xpath in title_xpath:
                    title = content.xpath(xpath, first=True)
                    if title is None:
                        continue
                    if re.search(
                            "".join(filter(str.isalnum, number)),
                            "".join(filter(str.isalnum, title)),
                            flags=re.I,
                    ):
                        return link

    def search(self, number, site):
        """
        can't use Chinese search, add hl-en

        """
        query = quote_plus(number + "+site:" + site)
        html = self.get_page(
            url=f"https://google.com/search?hl=en&q={query}&safe=off"
        )
        return self.filter(self.extract(html, number))
