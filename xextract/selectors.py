from datetime import datetime
import urlparse

from cssselect import GenericTranslator
from lxml import etree

from .extractors import XPathExtractor, HtmlXPathExtractor, XmlXPathExtractor
from .quantity import Quantity


__all__ = [
    'SelectorError', 'ParsingError',
    'Prefix', 'Group', 'Element', 'String', 'Url', 'DateTime']


class SelectorError(Exception):
    pass


class ParsingError(Exception):
    pass


class BaseSelector(object):
    def __init__(self, css=None, xpath=None, namespaces=None, children=None):
        if xpath and css:
            raise SelectorError('At most one of "xpath" or "css" attributes can be specified.')
        if xpath:
            self.raw_xpath = xpath
        elif css:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        else:
            self.raw_xpath = 'self::*'
        self.namespaces = namespaces
        self.children = children
        # ensure that all children inherited from BaseNamedSelector have names
        if self.children:
            for child in self.children:
                if isinstance(child, BaseNamedSelector) and child.name is None:
                    raise SelectorError('Children inherited from BaseNamedSelector should have "name" specified.')
        self._propagate_namespaces()

    def _propagate_namespaces(self):
        if self.namespaces and self.children:
            for child in self.children:
                if not child.namespaces:
                    child.namespaces = self.namespaces
                    child._propagate_namespaces()

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
        return self._parse(HtmlXPathExtractor(body), {'url': url})

    def parse_xml(self, body, url=None):
        return self._parse(XmlXPathExtractor(body), {'url': url})

    def _parse(self, extractor, context):
        # select the nodes based on the xpath/css selector
        nodes = extractor.select(self.compiled_xpath)
        return self._process_nodes(nodes, context)

    def _process_nodes(self, nodes, context):
        raise NotImplementedError

    @property
    def compiled_xpath(self):
        if not hasattr(self, '_compiled_xpath'):
            self._compiled_xpath = etree.XPath(self.raw_xpath, namespaces=self.namespaces)
        return self._compiled_xpath


class Prefix(BaseSelector):
    def __init__(self, **kwargs):
        super(Prefix, self).__init__(**kwargs)
        if self.children is None:
            raise SelectorError('You must specify "children" for Prefix parser.')

    def _process_nodes(self, nodes, context):
        parsed_data = {}
        for child in self.children:
            parsed_data.update(child._parse(nodes, context))
        return parsed_data


class BaseNamedSelector(BaseSelector):
    def __init__(self, name=None, quant='*', **kwargs):
        super(BaseNamedSelector, self).__init__(**kwargs)
        self.name = name
        self.quantity = Quantity(quant)

    def _process_nodes(self, nodes, context):
        # validate number of nodes
        num_nodes = len(nodes)
        if not self.quantity.check_quantity(num_nodes):
            raise ParsingError(
                'Number of "%s" elements, %s, does not match the expected quantity "%s".' %
                (self.name, num_nodes, self.quantity.raw_quantity))

        values = self._process_named_nodes(nodes, context)
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


class Group(BaseNamedSelector):
    def __init__(self, **kwargs):
        super(Group, self).__init__(**kwargs)
        if self.children is None:
            raise SelectorError('You must specify "children" for Group parser.')

    def _process_named_nodes(self, nodes, context):
        values = []
        for node in nodes:
            child_parsed_data = {}
            for child in self.children:
                child_parsed_data.update(child._parse(node, context))
            values.append(child_parsed_data)
        return values


class Element(BaseNamedSelector):
    def _process_named_nodes(self, nodes, context):
        return [node._root for node in nodes]


class String(BaseNamedSelector):
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
            values = [urlparse.urljoin(url, v) for v in values]
        return values


class DateTime(String):
    def __init__(self, format, **kwargs):
        super(DateTime, self).__init__(**kwargs)
        self.format = format

    def _process_values(self, values, context):
        return [datetime.strptime(v, self.format) for v in values]
