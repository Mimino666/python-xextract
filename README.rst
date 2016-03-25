********
xextract
********

Extract structured data from HTML and XML documents like a boss.

**xextract** is simple enough for writing a one-line parser, yet powerful enough to be used in a big project.


**Features**

- Simple declarative style of parsers
- Parsing of HTML and XML documents
- Supports **xpath** and **css** selectors
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
  >>> from xextract import Group, String

  # title - use css selector
  >>> String(css='h1[itemprop="name"]', quant=1).parse(response.text)
  u'The Shawshank Redemption'

  # year - use xpath selector
  >>> String(xpath='//*[@id="titleYear"]/a', quant=1).parse(response.text)
  u'1994'

  # cast list - parse structured data
  >>> Group(css='.cast_list tr:not(:first-child)', children=[
  ...   String(name='name', css='[itemprop="actor"]', attr='_all_text', quant=1),
  ...   String(name='character', css='.character', attr='_all_text', quant=1)
  ... ]).parse(response.text)
  [
    {
        'name': u'Tim Robbins',
        'character': u'Andy Dufresne'
    },
    {
        'name': u'Morgan Freeman',
        'character': u"Ellis Boyd 'Red' Redding"
    },
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


=======
Parsers
=======

------
String
------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``'self::*'``), `quant`_ (optional, default ``'*'``), `attr`_ (optional, default ``'_text'``), `namespaces`_ (optional)

Returns the string data extracted from the matched element.
Returned value is always unicode.

Use ``attr`` parameter to extract the data from an HTML/XML attribute.

By default, ``String`` extracts the text content of only the matched element, but not its descendants.
To extract and concatenate the text out of every descendant element, use ``attr`` parameter with the special value ``'_all_text'``:

Example:

.. code-block:: python

    >>> String(css='span', quant=1).parse('<span>Hello <b>world</b>!</span>')
    u'Hello !'

    >>> String(css='span', quant=1, attr='_all_text').parse('<span>Hello <b>world</b>!</span>')
    u'Hello world!''

    >>> String(css='span', quant=1, attr='class').parse('<span class="text-success"></span>')
    u'text-success'

---
Url
---

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``'self::*'``), `quant`_ (optional, default ``'*'``), `attr`_ (optional, default ``'href'``), `namespaces`_ (optional)

Behaves like ``String`` parser, but with two exceptions:

* default value for ``attr`` parameter is ``'href'``
* if you pass ``url`` parameter to ``parse()`` method, the absolute url will be constructed and returned

Example:

.. code-block:: python

    >>> html = '<a href="/test">Link</a>'
    >>> Url(css='a', quant=1).parse(html)
    u'/test'

    >>> Url(css='a', quant=1).parse(html, url='http://github.com/Mimino666')
    u'http://github.com/test'  # absolute url address. Told ya!


--------
DateTime
--------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``'self::*'``), ``format`` (required), `quant`_ (optional, default ``'*'``), `attr`_ (optional, default ``'_text'``), `namespaces`_ (optional)

Returns the ``datetime`` object constructed out of the extracted data: ``datetime.strptime(value, format)``.

``format`` syntax is described in the `Python documentation <https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior>`_.

Example:

.. code-block:: python

    >>> DateTime(css='span', quant=1, format='%d.%m.%Y').parse('<span>24.12.2015</span>')
    datetime.datetime(2015, 12, 24, 0, 0)


-------
Element
-------

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``'self::*'``), `quant`_ (optional, default ``'*'``), `namespaces`_ (optional)

Returns lxml instance (``lxml.etree._Element``) of matched element.

Example:

.. code-block:: python

    >>> Element(css='span', quant=1).parse('<span>Hello</span>')
    <Element span at 0x2ac2990>


-----
Group
-----

**Parameters**: `name`_ (optional), `css / xpath`_ (optional, default ``'self::*'``), `children`_ (required), `quant`_ (optional, default ``'*'``), `namespaces`_ (optional)

Returns the dictionary containing the data extracted by the parsers listed in ``children`` parameter.
All parsers listed in ``children`` parameter **must** have ``name`` specified.

Typical use case for this parser is when you want to parse structured data, e.g. list of user profiles, where each profile contains fields like name, address, etc. Use ``Group`` parser to group the fields of each user profile together.

Example:

.. code-block:: python

    >>> html = '<ul><li id="id1">Hello</li> <li id="id2">world!</li></ul>'
    >>> Group(css='li', quant=2, children=[
    ...     String(name='id', xpath='self::*', quant=1, attr='id'),
    ...     String(name='text', xpath='self::*', quant=1)
    ... ]).parse(html)
    [{'text': u'Hello', 'id': u'id1'},
     {'text': u'world!', 'id': u'id2'}]


------
Prefix
------

TODO

=================
Parser parameters
=================

----
name
----

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

**Default value**: ``None``

If specified, then the extracted data will be returned as a dictionary, with the ``name`` as the key and the data as the value.

All parsers listed in ``children`` parameter of ``Group`` or ``Prefix`` parser **must** have ``name`` specified.
If multiple children parsers have the same ``name``, the behavior is undefined.

Example:

.. code-block:: python

  >>> String(css='span', quant=1).parse('<span>Hello!</span>')
  u'Hello!'

  >>> String(name='message', quant=1).parse('<span>Hello!</span>')
  {'message': u'Hello!'}


-----------
css / xpath
-----------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_, `Prefix`_

**Default value (xpath)**: ``'self::*'``

Use either ``css`` or ``xpath`` parameter (but not both) to select the elements from which to extract the data.

Under the hood css selectors are translated into equivalent xpath selectors.

For the children of ``Prefix`` or ``Group`` parser the elements are selected relative to the elements matched by the parent parser.

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

**Default value**: ``'*'``

Number of matched elements is validated against the ``quant`` parameter.
If the number of elements doesn't match the expected quantity, ``xextract.parsers.ParsingError`` exception is raised.
In practice you can use this to be alerted when the website changed its HTML structure.

Syntax for ``quant`` mimics the regular expressions.
You can either pass the value as a string, single integer or tuple of two integers.

Depending on the value of ``quant``, the extracted data are returned either as a single value or a list of values.

+-------------------+-----------------------------------------------+-----------------------------+
| Value of ``quant``| Meaning                                       | Extracted data type         |
+===================+===============================================+=============================+
| ``'*'`` (default) | Zero or more elements.                        | List of values              |
+-------------------+-----------------------------------------------+-----------------------------+
| ``'+'``           | One or more elements.                         | List of values              |
+-------------------+-----------------------------------------------+-----------------------------+
| ``'?'``           | Zero or one element.                          | Single value or ``None``    |
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
|                   | You can pass either a string or tuple.        |                             |
+-------------------+-----------------------------------------------+-----------------------------+

Example:

.. code-block:: python

    >>> String(css='.name', quant=1).parse(html)
    u'Barack Obama'

    >>> String(css='.name', quant='1').parse(html)  # same as above
    u'Barack Obama'

    >>> String(css='.name', quant=(1,2)).parse(html)
    [u'Barack Obama']

    >>> String(css='.name', quant='1,2').parse(html)  # same as above
    [u'Barack Obama']

    >>> String(css='.middle-name', quant='?').parse(html)
    None

    >>> String(css='.job-titles', quant='+').parse(html)
    [u'President', u'US Senator', u'State Senator', u'Senior Lecturer in Law']

    >>> String(css='.friends', quant='*').parse(html)
    []

    >>> String(css='.friends', quant='+').parse(html)
    xextract.parsers.ParsingError: Number of "None" elements, 0, does not match the expected quantity "+".


----
attr
----

**Parsers**: `String`_, `Url`_, `DateTime`_

**Default value**: ``'href'`` for ``Url`` parser. ``'_text'`` otherwise.

Use ``attr`` parameter to specify what data to extract from the matched element.

+-------------------+-----------------------------------------------------+
| Value of ``attr`` | Meaning                                             |
+===================+=====================================================+
| ``'_text'``       | Extract the text content of the matched element.    |
+-------------------+-----------------------------------------------------+
| ``'_all_text'``   | Extract and concatenate the text content of         |
|                   | the matched element and all its descendants.        |
+-------------------+-----------------------------------------------------+
| ``att_name``      | Extract the value out of ``att_name`` attribute of  |
|                   | the matched element.                                |
|                   |                                                     |
|                   | If such attribute doesn't exist, empty string is    |
|                   | returned.                                           |
+-------------------+-----------------------------------------------------+

Example:

.. code-block:: python

    html = '<span class="name">Barack <strong>Obama</strong> III.</span> <a href="/test">Link</a>'

    >>> String(css='.name', quant=1).parse(html)
    u'Barack  III.'

    >>> String(css='.name', quant=1, attr='_text').parse(html)  # same as above
    u'Barack  III.'

    >>> String(css='.name', quant=1, attr='_all_text').parse(html)  # full name
    u'Barack Obama III.'

    >>> String(css='a', quant='1').parse(html)  # String extracts text content by default
    u'Link'

    >>> Url(css='a', quant='1').parse(html)  # Url extracts href by default
    u'/test'

    >>> String(css='a', quant='1', attr='id').parse(html)  # non-existent attributes return empty string
    u''


--------
children
--------

**Parsers**: `Group`_, `Prefix`_


----------
namespaces
----------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_, `Prefix`_
