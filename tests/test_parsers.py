from datetime import datetime, date
from urllib.parse import urlparse
import copy
import unittest
from unittest.mock import patch

from lxml import etree

from xextract.extractors import HtmlXPathExtractor, XmlXPathExtractor
from xextract.parsers import (
    ParserError, ParsingError, BaseParser, BaseNamedParser,
    Prefix, Group, Element, String, Url, DateTime, Date)


class TestBuild(unittest.TestCase):
    def test_build(self):
        # missing children for Group / Prefix parsers
        self.assertRaisesRegex(ParserError, r'You must specify "children" for Prefix parser', Prefix)
        self.assertRaisesRegex(ParserError, r'You must specify "children" for Group parser', Group)
        # missing name of children elements
        self.assertRaisesRegex(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Prefix(children=[String()]))
        self.assertRaisesRegex(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Group(children=[String()]))
        self.assertRaisesRegex(ParserError, r'Children elements inherited from BaseNamedParser',
            lambda: Prefix(children=[Prefix(children=[String()])]))
        self.assertRaisesRegex(ParserError, r'Children elements inherited from BaseNamedParser',
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
    return_value_type = str

    html = '''
    <ul>
        <li>a</li>
        <li>b</li>
    </ul>
    '''

    def test_check_quantity(self):
        self.assertRaises(ParsingError, self.parser_class(css='li', count=0, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='li', count=1, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ul', count=2, **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ul', count=(2, 3), **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='li', count='?', **self.parser_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.parser_class(css='ol', count='+', **self.parser_kwargs).parse, self.html)

    def test_check_quantity_return_type(self):
        self.assertIsNone(self.parser_class(css='ol', count=0, **self.parser_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.parser_class(css='ul', count=1, **self.parser_kwargs).parse(self.html)['val'], self.return_value_type)
        self.assertIsInstance(self.parser_class(css='li', count=2, **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.parser_class(css='ol', count=(0, 0), **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='ul', count=(1, 1), **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', count=(1, 2), **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsNone(self.parser_class(css='ol', count='?', **self.parser_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.parser_class(css='ul', count='?', **self.parser_kwargs).parse(self.html)['val'], self.return_value_type)

        self.assertIsInstance(self.parser_class(css='ol', count='*', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='ul', count='*', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', count='*', **self.parser_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.parser_class(css='ul', count='+', **self.parser_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.parser_class(css='li', count='+', **self.parser_kwargs).parse(self.html)['val'], list)

    def test_missing_name(self):
        no_name_parser_kwargs = copy.copy(self.parser_kwargs)
        del no_name_parser_kwargs['name']
        self.assertIsNone(self.parser_class(css='ol', count=0, **no_name_parser_kwargs).parse(self.html))
        self.assertIsInstance(self.parser_class(css='ul', count=1, **no_name_parser_kwargs).parse(self.html), self.return_value_type)
        self.assertIsInstance(self.parser_class(css='li', count=2, **no_name_parser_kwargs).parse(self.html), list)


class TestString(TestBaseNamedParser):
    parser_class = String

    def test_basic(self):
        html = '<span data-val="rocks">Hello <b>world</b>!</span>'

        # by default extract _text
        self.assertEqual(String(name='val', css='span', count=1).parse(html)['val'], 'Hello !')

        self.assertEqual(String(name='val', css='span', count=1, attr='_text').parse(html)['val'], 'Hello !')
        self.assertEqual(String(name='val', css='span', count=1, attr='_all_text').parse(html)['val'], 'Hello world!')
        self.assertEqual(String(name='val', css='span', count=1, attr='data-val').parse(html)['val'], 'rocks')
        self.assertEqual(String(name='val', css='span', count=1, attr='data-invalid').parse(html)['val'], '')

    def test_callback(self):
        html = '<span>1</span><span>2</span>'
        self.assertListEqual(String(css='span').parse(html), ['1', '2'])
        self.assertListEqual(String(css='span', callback=int).parse(html), [1, 2])
        self.assertEqual(String(css='span:first-child', callback=int, count=1).parse(html), 1)
        self.assertListEqual(String(css='div', callback=int).parse(html), [])


class TestUrl(TestBaseNamedParser):
    parser_class = Url

    def test_basic(self):
        html = '<a href="/test?a=b" data-val="/val">Hello <b>world</b>!</a>'

        # by default extract href
        self.assertEqual(Url(name='val', css='a', count=1).parse(html)['val'], '/test?a=b')
        self.assertEqual(Url(name='val', css='a', count=1).parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/test?a=b')

        self.assertEqual(Url(name='val', css='a', count=1, attr='data-val').parse(html)['val'], '/val')
        self.assertEqual(Url(name='val', css='a', count=1, attr='data-val').parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/val')

    def test_callback(self):
        def _parse_scheme(url):
            return urlparse(url).scheme
        html = '<a href="/test"></a>'
        self.assertEqual(Url(css='a', count=1, callback=_parse_scheme).parse(html), '')
        self.assertEqual(Url(css='a', count=1, callback=_parse_scheme).parse(html, url='http://example.com/a/b/c'), 'http')


class TestDateTime(TestBaseNamedParser):
    parser_class = DateTime
    parser_kwargs = {'name': 'val', 'format': '%d.%m.%Y %H:%M'}
    return_value_type = datetime
    html = '''<ul><li>1.1.2001 22:14</li><li>2.1.2001 12:12</li>20.3.2002 0:0</ul>'''

    def test_basic(self):
        html = '<span data-val="1.1.2001">24.11.2015 10:12</span>'
        val = DateTime(name='val', css='span', count=1, format='%d.%m.%Y %H:%M').parse(html)['val']
        self.assertEqual(val, datetime(year=2015, month=11, day=24, hour=10, minute=12))

        val = DateTime(name='val', css='span', count=1, format='%d.%m.%Y', attr='data-val').parse(html)['val']
        self.assertEqual(val, datetime(year=2001, month=1, day=1))

        # invalid format
        self.assertRaises(ValueError, DateTime(name='val', css='span', count=1, format='%d').parse, html)

    def test_callback(self):
        def _get_day(dt):
            return dt.day
        html = '<span>24.11.2015</span>'
        self.assertEqual(
            DateTime(css='span', count=1, format='%d.%m.%Y', callback=_get_day).parse(html),
            24)


class TestDate(TestBaseNamedParser):
    parser_class = Date
    parser_kwargs = {'name': 'val', 'format': '%d.%m.%Y'}
    return_value_type = date
    html = '''<ul><li>1.1.2001</li><li>2.1.2001</li>20.3.2002</ul>'''

    def test_basic(self):
        html = '<span data-val="1.1.2001">24.11.2015</span>'
        val = Date(name='val', css='span', count=1, format='%d.%m.%Y').parse(html)['val']
        self.assertEqual(val, date(year=2015, month=11, day=24))

        val = Date(name='val', css='span', count=1, format='%d.%m.%Y', attr='data-val').parse(html)['val']
        self.assertEqual(val, date(year=2001, month=1, day=1))

        # invalid format
        self.assertRaises(ValueError, Date(name='val', css='span', count=1, format='%d').parse, html)

    def test_callback(self):
        def _get_day(dt):
            return dt.day
        html = '<span>24.11.2015</span>'
        self.assertEqual(
            Date(css='span', count=1, format='%d.%m.%Y', callback=_get_day).parse(html),
            24)


class TestElement(TestBaseNamedParser):
    parser_class = Element
    parser_kwargs = {'name': 'val'}
    return_value_type = etree._Element

    def test_basic(self):
        html = '<span>Hello <b>world</b>!</span>'

        val = Element(name='val', css='span', count=1).parse(html)['val']
        self.assertEqual(val.tag, 'span')
        val = Element(name='val', css='b', count=1).parse(html)['val']
        self.assertEqual(val.tag, 'b')

    def test_callback(self):
        html = '<span>Hello <b>world</b>!</span>'
        val = Element(css='b', count=1, callback=lambda el: el.text).parse(html)
        self.assertEqual(val, 'world')

    def test_text_extract(self):
        html = '<span>Hello<br> world<b> nothing to see </b>!</span>'
        val = Element(xpath='//span/text()').parse(html)
        self.assertListEqual(val, ['Hello', ' world', '!'])

        html = '<span class="nice"></span>'
        val = Element(xpath='//span/@class', count=1).parse(html)
        self.assertEqual(val, 'nice')


class TestElementAsExtractor(unittest.TestCase):
    def test_element_as_parser(self):
        """
        we can pass an Element as the extractor to parse_*()
        """
        html = '''
            <div><span>Hello world!</span></div>
            <div></div>
            <div><span>Hello mars!</span></div>
        '''

        # take only the first containers so we can verify that the correct descendant is chosen
        container = Element(name='val', css='div', count=3).parse(html)['val'][2]

        val = Element(name='val', css='span', count=1).parse_html(container)['val']
        self.assertEqual(val.tag, 'span')
        self.assertEqual(val.text, 'Hello mars!')

    def test_element_as_parser_html(self):
        """
        passing Element as extractor for parse_html should use the correct parser
        """

        html = '''
            <html>
                <div>
                    <script>console.log(" &lt; > ");</script>
                    <span>a&lt;a&lsquo;</span>
                </div>
            </html>
        '''

        original_tostring = etree.tostring
        original_parser = HtmlXPathExtractor._parser

        # etree.HtmlParser is immutable so we can't patch it
        # instead we patch HtmlXPathExtractor._parser which references it
        with patch.object(HtmlXPathExtractor, attribute='_parser', autospec=True) as mock_parser:
            mock_parser.side_effect = original_parser
            with patch('lxml.etree.tostring', autospec=True) as mock_tostring:
                mock_tostring.side_effect = original_tostring

                ancestor = Element(css='div', count=1).parse_html(html)
                mock_parser.assert_called_once()
                mock_parser.reset_mock()
                mock_tostring.assert_not_called()

                script_val = String(css='script', count=1).parse_html(ancestor)
                mock_parser.assert_not_called()
                mock_tostring.assert_called_once()
                self.assertEqual(mock_tostring.call_args.kwargs['method'], 'html')
                mock_tostring.reset_mock()

                span_val = String(css='span', count=1).parse_html(ancestor)
                mock_parser.assert_not_called()
                mock_tostring.assert_called_once()
                self.assertEqual(mock_tostring.call_args.kwargs['method'], 'html')
                mock_tostring.reset_mock()

                # HTML has different entity processing from XML:
                #  <script> contents are automatically CDATA
                #  &lt; is an entity only inside <span>
                #  &lsquo; is a valid entity
                self.assertEqual(script_val, 'console.log(" &lt; > ");')
                self.assertEqual(span_val, 'a<a‘')

        with self.assertRaises(ParserError):
            # .parse() is missing the html/xml specifier
            String(css='script', count=1).parse(ancestor)

    def test_element_as_parser_xml(self):
        """
        passing Element as extractor for parse_xml should use the correct parser
        """

        xml = '''
            <?xml version="1.0" encoding="UTF-8"?>
            <body xmlns="http://test.com/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <ul>
                    <xsi:li>
                        <script>console.log(" &lt; > ");</script>
                        <span>a&lt;a&lsquo;</span>
                    </xsi:li>
                </ul>
            </body>
        '''
        namespaces = {'a': 'http://test.com/', 'b': 'http://www.w3.org/2001/XMLSchema-instance'}

        original_tostring = etree.tostring
        original_parser = XmlXPathExtractor._parser

        # etree.XMLParser is immutable so we can't patch it
        # instead we patch XmlXPathExtractor._parser which references it
        with patch.object(XmlXPathExtractor, attribute='_parser', autospec=True) as mock_parser:

            mock_parser.side_effect = original_parser
            with patch('lxml.etree.tostring', autospec=True) as mock_tostring:
                mock_tostring.side_effect = original_tostring

                ancestor = Element(xpath='//a:body', count=1, namespaces=namespaces).parse_xml(xml)
                mock_parser.assert_called_once()
                mock_parser.reset_mock()
                mock_tostring.assert_not_called()

                script_val = String(xpath='//a:script', count=1, namespaces=namespaces).parse_xml(ancestor)
                mock_parser.assert_not_called()
                mock_tostring.assert_called_once()
                self.assertEqual(mock_tostring.call_args.kwargs['method'], 'xml')
                mock_tostring.reset_mock()

                span_val = String(xpath='//a:span', count=1, namespaces=namespaces).parse_xml(ancestor)
                mock_parser.assert_not_called()
                mock_tostring.assert_called_once()
                self.assertEqual(mock_tostring.call_args.kwargs['method'], 'xml')
                mock_tostring.reset_mock()


                # XML has different entity processing from HTML:
                #  <script> contents are not automatically CDATA
                #  &lt; is a valid entity inside both <span> and <script>
                #  &lsquo; is not a valid entity (with libxml it also happens to break subsequent entity parsing)
                self.assertEqual(script_val, 'console.log(" < > ");')
                self.assertEqual(span_val, 'a<a')

        with self.assertRaises(ParserError):
            # .parse() is missing the html/xml specifier
            String(xpath='//a:script', count=1, namespaces=namespaces).parse(ancestor)


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
        val = Group(name='val', css='li', count=2, children=[
            String(name='name', css='span', count=1),
            Url(name='link', css='a', count='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        # xpath
        val = Group(name='val', css='li', count=2, children=[
            String(name='name', xpath='span', count=1),
            Url(name='link', xpath='a', count='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        val = Group(name='val', css='li', count=2, children=[
            String(name='name', xpath='descendant::span', count=1),
            Url(name='link', xpath='descendant::a', count='?')
        ]).parse(self.html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

    def test_callback(self):
        val = Group(css='li', count=2, callback=lambda d: d['name'], children=[
            String(name='name', css='span', count=1),
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
            String(name='name', css='span', count=2)
        ]).parse(self.html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})

        # xpath
        val = Prefix(xpath='//li', children=[
            String(name='name', xpath='span', count=2)
        ]).parse(self.html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})

    def test_callback(self):
        val = Prefix(xpath='//li', callback=lambda d: d['name'], children=[
            String(name='name', css='span', count=2),
        ]).parse(self.html)
        self.assertListEqual(val, ['Mike', 'John'])
