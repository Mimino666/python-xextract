from datetime import datetime
import urlparse

from cssselect import GenericTranslator
from lxml import etree

from .extractors import XPathExtractor, HtmlXPathExtractor, XmlXPathExtractor
from .quantity import Quantity


__all__ = ['ParserError', 'ParsingError',
           'Prefix', 'Group', 'Element', 'String', 'Url', 'DateTime', 'Date']


class ParserError(Exception):
    '''Parser is badly initialized.'''
    pass


class ParsingError(Exception):
    '''Numebr of parsed elements doesn't match the expected quantity.'''
    pass


class BaseParser(object):
    def __init__(self, css=None, xpath=None, namespaces=None):
        if xpath and css:
            raise ParserError('At most one of "xpath" or "css" attributes can be specified.')

        if xpath:
            self.raw_xpath = xpath
        elif css:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        else:
            self.raw_xpath = 'self::*'

        self.namespaces = namespaces
        self._compiled_xpath = None  # compile xpath lazily

    def __call__(self, body, url=None):
        return self.parse(body, url)

    def parse(self, body, url=None):
        if isinstance(body, XPathExtractor):
            extractor = body
        else:
            if '<?xml' in body[:128]:
                extractor = XmlXPathExtractor(body)
            else:
                extractor = HtmlXPathExtractor(body)

        return self._parse(extractor, {'url': url})

    def parse_html(self, body, url=None):
        '''Force `etree.HTMLParser`.'''
        return self._parse(HtmlXPathExtractor(body), {'url': url})

    def parse_xml(self, body, url=None):
        '''Force `etree.XMLParser`.'''
        return self._parse(XmlXPathExtractor(body), {'url': url})

    def _parse(self, extractor, context):
        nodes = extractor.select(self.compiled_xpath)
        return self._process_nodes(nodes, context)

    def _process_nodes(self, nodes, context):
        raise NotImplementedError

    @property
    def compiled_xpath(self):
        if self._compiled_xpath is None:
            self._compiled_xpath = etree.XPath(self.raw_xpath, namespaces=self.namespaces)
        return self._compiled_xpath


def propagate_namespaces(parser):
    '''Recursively propagate namespaces to children parsers.'''
    if parser.namespaces and hasattr(parser, 'children'):
        for child in parser.children:
            if not child.namespaces:
                child.namespaces = parser.namespaces
                propagate_namespaces(child)


class ChildrenParserMixin(object):
    def __init__(self, **kwargs):
        self.children = kwargs.pop('children', None)
        if self.children is None:
            raise ParserError('You must specify "children" for %s parser.' % self.__class__.__name__)

        super(ChildrenParserMixin, self).__init__(**kwargs)

        # ensure that all children elements inherited from BaseNamedParser have names
        for child in self.children:
            if isinstance(child, BaseNamedParser) and child.name is None:
                raise ParserError('Children elements inherited from BaseNamedParser should have "name" specified.')

        # propagate namespaces to children parsers
        propagate_namespaces(self)


class Prefix(ChildrenParserMixin, BaseParser):
    def __init__(self, **kwargs):
        self.callback = kwargs.pop('callback', None)
        super(Prefix, self).__init__(**kwargs)

    def _process_nodes(self, nodes, context):
        parsed_data = {}
        for child in self.children:
            parsed_data.update(child._parse(nodes, context))

        if self.callback is not None:
            parsed_data = self.callback(parsed_data)

        return parsed_data


class BaseNamedParser(BaseParser):
    def __init__(self, name=None, quant='*', callback=None, **kwargs):
        super(BaseNamedParser, self).__init__(**kwargs)
        self.name = name
        self.quantity = Quantity(quant)
        self.callback = callback

    def _process_nodes(self, nodes, context):
        # validate number of nodes
        num_nodes = len(nodes)
        if not self.quantity.check_quantity(num_nodes):
            if self.name:
                name_msg = '(name="%s")' % self.name
            else:
                name_msg = '(xpath="%s")' % self.raw_xpath
            raise ParsingError(
                'Parser %s%s matched %s elements ("%s" expected).' %
                (self.__class__.__name__, name_msg, num_nodes, self.quantity.raw_quantity))

        values = self._process_named_nodes(nodes, context)

        if self.callback is not None:
            values = map(self.callback, values)

        if self.name is None:
            return self._flatten_values(values)
        else:
            return {self.name: self._flatten_values(values)}

    def _process_named_nodes(self, nodes, context):
        raise NotImplementedError

    def _flatten_values(self, values):
        if self.quantity.is_single:
            return values[0] if values else None
        else:
            return values


class Group(ChildrenParserMixin, BaseNamedParser):
    def _process_named_nodes(self, nodes, context):
        values = []
        for node in nodes:
            child_parsed_data = {}
            for child in self.children:
                child_parsed_data.update(child._parse(node, context))
            values.append(child_parsed_data)
        return values


class Element(BaseNamedParser):
    def _process_named_nodes(self, nodes, context):
        return [node._root for node in nodes]


class String(BaseNamedParser):
    def __init__(self, attr='_text', **kwargs):
        super(String, self).__init__(**kwargs)
        if attr == '_text':
            self.attr = 'text()'
        elif attr == '_all_text':
            self.attr = 'descendant-or-self::*/text()'
        elif attr == '_name':
            self.attr = 'name()'
        else:
            self.attr = '@' + attr

    def _process_named_nodes(self, nodes, context):
        values = []
        for node in nodes:
            value = u''.join(node.select(self.attr).extract())
            values.append(value)
        return self._process_values(values, context)

    def _process_values(self, values, context):
        return values


class Url(String):
    def __init__(self, **kwargs):
        kwargs.setdefault('attr', 'href')
        super(Url, self).__init__(**kwargs)

    def _process_values(self, values, context):
        url = context.get('url')
        if url:
            return [urlparse.urljoin(url, v.strip()) for v in values]
        else:
            return [v.strip() for v in values]


class DateTime(String):
    def __init__(self, format, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        self.format = format

    def _process_values(self, values, context):
        return [datetime.strptime(v, self.format) for v in values]


class Date(DateTime):
    def _process_values(self, values, context):
        values = super(Date, self)._process_values(values, context)
        return [v.date() for v in values]
