import curses


class ColorManager(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            self = cls._instance
            self.colorCounter = 0
            self.colorPairs = {}

        return cls._instance

    def _scale_color(self, r, g, b):
        f = (curses.COLORS - 1) / 255
        rgb = (
            min(round(r * f), curses.COLORS - 1),
            min(round(g * f), curses.COLORS - 1),
            min(round(b * f), curses.COLORS - 1),
        )
        return rgb

    def get_color(self, r=None, g=None, b=None, name=None):

        if cp := self.colorPairs.get((r, g, b), None):
            return cp

        if cp := self.colorPairs.get((name), None):
            return cp

        if r is None or g is None or b is None:
            raise TypeError('r, g, b must have values from 0 to 255')

        self.colorCounter += 1
        r, g, b = self._scale_color(r, g, b)
        curses.init_color(self.colorCounter, *self._scale_color(r, g, b))
        curses.init_pair(self.colorCounter, self.colorCounter, -1)
        cp = curses.color_pair(self.colorCounter)
        self.colorPairs[(r, g, b)] = cp
        if name:
            self.colorPairs[name] = cp
        return cp

    def get(self, name):
        return self.get_color(name=name)
