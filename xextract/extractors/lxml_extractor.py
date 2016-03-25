from lxml import etree

from .extractor_list import XPathExtractorList


class XPathExtractor(object):
    _parser = etree.HTMLParser
    _tostring_method = 'html'

    def __init__(self, body=None, namespaces=None, _root=None):
        self.namespaces = namespaces
        if _root is None:
            self._root = self._get_root(body)
        else:
            self._root = _root

    def _get_root(self, body, encoding=None):
        body = body.strip() or self._empty_doc
        if isinstance(body, unicode):
            body = body.encode('utf-8')
            encoding = 'utf-8'
        parser = self._parser(recover=True, encoding=encoding)
        return etree.fromstring(body, parser=parser)

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

    def __nonzero__(self):
        return bool(self.extract())

    def __str__(self):
        data = repr(self.extract()[:40])
        return '<%s data=%s>' % (type(self).__name__, data)

    __repr__ = __str__


class XmlXPathExtractor(XPathExtractor):
    _parser = etree.XMLParser
    _tostring_method = 'xml'
    _empty_doc = '<?xml version="1.0" encoding="UTF-8"?>'


class HtmlXPathExtractor(XPathExtractor):
    _parser = etree.HTMLParser
    _tostring_method = 'html'
    _empty_doc = '<html/>'
