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
    def __init__(self, css=None, xpath=None):
        if (xpath is None) == (css is None):
            raise SelectorError('Exactly one of "xpath" or "css" attributes must be specified.')

        if xpath is not None:
            self.raw_xpath = xpath
        else:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        self.compiled_xpath = None

    def parse_html(self, body, url=None):
        extractor = HtmlXPathExtractor(body)
        context = {}
        if url:
            context['url'] = url
        return self._parse(extractor, context)

    def parse_xml(self, body, namespaces=None, url=None):
        extractor = XmlXPathExtractor(body, namespaces=namespaces)
        context = {}
        if url:
            context['url'] = url
        return self._parse(extractor, context, namespaces)

    def _parse(self, extractor, context, namespaces=None):
        # compile xpath expression for better performance
        if self.compiled_xpath is None:
            self.compiled_xpath = etree.XPath(self.raw_xpath, namespaces=namespaces)
        nodes = extractor.select(self.compiled_xpath)
        return self._process_nodes(nodes, context, namespaces)

    def _process_nodes(self, nodes, context, namespaces):
        raise NotImplementedError


class Prefix(BaseSelector):
    def __init__(self, children, **kwargs):
        super(Prefix, self).__init__(**kwargs)
        self.children = children

    def _process_nodes(self, nodes, context, namespaces):
        parsed_data = {}
        for child in self.children:
            parsed_data.update(child._parse(nodes, context, namespaces))
        return parsed_data


class BaseNamedSelector(BaseSelector):
    def __init__(self, name, quant='*', **kwargs):
        super(BaseNamedSelector, self).__init__(**kwargs)
        self.name = name
        self.quantity = Quantity(quant)

    def _check_quantity(self, nodes):
        num_nodes = len(nodes)
        # check the number of nodes
        if not self.quantity.check_quantity(num_nodes):
            raise ParsingError(
                'Number of "%s" nodes %s does not match the expected quantity "%s".' %
                (self.name, num_nodes, self.quantity.raw_quantity))
        return nodes

    def _flatten_values(self, values):
        if self.quantity.is_single:
            return values[0] if values else None
        else:
            return values


class Group(BaseNamedSelector):
    def __init__(self, children, **kwargs):
        super(Group, self).__init__(**kwargs)
        self.children = children

    def _process_nodes(self, nodes, context, namespaces):
        self._check_quantity(nodes)
        values = []
        for node in nodes:
            child_parsed_data = {}
            for child in self.children:
                child_parsed_data.update(child._parse(node, context, namespaces))
            values.append(child_parsed_data)
        return {self.name: self._flatten_values(values)}


class Element(BaseNamedSelector):
    def _process_nodes(self, nodes, context, namespaces):
        self._check_quantity(nodes)
        values = [node._root for node in nodes]
        return {self.name: self._flatten_values(values)}


class String(BaseNamedSelector):
    def __init__(self, attr='_text', **kwargs):
        super(String, self).__init__(**kwargs)
        if attr == '_text':
            self.attr = 'text()'
        elif attr == '_all_text':
            self.attr = 'descendant-or-self::*/text()'
        else:
            self.attr = '@' + attr

    def _process_nodes(self, nodes, context, namespaces):
        self._check_quantity(nodes)
        values = []
        for node in nodes:
            value = ''.join(node.select(self.attr).extract())
            values.append(value)
        return {self.name: self._flatten_values(values)}


class Url(String):
    def __init__(self, **kwargs):
        kwargs.setdefault('attr', 'href')
        super(Url, self).__init__(**kwargs)

    def _process_nodes(self, nodes, context, namespaces):
        values = []
        for node in nodes:
            value = ''.join(node.select(self.attr).extract())
            url = context.get('url')
            if url:
                value = urlparse.urljoin(url, value)
            values.append(value)
        return {self.name: self._flatten_values(values)}
