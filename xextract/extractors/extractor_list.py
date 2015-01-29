from xextract.utils.python import flatten


class XPathExtractorList(list):
    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))

    def select(self, xpath):
        return self.__class__(flatten(x.select(xpath) for x in self))

    def extract(self):
        return [x.extract() for x in self]
