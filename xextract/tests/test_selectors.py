from datetime import datetime
import unittest

from lxml import etree
import six

from xextract.selectors import (SelectorError, ParsingError, BaseSelector,
    BaseNamedSelector, Prefix, Group, Element, String, Url, DateTime)


class TestBaseSelector(unittest.TestCase):
    selector_class = BaseSelector
    selector_kwargs = {}

    def test_init(self):
        # xpath / css missing
        self.assertRaises(SelectorError, self.selector_class, **self.selector_kwargs)
        # both xpath / css specified
        self.assertRaises(SelectorError, self.selector_class, css='a', xpath='//a', **self.selector_kwargs)
        # css specified
        self.selector_class(css='a', **self.selector_kwargs)
        # xpath specified
        self.selector_class(xpath='//a', **self.selector_kwargs)


class MockSelector(BaseSelector):
    def _process_nodes(self, nodes, context):
        return nodes


class TestSelector(TestBaseSelector):
    selector_class = MockSelector

    def test_html_extraction(self):
        html = '''
        <ul>
            <li>a</li>
            <li>b</li>
        </ul>
        '''

        # xpath
        self.assertEqual(len(MockSelector(xpath='//ul').parse(html)), 1)
        self.assertEqual(len(MockSelector(xpath='ul').parse(html)), 0)
        self.assertEqual(len(MockSelector(xpath='/ul').parse(html)), 0)

        self.assertEqual(len(MockSelector(xpath='//li').parse(html)), 2)
        self.assertEqual(len(MockSelector(xpath='li').parse(html)), 0)
        self.assertEqual(len(MockSelector(xpath='/li').parse(html)), 0)

        self.assertEqual(len(MockSelector(xpath='//ul/li').parse(html)), 2)
        self.assertEqual(len(MockSelector(xpath='//ul//li').parse(html)), 2)

        # css
        self.assertEqual(len(MockSelector(css='ol').parse(html)), 0)
        self.assertEqual(len(MockSelector(css='ul').parse(html)), 1)
        self.assertEqual(len(MockSelector(css='li').parse(html)), 2)

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
        self.assertEqual(len(MockSelector(xpath='//a:ul', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockSelector(xpath='a:ul', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockSelector(xpath='/a:ul', namespaces=namespaces).parse(xml)), 0)

        self.assertEqual(len(MockSelector(xpath='//a:li', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockSelector(xpath='a:li', namespaces=namespaces).parse(xml)), 0)
        self.assertEqual(len(MockSelector(xpath='/a:li', namespaces=namespaces).parse(xml)), 0)

        self.assertEqual(len(MockSelector(xpath='//b:li', namespaces=namespaces).parse(xml)), 1)
        self.assertEqual(len(MockSelector(xpath='b:li', namespaces=namespaces).parse(xml)), 0)
        self.assertEqual(len(MockSelector(xpath='/b:li', namespaces=namespaces).parse(xml)), 0)


class MockNamedSelector(BaseNamedSelector):
    def _process_nodes(self, nodes, context):
        values = [node.extract() for node in nodes]
        return {self.name: self._flatten_values(values)}


class TestBaseNamedSelector(TestBaseSelector):
    selector_class = MockNamedSelector
    selector_kwargs = {'name': 'val'}
    selector_type = six.text_type

    html = '''
    <ul>
        <li>a</li>
        <li>b</li>
    </ul>
    '''

    def test_check_quantity(self):
        self.assertRaises(ParsingError, self.selector_class(css='li', quant=0, **self.selector_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.selector_class(css='li', quant=1, **self.selector_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.selector_class(css='ul', quant=2, **self.selector_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.selector_class(css='ul', quant=(2,3), **self.selector_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.selector_class(css='li', quant='?', **self.selector_kwargs).parse, self.html)
        self.assertRaises(ParsingError, self.selector_class(css='ol', quant='+', **self.selector_kwargs).parse, self.html)

    def test_check_quantity_return_type(self):
        self.assertIsNone(self.selector_class(css='ol', quant=0, **self.selector_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.selector_class(css='ul', quant=1, **self.selector_kwargs).parse(self.html)['val'], self.selector_type)
        self.assertIsInstance(self.selector_class(css='li', quant=2, **self.selector_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.selector_class(css='ol', quant=(0, 0), **self.selector_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.selector_class(css='ul', quant=(1, 1), **self.selector_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.selector_class(css='li', quant=(1, 2), **self.selector_kwargs).parse(self.html)['val'], list)

        self.assertIsNone(self.selector_class(css='ol', quant='?', **self.selector_kwargs).parse(self.html)['val'])
        self.assertIsInstance(self.selector_class(css='ul', quant='?', **self.selector_kwargs).parse(self.html)['val'], self.selector_type)

        self.assertIsInstance(self.selector_class(css='ol', quant='*', **self.selector_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.selector_class(css='ul', quant='*', **self.selector_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.selector_class(css='li', quant='*', **self.selector_kwargs).parse(self.html)['val'], list)

        self.assertIsInstance(self.selector_class(css='ul', quant='+', **self.selector_kwargs).parse(self.html)['val'], list)
        self.assertIsInstance(self.selector_class(css='li', quant='+', **self.selector_kwargs).parse(self.html)['val'], list)


class TestString(TestBaseNamedSelector):
    selector_class = String

    def test_basic(self):
        html = '<span data-val="rocks">Hello <b>world</b>!</span>'

        # by default extract _text
        self.assertEqual(String(name='val', css='span', quant=1).parse(html)['val'], 'Hello !')

        self.assertEqual(String(name='val', css='span', quant=1, attr='_text').parse(html)['val'], 'Hello !')
        self.assertEqual(String(name='val', css='span', quant=1, attr='_all_text').parse(html)['val'], 'Hello world!')
        self.assertEqual(String(name='val', css='span', quant=1, attr='data-val').parse(html)['val'], 'rocks')
        self.assertEqual(String(name='val', css='span', quant=1, attr='data-invalid').parse(html)['val'], '')


class TestUrl(TestBaseNamedSelector):
    selector_class = Url

    def test_basic(self):
        html = '<a href="/test?a=b" data-val="/val">Hello <b>world</b>!</a>'

        # by default extract href
        self.assertEqual(Url(name='val', css='a', quant=1).parse(html)['val'], '/test?a=b')
        self.assertEqual(Url(name='val', css='a', quant=1).parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/test?a=b')

        self.assertEqual(Url(name='val', css='a', quant=1, attr='data-val').parse(html)['val'], '/val')
        self.assertEqual(Url(name='val', css='a', quant=1, attr='data-val').parse(html, url='http://example.com/a/b/c')['val'], 'http://example.com/val')


class TestDateTime(TestBaseNamedSelector):
    selector_class = DateTime
    selector_kwargs = {'name': 'val', 'format': '%d.%m.%Y'}
    selector_type = datetime
    html = '''<ul><li>1.1.2001</li><li>2.1.2001</li>20.3.2002</ul>'''

    def test_basic(self):
        html = '<span data-val="1.1.2001">24.11.2015</span>'
        val = DateTime(name='val', css='span', quant=1, format='%d.%m.%Y').parse(html)['val']
        self.assertEqual(val, datetime(year=2015, month=11, day=24))

        val = DateTime(name='val', css='span', quant=1, format='%d.%m.%Y', attr='data-val').parse(html)['val']
        self.assertEqual(val, datetime(year=2001, month=1, day=1))

        # invalid format
        self.assertRaises(ValueError, DateTime(name='val', css='span', quant=1, format='%d').parse, html)


class TestElement(TestBaseNamedSelector):
    selector_class = Element
    selector_kwargs = {'name': 'val'}
    selector_type = etree._Element

    def test_basic(self):
        html = '<span>Hello <b>world</b>!</span>'

        val = Element(name='val', css='span', quant=1).parse(html)['val']
        self.assertEqual(val.tag, 'span')
        val = Element(name='val', css='b', quant=1).parse(html)['val']
        self.assertEqual(val.tag, 'b')


class TestGroup(TestBaseNamedSelector):
    selector_class = Group
    selector_kwargs = {'name': 'val', 'children': []}
    selector_type = dict

    def test_basic(self):
        html = '''
        <ul>
            <li>
                <span>Mike</span>
            </li>

            <li>
                <span>John</span>
                <a href="/test">link</a>
            </li>
        </ul>
        '''

        extracted = {'val': [
            {'name': 'Mike', 'link': None},
            {'name': 'John', 'link': 'http://example.com/test'}]}

        # css
        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', css='span', quant=1),
            Url(name='link', css='a', quant='?')
        ]).parse(html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        # xpath
        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', xpath='span', quant=1),
            Url(name='link', xpath='a', quant='?')
        ]).parse(html, url='http://example.com/')
        self.assertDictEqual(val, extracted)

        val = Group(name='val', css='li', quant=2, children=[
            String(name='name', xpath='descendant::span', quant=1),
            Url(name='link', xpath='descendant::a', quant='?')
        ]).parse(html, url='http://example.com/')
        self.assertDictEqual(val, extracted)


class TestPrefix(TestBaseSelector):
    selector_class = Prefix
    selector_kwargs = {'children': []}

    def test_basic(self):
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

        # css
        val = Prefix(css='li', children=[
            String(name='name', css='span', quant=2)
        ]).parse(html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})

        # xpath
        val = Prefix(xpath='//li', children=[
            String(name='name', xpath='span', quant=2)
        ]).parse(html)
        self.assertDictEqual(val, {'name': ['Mike', 'John']})
