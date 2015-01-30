class XPathExtractorList(list):
    def __getslice__(self, i, j):
        return self.__class__(list.__getslice__(self, i, j))

    def select(self, xpath):
        return self.__class__(node for extractor in self for node in extractor.select(xpath))

    def extract(self):
        return [x.extract() for x in self]
