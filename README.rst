********
xextract
********

Extract structured data from HTML and XML documents like a boss.

**xextract** is simple enough for writing a one-line parser, yet powerful enough to be used in a big project.


**Features**

- Parsing of HTML and XML documents
- Supports **xpath** and **css** selectors
- Simple declarative style of parsers
- Built-in self-validation to let you know when the structure of the website has changed
- Speed - under the hood the library uses `lxml library <http://lxml.de/>`_ with compiled xpath selectors


**Table of Contents**

.. contents::
    :local:
    :depth: 2
    :backlinks: none


====================
A little taste of it
====================

Let's parse `The Shawshank Redemption <http://www.imdb.com/title/tt0111161/>`_'s IMDB page:

.. code-block:: python

  # fetch the website
  >>> import requests
  >>> response = requests.get('http://www.imdb.com/title/tt0111161/')

  # parse like a boss
  >>> from xextract import String, Group

  # extract title with css selector
  >>> String(css='h1[itemprop="name"]', quant=1).parse(response.text)
  u'The Shawshank Redemption'

  # extract release year with xpath selector
  >>> String(xpath='//*[@id="titleYear"]/a', quant=1, callback=int).parse(response.text)
  1994

  # extract structured data
  >>> Group(css='.cast_list tr:not(:first-child)', children=[
  ...   String(name='name', css='[itemprop="actor"]', attr='_all_text', quant=1),
  ...   String(name='character', css='.character', attr='_all_text', quant=1)
  ... ]).parse(response.text)
  [
   {'name': u'Tim Robbins', 'character': u'Andy Dufresne'},
   {'name': u'Morgan Freeman', 'character': u"Ellis Boyd 'Red' Redding"},
   ...
  ]


============
Installation
============

To install **xextract**, simply run:

.. code-block:: bash

    $ pip install xextract

Requirements: six, lxml, cssselect

Supported Python versions are 2.6, 2.7, 3.x.

Windows users can download lxml binary `here <http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml>`_.


=======
Parsers
=======

------
String
------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``"self::*"``), `quant`_ (optional, default ``"*"``), `attr`_ (optional, default ``"_text"``), `callback`_ (optional), `namespaces`_ (optional)

Extract string data from the matched element(s).
Extracted value is always unicode.

By default, ``String`` extracts the text content of only the matched element, but not its descendants.
To extract and concatenate the text out of every descendant element, use ``attr`` parameter with the special value ``"_all_text"``:

Use ``attr`` parameter to extract the data from an HTML/XML attribute.

Use ``callback`` parameter to post-process extracted values.

Example:

.. code-block:: python

    >>> from xextract import String
    >>> String(css='span', quant=1).parse('<span>Hello <b>world</b>!</span>')
    u'Hello !'

    >>> String(css='span', quant=1, attr='_all_text').parse('<span>Hello <b>world</b>!</span>')
    u'Hello world!'

    >>> String(css='span', quant=1, attr='class').parse('<span class="text-success"></span>')
    u'text-success'

    >>> String(css='span', callback=int).parse('<span>1</span><span>2</span>')
    [1, 2]

---
Url
---

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``"self::*"``), `quant`_ (optional, default ``"*"``), `attr`_ (optional, default ``"href"``), `callback`_ (optional), `namespaces`_ (optional)

Behaves like ``String`` parser, but with two exceptions:

* default value for ``attr`` parameter is ``"href"``
* if you pass ``url`` parameter to ``parse()`` method, the absolute url will be constructed and returned

If ``callback`` is specified, it is called *after* the absolute urls are constructed.

Example:

.. code-block:: python

    >>> from xextract import Url, Prefix
    >>> content = '<div id="main"> <a href="/test">Link</a> </div>'

    >>> Url(css='a', quant=1).parse(content)
    u'/test'

    >>> Url(css='a', quant=1).parse(content, url='http://github.com/Mimino666')
    u'http://github.com/test'  # absolute url address. Told ya!

    >>> Prefix(css='#main', children=[
    ...   Url(css='a', quant=1)
    ... ]).parse(content, url='http://github.com/Mimino666')  # you can pass url also to ancestor's parse(). It will propagate down.
    u'http://github.com/test'


--------
DateTime
--------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``"self::*"``), ``format`` (**required**), `quant`_ (optional, default ``"*"``), `attr`_ (optional, default ``"_text"``), `callback`_ (optional) `namespaces`_ (optional)

Returns the ``datetime`` object constructed out of the extracted data: ``datetime.strptime(extracted_data, format)``.

``format`` syntax is described in the `Python documentation <https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior>`_.

If ``callback`` is specified, it is called *after* the datetime objects are constructed.

Example:

.. code-block:: python

    >>> from xextract import DateTime
    >>> DateTime(css='span', quant=1, format='%d.%m.%Y').parse('<span>24.12.2015</span>')
    datetime.datetime(2015, 12, 24, 0, 0)


-------
Element
-------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``"self::*"``), `quant`_ (optional, default ``"*"``), `callback`_ (optional), `namespaces`_ (optional)

Returns lxml instance (``lxml.etree._Element``) of the matched element(s).

If ``callback`` is specified, it is called with ``lxml.etree._Element`` instance.

Example:

.. code-block:: python

    >>> from xextract import Element
    >>> Element(css='span', quant=1).parse('<span>Hello</span>')
    <Element span at 0x2ac2990>

    >>> Element(css='span', quant=1, callback=lambda el: el.text).parse('<span>Hello</span>')
    u'Hello'


-----
Group
-----

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``"self::*"``), `children`_ (**required**), `quant`_ (optional, default ``"*"``), `callback`_ (optional), `namespaces`_ (optional)

For each element matched by css/xpath selector returns the dictionary containing the data extracted by the parsers listed in ``children`` parameter.
All parsers listed in ``children`` parameter **must** have ``name`` specified - this is then used as the key in dictionary.

Typical use case for this parser is when you want to parse structured data, e.g. list of user profiles, where each profile contains fields like name, address, etc. Use ``Group`` parser to group the fields of each user profile together.

If ``callback`` is specified, it is called with the dictionary of parsed children values.

Example:

.. code-block:: python

    >>> from xextract import Group
    >>> content = '<ul><li id="id1">michal</li> <li id="id2">peter</li></ul>'

    >>> Group(css='li', quant=2, children=[
    ...     String(name='id', xpath='self::*', quant=1, attr='id'),
    ...     String(name='name', xpath='self::*', quant=1)
    ... ]).parse(content)
    [{'name': u'michal', 'id': u'id1'},
     {'name': u'peter', 'id': u'id2'}]


------
Prefix
------

**Parameters**: `css / xpath`_ (optional, default ``"self::*"``), `children`_ (**required**), `namespaces`_ (optional)

This parser doesn't actually parse any data on its own. Instead you can use it, when many of your parsers share the same css/xpath selector prefix.

``Prefix`` parser always returns a single dictionary containing the data extracted by the parsers listed in ``children`` parameter.
All parsers listed in ``children`` parameter **must** have ``name`` specified - this is then used as the key in dictionary.

Example:

.. code-block:: python

    # instead of
    >>> String(css='#main .name').parse(...)
    >>> String(css='#main .date').parse(...)

    # you can use
    >>> from xextract import Prefix
    >>> Prefix(css='#main', children=[
    ...   String(name="name", css='.name'),
    ...   String(name="date", css='.date')
    ... ]).parse(...)


=================
Parser parameters
=================

----
name
----

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

**Default value**: ``None``

If specified, then the extracted data will be returned in a dictionary, with the ``name`` as the key and the data as the value.

All parsers listed in ``children`` parameter of ``Group`` or ``Prefix`` parser **must** have ``name`` specified.
If multiple children parsers have the same ``name``, the behavior is undefined.

Example:

.. code-block:: python

  # when `name` is not specified, raw value is returned
  >>> String(css='span', quant=1).parse('<span>Hello!</span>')
  u'Hello!'

  # when `name` is specified, dictionary is returned with `name` as the key
  >>> String(name='message', css='span', quant=1).parse('<span>Hello!</span>')
  {'message': u'Hello!'}


-----------
css / xpath
-----------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_, `Prefix`_

**Default value (xpath)**: ``"self::*"``

Use either ``css`` or ``xpath`` parameter (but not both) to select the elements from which to extract the data.

Under the hood css selectors are translated into equivalent xpath selectors.

For the children of ``Prefix`` or ``Group`` parsers, the elements are selected relative to the elements matched by the parent parser.

Example:

.. code-block:: python

    Prefix(xpath='//*[@id="profile"]', children=[
        # equivalent to: //*[@id="profile"]/descendant-or-self::*[@class="name"]
        String(name='name', css='.name', quant=1),

        # equivalent to: //*[@id="profile"]/*[@class="title"]
        String(name='title', xpath='*[@class="title"]', quant=1),

        # equivalent to: //*[@class="subtitle"]
        String(name='subtitle', xpath='//*[@class="subtitle"]', quant=1)
    ])


-----
quant
-----

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

**Default value**: ``"*"``

``quant`` specifies the expected number of elements to be matched with css/xpath selector. It serves two purposes:

1. Number of matched elements is checked against the ``quant`` parameter. If the number of elements doesn't match the expected quantity, ``xextract.parsers.ParsingError`` exception is raised. This way you will be notified, when the website has changed its structure.
2. It tells the parser whether to return a single extracted value or a list of values. See the table below.

Syntax for ``quant`` mimics the regular expressions.
You can either pass the value as a string, single integer or tuple of two integers.

Depending on the value of ``quant``, the parser returns either a single extracted value or a list of values.

+-------------------+-----------------------------------------------+-----------------------------+
| Value of ``quant``| Meaning                                       | Extracted data              |
+===================+===============================================+=============================+
| ``"*"`` (default) | Zero or more elements.                        | List of values              |
+-------------------+-----------------------------------------------+-----------------------------+
| ``"+"``           | One or more elements.                         | List of values              |
+-------------------+-----------------------------------------------+-----------------------------+
| ``"?"``           | Zero or one element.                          | Single value or ``None``    |
+-------------------+-----------------------------------------------+-----------------------------+
| ``num``           | Exactly ``num`` elements.                     | ``num`` == 0: ``None``      |
|                   |                                               |                             |
|                   | You can pass either string or integer.        | ``num`` == 1: Single value  |
|                   |                                               |                             |
|                   |                                               | ``num`` > 1: List of values |
+-------------------+-----------------------------------------------+-----------------------------+
| ``(num1, num2)``  | Number of elements has to be between          | List of values              |
|                   | ``num1`` and ``num2``, inclusive.             |                             |
|                   |                                               |                             |
|                   | You can pass either a string or 2-tuple.      |                             |
+-------------------+-----------------------------------------------+-----------------------------+

Example:

.. code-block:: python

    >>> String(css='.full-name', quant=1).parse(content)  # return single value
    u'John Rambo'

    >>> String(css='.full-name', quant='1').parse(content)  # same as above
    u'John Rambo'

    >>> String(css='.full-name', quant=(1,2)).parse(content)  # return list of values
    [u'John Rambo']

    >>> String(css='.full-name', quant='1,2').parse(content)  # same as above
    [u'John Rambo']

    >>> String(css='.middle-name', quant='?').parse(content)  # return single value or None
    None

    >>> String(css='.job-titles', quant='+').parse(content)  # return list of values
    [u'President', u'US Senator', u'State Senator', u'Senior Lecturer in Law']

    >>> String(css='.friends', quant='*').parse(content)  # return possibly empty list of values
    []

    >>> String(css='.friends', quant='+').parse(content)  # raise exception, when no elements are matched
    xextract.parsers.ParsingError: Parser String matched 0 elements ("+" expected).


----
attr
----

**Parsers**: `String`_, `Url`_, `DateTime`_

**Default value**: ``"href"`` for ``Url`` parser. ``"_text"`` otherwise.

Use ``attr`` parameter to specify what data to extract from the matched element.

+-------------------+-----------------------------------------------------+
| Value of ``attr`` | Meaning                                             |
+===================+=====================================================+
| ``"_text"``       | Extract the text content of the matched element.    |
+-------------------+-----------------------------------------------------+
| ``"_all_text"``   | Extract and concatenate the text content of         |
|                   | the matched element and all its descendants.        |
+-------------------+-----------------------------------------------------+
| ``"_name"``       | Extract tag name of the matched element.            |
+-------------------+-----------------------------------------------------+
| ``att_name``      | Extract the value out of ``att_name`` attribute of  |
|                   | the matched element.                                |
|                   |                                                     |
|                   | If such attribute doesn't exist, empty string is    |
|                   | returned.                                           |
+-------------------+-----------------------------------------------------+

Example:

.. code-block:: python

    >>> from xextract import String, Url
    >>> content = '<span class="name">Barack <strong>Obama</strong> III.</span> <a href="/test">Link</a>'

    >>> String(css='.name', quant=1).parse(content)  # default attr is "_text"
    u'Barack  III.'

    >>> String(css='.name', quant=1, attr='_text').parse(content)  # same as above
    u'Barack  III.'

    >>> String(css='.name', quant=1, attr='_all_text').parse(content)  # all text
    u'Barack Obama III.'

    >>> String(css='.name', quant=1, attr='_name').parse(content)  # tag name
    u'span'

    >>> Url(css='a', quant='1').parse(content)  # Url extracts href by default
    u'/test'

    >>> String(css='a', quant='1', attr='id').parse(content)  # non-existent attributes return empty string
    u''


--------
callback
--------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

Provides an easy way to post-process extracted values.
It should be a function that takes a single argument, the extracted value, and returns the postprocessed value.

Example:

.. code-block:: python

    >>> String(css='span', callback=int).parse('<span>1</span><span>2</span>')
    [1, 2]

    >>> Element(css='span', quant=1, callback=lambda el: el.text).parse('<span>Hello</span>')
    u'Hello'

--------
children
--------

**Parsers**: `Group`_, `Prefix`_

Specifies the children parsers for the ``Group`` and ``Prefix`` parsers.
All parsers listed in ``children`` parameter **must** have ``name`` specified

Css/xpath selectors in the children parsers are relative to the selectors specified in the parent parser.

Example:

.. code-block:: python

    Prefix(xpath='//*[@id="profile"]', children=[
        # equivalent to: //*[@id="profile"]/descendant-or-self::*[@class="name"]
        String(name='name', css='.name', quant=1),

        # equivalent to: //*[@id="profile"]/*[@class="title"]
        String(name='title', xpath='*[@class="title"]', quant=1),

        # equivalent to: //*[@class="subtitle"]
        String(name='subtitle', xpath='//*[@class="subtitle"]', quant=1)
    ])

----------
namespaces
----------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_, `Prefix`_

When parsing XML documents containing namespace prefixes, pass the dictionary mapping namespace prefixes to namespace URIs.
Use then full name for elements in xpath selector in the form ``"prefix:element"``

As for the moment, you **cannot use default namespace** for parsing (see `lxml docs <http://lxml.de/FAQ.html#how-can-i-specify-a-default-namespace-for-xpath-expressions>`_ for more information).  Just use an arbitrary prefix.

Example:

.. code-block:: python

    >>> content = '''<?xml version='1.0' encoding='UTF-8'?>
    ... <movie xmlns="http://imdb.com/ns/">
    ...   <title>The Shawshank Redemption</title>
    ...   <year>1994</year>
    ... </movie>'''
    >>> nsmap = {'imdb': 'http://imdb.com/ns/'}  # use arbitrary prefix for default namespace

    >>> Prefix(xpath='//imdb:movie', namespaces=nsmap, children=[  # pass namespaces to the outermost parser
    ...   String(name='title', xpath='imdb:title', quant=1),
    ...   String(name='year', xpath='imdb:year', quant=1)
    ... ]).parse(content)
    {'title': u'The Shawshank Redemption', 'year': u'1994'}


====================
HTML vs. XML parsing
====================

To extract data from HTML or XML document, simply call ``parse()`` method of the parser:

.. code-block:: python

    >>> from xextract import *
    >>> parser = Prefix(..., children=[...])
    >>> extracted_data = parser.parse(content)


``content`` can be either string or unicode, containing the content of the document.

Under the hood **xextact** uses either ``lxml.etree.XMLParser`` or ``lxml.etree.HTMLParser`` to parse the document.
To select the parser, **xextract** looks for ``"<?xml"`` string in the first 128 bytes of the document. If it is found, then ``XMLParser`` is used.

To force either of the parsers, you can call ``parse_html()`` or ``parse_xml()`` method:

.. code-block:: python

    >>> parser.parse_html(content)  # force lxml.etree.HTMLParser
    >>> parser.parse_xml(content)   # force lxml.etree.XMLParser
