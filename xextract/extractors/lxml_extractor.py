from lxml import etree

from .extractor_list import XPathExtractorList


class XPathExtractor(object):
    _parser = etree.HTMLParser
    _tostring_method = 'html'

    def __init__(self, text=None, url=None, namespaces=None, _root=None):
        self.url = url
        self.namespaces = namespaces
        if _root is None:
            _root = self._get_root(text)
        self._root = _root

    def _get_root(self, text):
        text = text.strip() or '<html/>'
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        parser = self._parser(recover=True, encoding='utf-8')
        return etree.fromstring(text, parser=parser, base_url=self.url)

    def select(self, xpath):
        if not hasattr(self._root, 'xpath'):
            return XPathExtractorList([])

        if isinstance(xpath, etree.XPath):
            result = xpath(self._root)
        else:
            result = self._root.xpath(xpath, namespaces=self.namespaces)

        if not isinstance(result, list):
            result = [result]

        return XPathExtractorList(self.__class__(_root=x, namespaces=self.namespaces) for x in result)

    def extract(self):
        try:
            return etree.tostring(self._root, method=self._tostring_method,
                                  encoding=unicode, with_tail=False)
        except (AttributeError, TypeError):
            if self._root is True:
                return u'1'
            elif self._root is False:
                return u'0'
            else:
                return unicode(self._root)

    def register_namespace(self, prefix, uri):
        if self.namespaces is None:
            self.namespaces = {}
        self.namespaces[prefix] = uri

    def compile_xpath(self, xpath):
        return etree.XPath(xpath, namespaces=self.namespaces)

    def __nonzero__(self):
        return bool(self.extract())

    def __str__(self):
        data = repr(self.extract()[:40])
        return '<%s data=%s>' % (type(self).__name__, data)

    __repr__ = __str__


class XmlXPathExtractor(XPathExtractor):
    _parser = etree.XMLParser
    _tostring_method = 'xml'


class HtmlXPathExtractor(XPathExtractor):
    _parser = etree.HTMLParser
    _tostring_method = 'html'
