import copy
from datetime import datetime, date
import unittest
from urlparse import urlparse

from lxml import etree
import six

from xextract.parsers import (ParserError, ParsingError, BaseParser,
    BaseNamedParser, Prefix, Group, Element, String, Url, DateTime, Date)


class TestBuild(unittest.TestCase):
    def test_build(self):
        # missing children for Group / Prefix parsers
        self.assertRaisesRegexp(ParserError, r'You must specify "children" for Prefix parser', Prefix)
        self.assertRaisesRegexp(ParserError, r'You must specify "children" for Group parser', Group)
        # missing name of children elements
        self.assertRaisesRegexp(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Prefix(children=[String()]))
        self.assertRaisesRegexp(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Group(children=[String()]))
        self.assertRaisesRegexp(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Prefix(children=[Prefix(children=[String()])]))
        self.assertRaisesRegexp(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Prefix(children=[Group(name='x', children=[String()])]))


class TestBaseParser(unittest.TestCase):
    parser_class = BaseParser
    parser_kwargs = {}

    def test_init(self):
        # xpath / css missing
        parser = self.parser_class(**self.parser_kwargs)
        self.assertEqual(parser.raw_xpath, 'self::*')
        # both xpath / css specified
        self.assertRaises(ParserError, self.parser_class, css='a', xpath='//a', **self.parser_kwargs)
        # css specified
        self.parser_class(css='a', **self.parser_kwargs)
        # xpath specified
        self.parser_class(xpath='//a', **self.parser_kwargs)


class MockParser(BaseParser):
    def _process_nodes(self, nodes, context):
        return nodes


class TestParser(TestBaseParser):
    parser_class = MockParser

    def test_html_extraction(self):
        html = '''
        <ul>
            <li>a</li>
            <li>b</li>
        </ul>
        '''

        # xpath
        self.assertEqual(len(MockParser(xpath='//ul').parse(html)), 1)
        self.assertEqual(len(MockParser(xpath='ul').parse(html)), 0)
        self.assertEqual(len(MockParser(xpath='/ul').parse(html)), 0)

        self.assertEqual(len(MockParser(xpath='//li').parse(html)), 2)
        self.assertEqual(len(MockParser(xpath='li').parse(html)), 0)
        self.assertEqual(len(MockParser(xpath='/li').parse(html)), 0)

        self.assertEqual(len(MockParser(xpath='//ul/li').parse(html)), 2)
        self.assertEqual(len(MockParser(xpath='//ul//li').parse(html)), 2)

        # css
        self.assertEqual(len(MockParser(css='ol').parse(html)), 0)
        self.assertEqual(len(MockParser(css='ul').parse(html)), 1)
        self.assertEqual(len(MockParser(css='li').parse(html)), 2)

    def test_xml_extraction(self):
        xml = '''
        <?xml version="1.0" encoding="UTF-8"?>
        <body xmlns="http://test.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <ul>
                <li>a</li>
                <xsi:li>b</xsi:li>
            </ul>
        </body>
        '''

        namespaces = {'a': 'http://test.com/', 'b': 'http://www.w3.org/2001/XMLSchema-instance'}
        # xpath
        self.assertEqual(len(MockParser(xpath='//a:ul', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockParser(xpath='a:ul', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockParser(xpath='/a:ul', namespaces=namespaces).parse(xml)), 0)

        self.assertEqual(len(MockParser(xpath='//a:li', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockParser(xpath='a:li', namespaces=namespaces).parse(xml)), 0)
        self.assertEqual(len(MockParser(xpath='/a:li', namespaces=namespaces).parse(xml)), 0)

        self.assertEqual(len(MockParser(xpath='//b:li', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockParser(xpath='b:li', namespaces=namespaces).parse(xml)), 0)
        self.assertEqual(len(MockParser(xpath='/b:li', namespaces=namespaces).parse(xml)), 0)


class MockNamedParser(BaseNamedParser):
    def _process_named_nodes(self, nodes, context):
        return [node.extract() for node in nodes]


class TestBaseNamedParser(TestBaseParser):
    parser_class = MockNamedParser
    parser_kwargs = {'name': 'val'}
    return_value_type = six.text_type

    html = '''
    <ul>
        <li>a</li>
        <li>b</li>
    </ul>
    '''

    def test_check_quantity(self):
        self.assertRaises(ParsingError, self.parser_class(css='li', quant=0, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='li', quant=1, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ul', quant=2, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ul', quant=(2,3), **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='li', quant='?', **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ol', quant='+', **self.parser_kwargs).parse, self.html)

    def test_check_quantity_return_type(self):
        self.assertIsNone(self.parser_class(css='ol', quant=0, **self.parser_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.parser_class(css='ul', quant=1, **self.parser_kwargs).parse(self.html)['val'], self.return_value_type)
        self.assertIsInstance(self.parser_class(css='li', quant=2, **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.parser_class(css='ol', quant=(0, 0), **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='ul', quant=(1, 1), **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', quant=(1, 2), **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsNone(self.parser_class(css='ol', quant='?', **self.parser_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.parser_class(css='ul', quant='?', **self.parser_kwargs).parse(self.html)['val'], self.return_value_type)

        self.assertIsInstance(self.parser_class(css='ol', quant='*', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='ul', quant='*', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', quant='*', **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.parser_class(css='ul', quant='+', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', quant='+', **self.parser_kwargs).parse(self.html)['val'], list)

    def test_missing_name(self):
        no_name_parser_kwargs = copy.copy(self.parser_kwargs)
        del no_name_parser_kwargs['name']
        self.assertIsNone(self.parser_class(css='ol', quant=0, **no_name_parser_kwargs).parse(self.html))
        self.assertIsInstance(self.parser_class(css='ul', quant=1, **no_name_parser_kwargs).parse(self.html), self.return_value_type)
        self.assertIsInstance(self.parser_class(css='li', quant=2, **no_name_parser_kwargs).parse(self.html), list)


class TestString(TestBaseNamedParser):
    parser_class = String

    def test_basic(self):
        html = '<span data-val="rocks">Hello <b>world</b>!</span>'

        # by default extract _text
        self.assertEqual(String(name='val', css='span', quant=1).parse(html)['val'], 'Hello !')

        self.assertEqual(String(name='val', css='span', quant=1, attr='_text').parse(html)['val'], 'Hello !')
        self.assertEqual(String(name='val', css='span', quant=1, attr='_all_text').parse(html)['val'], 'Hello world!')
        self.assertEqual(String(name='val', css='span', quant=1, attr='data-val').parse(html)['val'], 'rocks')
        self.assertEqual(String(name='val', css='span', quant=1, attr='data-invalid').parse(html)['val'], '')

    def test_callback(self):
        html = '<span>1</span><span>2</span>'
        self.assertListEqual(String(css='span').parse(html), ['1', '2'])
        self.assertListEqual(String(css='span', callback=int).parse(html), [1, 2])
        self.assertEqual(String(css='span:first-child', callback=int, quant=1).parse(html), 1)
        self.assertListEqual(String(css='div', callback=int).parse(html), [])


class TestUrl(TestBaseNamedParser):
    parser_class = Url

    def test_basic(self):
        html = '<a href="/test?a=b" data-val="/val">Hello <b>world</b>!</a>'

        # by default extract href
        self.assertEqual(Url(name='val', css='a', quant=1).parse(html)['val'], '/test?a=b')
        self.assertEqual(Url(name='val', css='a', quant=1).parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/test?a=b')

        self.assertEqual(Url(name='val', css='a', quant=1, attr='data-val').parse(html)['val'], '/val')
        self.assertEqual(Url(name='val', css='a', quant=1, attr='data-val').parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/val')

    def test_callback(self):
        def _parse_scheme(url):
            return urlparse(url).scheme
        html = '<a href="/test"></a>'
        self.assertEqual(Url(css='a', quant=1, callback=_parse_scheme).parse(html), '')
        self.assertEqual(Url(css='a', quant=1, callback=_parse_scheme).parse(html, url='http://example.com/a/b/c'), 'http')


class TestDateTime(TestBaseNamedParser):
    parser_class = DateTime
    parser_kwargs = {'name': 'val', 'format': '%d.%m.%Y %H:%M'}
    return_value_type = datetime
    html = '''<ul><li>1.1.2001 22:14</li><li>2.1.2001 12:12</li>20.3.2002 0:0</ul>'''

    def test_basic(self):
        html = '<span data-val="1.1.2001">24.11.2015 10:12</span>'
        val = DateTime(name='val', css='span', quant=1, format='%d.%m.%Y %H:%M').parse(html)['val']
        self.assertEqual(val, datetime(year=2015, month=11, day=24, hour=10, minute=12))

        val = DateTime(name='val', css='span', quant=1, format='%d.%m.%Y', attr='data-val').parse(html)['val']
        self.assertEqual(val, datetime(year=2001, month=1, day=1))

        # invalid format
        self.assertRaises(ValueError, DateTime(name='val', css='span', quant=1, format='%d').parse, html)

    def test_callback(self):
        def _get_day(dt):
            return dt.day
        html = '<span>24.11.2015</span>'
        self.assertEqual(
            DateTime(css='span', quant=1, format='%d.%m.%Y', callback=_get_day).parse(html),
            24)


class TestDate(TestBaseNamedParser):
    parser_class = Date
    parser_kwargs = {'name': 'val', 'format': '%d.%m.%Y'}
    return_value_type = date
    html = '''<ul><li>1.1.2001</li><li>2.1.2001</li>20.3.2002</ul>'''

    def test_basic(self):
        html = '<span data-val="1.1.2001">24.11.2015</span>'
        val = Date(name='val', css='span', quant=1, format='%d.%m.%Y').parse(html)['val']
        self.assertEqual(val, date(year=2015, month=11, day=24))

        val = Date(name='val', css='span', quant=1, format='%d.%m.%Y', attr='data-val').parse(html)['val']
        self.assertEqual(val, date(year=2001, month=1, day=1))

        # invalid format
        self.assertRaises(ValueError, Date(name='val', css='span', quant=1, format='%d').parse, html)

    def test_callback(self):
        def _get_day(dt):
            return dt.day
        html = '<span>24.11.2015</span>'
        self.assertEqual(
            Date(css='span', quant=1, format='%d.%m.%Y', callback=_get_day).parse(html),
            24)


class TestElement(TestBaseNamedParser):
    parser_class = Element
    parser_kwargs = {'name': 'val'}
    return_value_type = etree._Element

    def test_basic(self):
        html = '<span>Hello <b>world</b>!</span>'

        val = Element(name='val', css='span', quant=1).parse(html)['val']
        self.assertEqual(val.tag, 'span')
        val = Element(name='val', css='b', quant=1).parse(html)['val']
        self.assertEqual(val.tag, 'b')

    def test_callback(self):
        html = '<span>Hello <b>world</b>!</span>'
        val = Element(css='b', quant=1, callback=lambda el: el.text).parse(html)
        self.assertEqual(val, 'world')

    def test_text_extract(self):
        html = '<span>Hello<br> world<b> nothing to see </b>!</span>'
        val = Element(xpath='//span/text()').parse(html)
        self.assertListEqual(val, ['Hello', ' world', '!'])

        html = '<span class="nice"></span>'
        val = Element(xpath='//span/@class', quant=1).parse(html)
        self.assertEqual(val, 'nice')


class TestGroup(TestBaseNamedParser):
    parser_class = Group
    parser_kwargs = {'name': 'val', 'children': []}
    return_value_type = dict
    html = '''
        <ul>
            <li>
                <span>Mike</span>
            </li>
            <li>
                <span>John</span>
                <a href="/test">link</a>
            </li>
        </ul>'''

    def test_basic(self):
        extracted = {'val': [
            {'name': 'Mike', 'link': None},
            {'name': 'John', 'link': 'http://example.com/test'}]}

        # css
        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', css='span', quant=1),
            Url(name='link', css='a', quant='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        # xpath
        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', xpath='span', quant=1),
            Url(name='link', xpath='a', quant='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', xpath='descendant::span', quant=1),
            Url(name='link', xpath='descendant::a', quant='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

    def test_callback(self):
        val = Group(css='li', quant=2, callback=lambda d: d['name'], children=[
            String(name='name', css='span', quant=1),
        ]).parse(self.html)
        self.assertListEqual(val, ['Mike', 'John'])


class TestPrefix(TestBaseParser):
    parser_class = Prefix
    parser_kwargs = {'children': []}
    html = '''
        <ul>
            <li>
                <span>Mike</span>
            </li>

            <li>
                <span>John</span>
            </li>
        </ul>
    '''

    def test_basic(self):
        # css
        val = Prefix(css='li', children=[
            String(name='name', css='span', quant=2)
        ]).parse(self.html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})

        # xpath
        val = Prefix(xpath='//li', children=[
            String(name='name', xpath='span', quant=2)
        ]).parse(self.html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})

    def test_callback(self):
        val = Prefix(xpath='//li', callback=lambda d: d['name'], children=[
            String(name='name', css='span', quant=2),
        ]).parse(self.html)
        self.assertListEqual(val, ['Mike', 'John'])
