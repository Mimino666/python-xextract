from datetime import datetime
import urlparse

from cssselect import GenericTranslator
from lxml import etree

from .extractors import HtmlXPathExtractor, XmlXPathExtractor
from .quantity import Quantity


class SelectorError(Exception):
    pass


class ParsingError(Exception):
    pass


class BaseSelector(object):
    def __init__(self, css=None, xpath=None, namespaces=None):
        if (xpath is None) == (css is None):
            raise SelectorError('Exactly one of "xpath" or "css" attributes must be specified.')

        if xpath is not None:
            self.raw_xpath = xpath
        else:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        self.namespaces = namespaces
        self._propagate_namespaces()

    def _propagate_namespaces(self):
        if self.namespaces and hasattr(self, 'children'):
            for child in self.children:
                if not child.namespaces:
                    child.namespaces = self.namespaces
                    child._propagate_namespaces()

    def parse(self, body, url=None):
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
        nodes = extractor.select(self.compiled_xpath)
        self._check_nodes(nodes)
        return self._process_nodes(nodes, context)

    def _check_nodes(self, nodes):
        pass

    def _process_nodes(self, nodes, context):
        raise NotImplementedError

    @property
    def compiled_xpath(self):
        if not hasattr(self, '_compiled_xpath'):
            self._compiled_xpath = etree.XPath(self.raw_xpath, namespaces=self.namespaces)
        return self._compiled_xpath


class Prefix(BaseSelector):
    def __init__(self, children, **kwargs):
        self.children = children
        super(Prefix, self).__init__(**kwargs)

    def _process_nodes(self, nodes, context):
        parsed_data = {}
        for child in self.children:
            parsed_data.update(child._parse(nodes, context))
        return parsed_data


class BaseNamedSelector(BaseSelector):
    def __init__(self, name, quant='*', **kwargs):
        self.name = name
        self.quantity = Quantity(quant)
        super(BaseNamedSelector, self).__init__(**kwargs)

    def _check_nodes(self, nodes):
        num_nodes = len(nodes)
        # check the number of nodes
        if not self.quantity.check_quantity(num_nodes):
            raise ParsingError(
                'Number of "%s" elements, %s, does not match the expected quantity "%s".' %
                (self.name, num_nodes, self.quantity.raw_quantity))
        return nodes

    def _flatten_values(self, values):
        if self.quantity.is_single:
            return values[0] if values else None
        else:
            return values


class Group(BaseNamedSelector):
    def __init__(self, children, **kwargs):
        self.children = children
        super(Group, self).__init__(**kwargs)

    def _process_nodes(self, nodes, context):
        values = []
        for node in nodes:
            child_parsed_data = {}
            for child in self.children:
                child_parsed_data.update(child._parse(node, context))
            values.append(child_parsed_data)
        return {self.name: self._flatten_values(values)}


class Element(BaseNamedSelector):
    def _process_nodes(self, nodes, context):
        values = [node._root for node in nodes]
        return {self.name: self._flatten_values(values)}


class String(BaseNamedSelector):
    def __init__(self, attr='_text', **kwargs):
        if attr == '_text':
            self.attr = 'text()'
        elif attr == '_all_text':
            self.attr = 'descendant-or-self::*/text()'
        else:
            self.attr = '@' + attr
        super(String, self).__init__(**kwargs)

    def _process_nodes(self, nodes, context):
        values = []
        for node in nodes:
            value = u''.join(node.select(self.attr).extract())
            values.append(value)
        values = self._process_values(values, context)
        return {self.name: self._flatten_values(values)}

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
        self.format = format
        super(DateTime, self).__init__(**kwargs)

    def _process_values(self, values, context):
        return [datetime.strptime(v, self.format) for v in values]
