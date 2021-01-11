# coding: utf-8
"""
this file contains components with preprocessing

"""

import itertools
import re
from bisect import insort


__all__ = ["PriorityQueue", "ExtractNumber"]


class PriorityQueue:
    """
    Easy priority queue implemented by Insort

    """

    def __init__(self):
        self._pq = []
        self._entry_map = {}
        self._counter = itertools.count()
        self.priority = lambda p: -int(p or 0)

    def add(self, task, priority=None):
        """
        add task according priority
        del old entry from pq if task in map
        Args:
            task (str): plugin name, corresponding to crawler class
            priority (int): usually 0 and 1
        """
        if task in self._entry_map:
            old_entry = self._entry_map.pop(task)
            self._pq.remove(old_entry)
        # queue consists of list form
        entry = [self.priority(priority), next(self._counter), task]
        self._entry_map[task] = entry
        insort(self._pq, entry)

    def pop(self):
        """
        shift and return value

        Returns: the last value in the queue

        """
        try:
            return self._pq.pop(0)[-1]
        except IndexError:
            pass

    def empty(self):
        """
        check whether the queue is empty

        Returns:
            bool: false if empty

        """
        return bool(not self._pq)

    @classmethod
    def get(cls, n: str, website: list):
        """
        init plugin priority, adjust according to number
        Args:
            n (str): id
            website (list): plugin name

        Returns: priorities obj

        """
        pq = cls()
        for w in website:
            pq.add(w, 0)
        # if re.match(r"^\d{5,}", n) or "heyzo" in n.lower():
        #     pq.add("avsox", 1)
        # elif re.match(r"\d+[a-zA-Z]+-\d+", number) or "siro" in number.lower():
        # cls.add("mgstage", 1)
        # elif (re.match(r"\D{2,}00\d{3,}", number) and "-" not in number
        #       and "_" not in number):
        #     cls.add("dmm", 1)
        # elif re.search(r"\D+\.\d{2}\.\d{2}\.\d{2}", number):
        #     cls.add("javdb", 1)
        # elif "fc2" in number.lower():
        #     cls.add("fc2", 1)
        # elif "rj" in number.lower():
        #     cls.add("dlsite", 1)

        return pq


class ExtractNumber:
    _banned = [
        r"cd\d$", "1080p", "1pon", ".com", "nyap2p", "22-sht.me", "xxx", "carib"
    ]

    def banned(self, name, banned=None):
        banned = self._banned if banned is None else set(banned + self._banned)
        pattern = re.compile(r"\b(" + "|".join(banned) + ")\\W", re.I)
        return pattern.sub("", name).rstrip("-cC")

    @staticmethod
    def west(name):
        if obj := re.search(r"^\D+\d{2}\.\d{2}\.\d{2}", name):
            if sec_obj := re.search(
                    r"^\D+\d{2}\.\d{2}\.\d{2}\.\D+", name, flags=re.I
            ):
                return sec_obj.group()
            return obj.group()

    @staticmethod
    def xxxav(name):
        if obj := re.search(r"XXX-AV-\d{4,}", name.upper(), flags=re.I):
            return obj.group()

    @staticmethod
    def tokyohot(name):
        if obj := re.search(r"n[1|0]\d{3}", name, flags=re.I):
            return obj.group()

    @staticmethod
    def luxu(name):
        if obj := re.search(r"\d{0,3}luxu[-_]\d{4}", name, re.I):
            return obj.group()

    @staticmethod
    def fc2(name):
        if "ppv" in name.lower():
            # if has line, del ppv
            if re.search(r"ppv\s*[-|_]\s*\d{6,}", name, flags=re.I):
                name = re.sub(r"ppv", "", name, flags=re.I)
            # if no line, replace ppv with line
            name = re.sub(
                r"\s{0,2}ppv\s{0,2}", "-", name, flags=re.I
            )
        # if fcxxxx, replace fc with fc2-
        if re.search(r"fc[^2]\d{5,}", name, re.I):
            name = name.replace("fc", "fc2-").replace("FC", "FC2-")
        if obj := re.search(r"fc2[-_]\d{6,}", name, flags=re.I):
            return obj.group()

    @staticmethod
    def regular(name):
        regex = [
            r"[a-z]{2,5}[-_]\d{2,4}",  # bf-123 abp-454 mkbd-120  kmhrs-026
            r"[a-z]{4}[-_][a-z]\d{3}",  # mkbd-s120
            r"\d{6,}[-_][a-z]{4,}",  # 111111-MMMM
            r"\d{6,}[-_]\d{3,}",  # 111111-111
            r"n[-_]*[1|0]\d{3}",  # n1111,n-1111
        ]
        for r in regex:
            if searchobj := re.search(r, name, flags=re.I):
                return searchobj.group()

    @staticmethod
    def no_line(name):
        regex = [
            r"([a-z]{2,5})(\d{2,3})",  # bf123 abp454 mkbd120  kmhrs026
            r"(\d{6,})([a-z]{4,})",  # 111111MMMM
        ]
        for r in regex:
            if obj := re.search(r, name, flags=re.I):
                return obj.group(1) + "-" + obj.group(2)

    def __call__(self, name, *args, **kwargs):
        name = self.banned(name.stem, *args, **kwargs)
        funcs = [self.west(name), self.xxxav(name), self.tokyohot(name), self.luxu(name)]
        for func in funcs:
            if func is not None:
                return func
        if re.search(r'fc.*?\d{5,}', name, flags=re.I):
            return self.fc2(name)
        if "-" in name or "_" in name:
            return self.regular(name)
        return self.no_line(name)
