import unittest

from xextract.extractors.lxml_extractor import XPathExtractor, XmlXPathExtractor, HtmlXPathExtractor


class TestXpathExtractor(unittest.TestCase):
    xs_cls = XPathExtractor
    hxs_cls = HtmlXPathExtractor
    xxs_cls = XmlXPathExtractor

    def test_extractor_simple(self):
        text = '<p><input name="a" value="1"/><input name="b" value="2"/></p>'
        xpath = self.hxs_cls(text)

        xl = xpath.select('//input')
        self.assertEqual(2, len(xl))
        for x in xl:
            self.assertIsInstance(x, self.hxs_cls)

        self.assertEqual(xpath.select('//input').extract(),
                         [x.extract() for x in xpath.select('//input')])

        self.assertEqual([x.extract() for x in xpath.select('//input[@name="a"]/@name')],
                         [u'a'])
        self.assertEqual([x.extract() for x in xpath.select('number(concat(//input[@name="a"]/@value, //input[@name="b"]/@value))')],
                         [u'12.0'])

        self.assertEqual(xpath.select('concat("xpath", "rules")').extract(),
                         [u'xpathrules'])
        self.assertEqual([x.extract() for x in xpath.select('concat(//input[@name="a"]/@value, //input[@name="b"]/@value)')],
                         [u'12'])

    def test_extractor_unicode_query(self):
        text = u'<p><input name="\xa9" value="1"/></p>'
        xpath = self.hxs_cls(text)
        self.assertEqual(xpath.select(u'//input[@name="\xa9"]/@value').extract(), [u'1'])

    def test_extractor_same_type(self):
        '''Test XPathExtractor returning the same type in x() method.'''
        text = '<p>test<p>'
        self.assertIsInstance(self.xxs_cls(text).select('//p')[0],
                              self.xxs_cls)
        self.assertIsInstance(self.hxs_cls(text).select('//p')[0],
                              self.hxs_cls)

    def test_extractor_boolean_result(self):
        text = '<p><input name="a" value="1"/><input name="b" value="2"/></p>'
        xs = self.hxs_cls(text)
        self.assertEqual(xs.select('//input[@name="a"]/@name="a"').extract(), [u'1'])
        self.assertEqual(xs.select('//input[@name="a"]/@name="n"').extract(), [u'0'])

    def test_extractor_xml_html(self):
        '''Test that XML and HTML XPathExtractor's behave differently.'''
        # some text which is parsed differently by XML and HTML flavors
        text = '<div><img src="a.jpg"><p>Hello</div>'

        self.assertEqual(self.xxs_cls(text).select('//div').extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></img></div>'])

        self.assertEqual(self.hxs_cls(text).select('//div').extract(),
                         [u'<div><img src="a.jpg"><p>Hello</p></div>'])

    def test_extractor_nested(self):
        '''Nested extractor tests.'''
        text = '''<body>
                    <div class='one'>
                      <ul>
                        <li>one</li><li>two</li>
                      </ul>
                    </div>
                    <div class='two'>
                      <ul>
                        <li>four</li><li>five</li><li>six</li>
                      </ul>
                    </div>
                  </body>'''

        x = self.hxs_cls(text)
        divtwo = x.select('//div[@class="two"]')
        self.assertEqual(map(unicode.strip, divtwo.select('//li').extract()),
                         ['<li>one</li>', '<li>two</li>', '<li>four</li>', '<li>five</li>', '<li>six</li>'])
        self.assertEqual(map(unicode.strip, divtwo.select('./ul/li').extract()),
                         ['<li>four</li>', '<li>five</li>', '<li>six</li>'])
        self.assertEqual(map(unicode.strip, divtwo.select('.//li').extract()),
                         ['<li>four</li>', '<li>five</li>', '<li>six</li>'])
        self.assertEqual(divtwo.select('./li').extract(),
                         [])

    def test_dont_strip(self):
        hxs = self.hxs_cls('<div>fff: <a href="#">zzz</a></div>')
        self.assertEqual(hxs.select('//text()').extract(), [u'fff: ', u'zzz'])

    def test_extractor_namespaces_simple(self):
        text = '''
        <test xmlns:somens="http://github.com/">
           <somens:a id="foo">take this</a>
           <a id="bar">found</a>
        </test>
        '''
        x = self.xxs_cls(text)
        x.register_namespace('somens', 'http://github.com/')
        self.assertEqual(x.select('//somens:a/text()').extract(), [u'take this'])

    def test_extractor_namespaces_multiple(self):
        text = '''<?xml version="1.0" encoding="UTF-8"?>
        <BrowseNode xmlns="http://webservices.amazon.com/AWSECommerceService/2005-10-05"
                xmlns:b="http://somens.com"
                xmlns:p="http://www.github.com/product" >
            <b:Operation>hello</b:Operation>
            <TestTag b:att="value"><Other>value</Other></TestTag>
            <p:SecondTestTag><material>iron</material><price>90</price><p:name>Dried Rose</p:name></p:SecondTestTag>
        </BrowseNode>
        '''
        x = self.xxs_cls(text)

        x.register_namespace('xmlns', 'http://webservices.amazon.com/AWSECommerceService/2005-10-05')
        x.register_namespace('p', 'http://www.github.com/product')
        x.register_namespace('b', 'http://somens.com')
        self.assertEqual(len(x.select('//xmlns:TestTag')), 1)
        self.assertEqual(x.select('//b:Operation/text()').extract()[0], 'hello')
        self.assertEqual(x.select('//xmlns:TestTag/@b:att').extract()[0], 'value')
        self.assertEqual(x.select('//p:SecondTestTag/xmlns:price/text()').extract()[0], '90')
        self.assertEqual(x.select('//p:SecondTestTag').select('./xmlns:price/text()')[0].extract(), '90')
        self.assertEqual(x.select('//p:SecondTestTag/xmlns:material/text()').extract()[0], 'iron')

    def test_extractor_over_text(self):
        hxs = self.hxs_cls('<root>lala</root>')
        self.assertEqual(hxs.extract(),
                         u'<html><body><root>lala</root></body></html>')

        xxs = self.xxs_cls('<root>lala</root>')
        self.assertEqual(xxs.extract(),
                         u'<root>lala</root>')

        xxs = self.xxs_cls('<root>lala</root>')
        self.assertEqual(xxs.select('.').extract(),
                         [u'<root>lala</root>'])

    def test_extractor_invalid_xpath(self):
        x = self.hxs_cls('<html></html>')
        xpath = '//test[@foo="bar]'
        self.assertRaises(Exception, x.select, xpath)

    def test_empty_bodies(self):
        # shouldn't raise errors
        self.hxs_cls('').select('//text()').extract()
        self.xxs_cls('').select('//text()').extract()

    def test_null_bytes(self):
        # shouldn't raise errors
        text = '<root>pre\x00post</root>'
        self.hxs_cls(text).select('//text()').extract()
        self.xxs_cls(text).select('//text()').extract()

    def test_select_on_unevaluable_nodes(self):
        r = self.hxs_cls(u'<span class="big">some text</span>')
        # Text node
        x1 = r.select('//text()')
        self.assertEquals(x1.extract(), [u'some text'])
        self.assertEquals(x1.select('.//b').extract(), [])
        # Tag attribute
        x1 = r.select('//span/@class')
        self.assertEquals(x1.extract(), [u'big'])
        self.assertEquals(x1.select('.//text()').extract(), [])

    def test_select_on_text_nodes(self):
        r = self.hxs_cls(u'<div><b>Options:</b>opt1</div><div><b>Other</b>opt2</div>')
        x1 = r.select('//div/descendant::text()[preceding-sibling::b[contains(text(), "Options")]]')
        self.assertEquals(x1.extract(), [u'opt1'])

        x1 = r.select('//div/descendant::text()/preceding-sibling::b[contains(text(), "Options")]')
        self.assertEquals(x1.extract(), [u'<b>Options:</b>'])
