********
xextract
********

*NOTE*: **xextract** is still under construction.

Extract structured data from HTML and XML like a boss.

**xextract** is simple enough to write a one-line parser, yet powerful enough to be a part of a big project.


**Features**

- Simple declarative style of parsers
- Parsing of HTML and XML documents
- Supports **xpath** and **css selectors**
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

.. code-block:: python

  # fetch the website
  import requests
  response = requests.get('https://www.linkedin.com/in/barackobama')

  # parse like a boss
  from xextract import Prefix, Group, String, Url
  Prefix(css='#profile', children=[
      String(name='name', css='.full-name', quant=1),
      String(name='title', css='.title', quant=1),
      Group(name='jobs', css='#background-experience .section-item', quant='*', children=[
          String(name='title', css='h4', quant=1),
          String(name='company', css='h5', quant=1, attr='_all_text'),
          Url(name='company_url', css='h5 a', quant='?'),
          String(name='description', css='.description', quant='?')
      ])
  ]).parse(response.text, url=response.url)


Output:

.. code-block:: python

  {'name': u'Barack Obama',
   'title': u'President of the United States of America',
   'jobs': [
       {'company': u'United States of America',
        'company_url': None,
        'description': u'I am serving as the 44th President of the United States of America.',
        'title': u'President'},
       {'company': u'US Senate (IL-D)',
        'company_url': u'http://www.linkedin.com/company/4560?trk=ppro_cprof',
        'description': u'In the U.S. Senate, I sought to focus on tackling the challenges of a globalized, 21st century world with fresh thinking and a politics that no longer settles for the lowest common denominator.',
        'title': u'US Senator'},
       {'company': u'Illinois State Senate',
        'company_url': None,
        'description': u"Proudly representing the 13th District on Chicago's south side.",
        'title': u'State Senator'},
       {'company': u'University of Chicago Law School',
        'company_url': u'http://www.linkedin.com/company/3878?trk=ppro_cprof',
        'description': None,
        'title': u'Senior Lecturer in Law'}]}


============
Installation
============

To install **xextract**, simply:

.. code-block:: bash

    $ pip install xextract

Requirements: six, lxml, cssselect

Supported Python versions are 2.6, 2.7, 3.x.


===========
Basic usage
===========

In the examples below we will demonstrate how to parse the data from a Linkedin profile,
so include the following code to the top of the file:

.. code-block:: python

    from xextract import *
    import requests
    response = requests.get('https://www.linkedin.com/in/barackobama')
    html, url = response.text, response.url

-----

To extract the name from the Linkedin profile, call:

.. code-block:: python

    >>> String(name='name', css='.full-name', quant=1).parse(html)
    {'name': u'Barack Obama'}


You can see that the **parsed data are returned in a dictionary**.

Parameters we passed to the parser have the following meaning:

- ``name`` (required) - dictionary key under which to store the parsed data.
- ``css`` (required) - css selector to the HTML element containing the data.
- ``quant`` (optional) - number of HTML elements we expect to match with the css selector. In this case we expect exactly one element. If the number of elements doesn't match, ``ParsingError`` exception is raised:

    .. code-block:: python

        >>> String(name='name', css='.full-name', quant=2).parse(html)
        xextract.selectors.ParsingError: Number of "name" elements, 1, does not match the expected quantity "2".

If you don't pass ``quant`` parameter, two things will happen. First, there will be no validation on the number of matched elements, i.e. you can match zero or more elements and no exception is raised. Second, the extracted data will be returned as a (possibly empty) list of values (for more details see `quant`_ reference):

.. code-block:: python

    >>> String(name='name', css='.full-name').parse(html)
    {'name': [u'Barack Obama']}  # note that the extracted data are in the list

-----

In the previous example we could have used xpath instead of css selector:

.. code-block:: python

    >>> String(name='name', xpath='//*[@class="full-name"]', quant=1).parse(html)
    {'name': u'Barack Obama'}


-----

By default, ``String`` extracts the text content of the element. To extract the data from an HTML attribute, use ``attr`` parameter:

.. code-block:: python

    >>> String(name='css-class', css='span', quant=1, attr='class').parse('<span class="hello"></span>')
    {'css-class': u'hello'}


-----

To extract the whole text "*500+ connections*" from the following HTML structure:

.. code-block:: html

    <div class="member-connections">
        <strong>500+</strong>
        connections
    </div>

By default, ``String`` parser extracts only the text directly from the matched elements, but not their descendants.
In the above case, if we matched ``.member-connections`` element, by default it would extract only the text "*connections*".

To extract and concatenate the text out of every descendant element, use ``attr`` parameter with the special value *'_all_text'*:

.. code-block:: python

    >>> String(name='connections', css='.profile-overview .member-connections', quant=1, attr='_all_text').parse(html)
    {'connections': u'500+ connections'}


-----

To extract the url of the profile picture, use ``Url`` parser instead of ``String``:

.. code-block:: python

    >>> Url(name='profile-picture', css='.profile-picture img', quant=1, attr='src').parse(html, url=url)
    {'profile-picture': u'https://media.licdn.com/mpr/mpr/shrink_200_200/p/2/000/1a3/129/3a73f4c.jpg'}


When you use ``Url`` parser and pass ``url`` parameter to ``parse()`` method,
the parser will extract the absolute url address.
By default, ``Url`` extracts the value out of *href* attribute of the matched element.
If you want to extract the value out of a different attribute (e.g. *src*), pass it as ``attr`` parameter.

-----

To extract a list of jobs and from each job to store the company name and the title,
use ``Group`` parser to group the job data together:

.. code-block:: python

    >>> Group(name='jobs', css='#background-experience .section-item', quant='+', children=[
    ...     String(name='title', css='h4', quant=1),
    ...     String(name='company', css='h5', quant=1, attr='_all_text')
    ... ]).parse(html)
    {'jobs': [
        {'company': u'United States of America', 'title': u'President'},
        {'company': u'US Senate (IL-D)', 'title': u'US Senator'},
        {'company': u'Illinois State Senate', 'title': u'State Senator'},
        {'company': u'University of Chicago Law School', 'title': u'Senior Lecturer in Law'}]}


In this case the ``Group`` matched four elements, each of those containing a single ``h4`` and ``h5`` elements.


================
Parser reference
================

------
String
------

**Parameters**: `name`_ (required), `css / xpath`_ (required), `quant`_ (default ``'*'``), `attr`_ (default ``'_text'``), `namespaces`_

Returns the raw string extracted from the matched element.
Returned value is always unicode.

Use ``attr`` parameter to extract the data from an HTML attribute.

By default, ``String`` extracts the text content directly from the matched element, but not its descendants.
To extract and concatenate the text out of every descendant element, use ``attr`` parameter with the special value *'_all_text'*:

Example:

.. code-block:: python

    >>> String(name='text', css='span', quant=1).parse('<span>Hello <b>world!</b></span>')
    {'text': u'Hello '}

    >>> String(name='text', css='span', quant=1, attr='_all_text').parse('<span>Hello <b>world!</b></span>')
    {'text': u'Hello world!'}


---
Url
---

**Parameters**: `name`_ (required), `css / xpath`_ (required), `quant`_ (default ``'*'``), `attr`_ (default ``'href'``), `namespaces`_

Returns the raw string extracted from the matched element.
Returned value is always unicode.

If you pass ``url`` parameter to ``parse()`` method, the absolute urls will be extracted and returned.

Example:

.. code-block:: python

    >>> html = '<a href="/test">Link</a>'
    >>> Url(name='url', css='a', quant=1).parse(html)
    {'url': u'/test'}  # without url passed, Url parser behaves just like the String parser

    >>> Url(name='url', css='a', quant=1).parse(html, url='http://github.com/Mimino666')
    {'url': u'http://github.com/test'}  # absolute url address. Told ya!


--------
DateTime
--------

**Parameters**: `name`_ (required), `css / xpath`_ (required), ``format`` (required), `quant`_ (default ``'*'``), `attr`_ (default ``'_text'``), `namespaces`_

Returns the ``datetime`` object constructed out of the parsed data by: ``datetime.strptime(value, format)``.

Use ``format`` parameter to specify how to parse the ``datetime`` object. Syntax is described in the `Python documentation <https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior>`_.

Example:

.. code-block:: python

    >>> DateTime(name='christmas', css='span', quant=1, format='%d.%m.%Y').parse('<span>24.12.2015</span>')
    {'christmas': datetime.datetime(2015, 12, 24, 0, 0)}


-------
Element
-------

**Parameters**: `name`_ (required), `css / xpath`_ (required), `quant`_ (default ``'*'``), `namespaces`_

Returns the instance of ``lxml.etree._Element``.

This parser doesn't extract any value, but returns the matched element itself.

Example:

.. code-block:: python

    >>> Element(name='span', css='span', quant=1).parse('<span>Hello</span>')
    {'span': <Element span at 0x2ac2990>}


-----
Group
-----

**Parameters**: `name`_ (required), `css / xpath`_ (required), `children`_ (required), `quant`_ (default ``'*'``), `namespaces`_

Returns the dictionary of the data extracted by the parsers listed in ``children`` parameter.

Typical use case for this parser is when you want to parse a list of user profiles and each profile further contains additional fields like name, address, etc. Use ``Group`` parser to group the fields of each profile together into separate dictionary.

Example:

.. code-block:: python

    >>> html = '<ul><li id="id1">Hello</li> <li id="id2">world!</li></ul>'
    >>> Group(name='data', css='li', quant=2, children=[
    ...     String(name='id', xpath='self::*', quant=1, attr='id'),
    ...     String(name='text', xpath='self::*', quant=1)
    ... ]).parse(html)
    {'data': [
        {'text': u'Hello', 'id': u'id1'},
        {'text': u'world!', 'id': u'id2'}]}


------
Prefix
------


=================
Parser parameters
=================

----
name
----

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

Specifies the dictionary key under which to store the extracted data.

If multiple parsers under the ``Group`` or ``Prefix`` parser have the same ``name``, the behavior is undefined.


-----------
css / xpath
-----------

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_, `Prefix`_

Use either ``css`` or ``xpath`` parameter (but not both) to select the elements from which to extract the data.

Under the hood css selectors are translated into equivalent xpath selectors.

For the children of the ``Prefix`` or ``Group`` parser note, that the elements are selected relative to the elements matched by the parent parser. For example:

.. code-block:: python

    Prefix(xpath='//*[@id="profile"]', children=[
        # same as: //*[@id="profile"]/descendant::*[@class="full-name"]
        String(name='name', css='.full-name', quant=1),
        # same as: //*[@id="profile"]/*[@class="title"]
        String(name='title', xpath='*[@class="title"]', quant=1),
        # same as: //*[@class="subtitle"]
        # Probably not what you want.
        String(name='subtitle', xpath='//*[@class="subtitle"]', quant=1)
    ])


-----
quant
-----

**Parsers**: `String`_, `Url`_, `DateTime`_, `Element`_, `Group`_

**Default value**: ``'*'``

Number of matched elements is validated against the ``quant`` parameter.
If the number of elements doesn't match the expected quantity, ``ParsingError`` exception is raised.
In practice you can use this to be notified when the website changed its HTML structure.

Syntax for ``quant`` mimics the regular expressions.
You can either pass the value as a string, single integer or tuple of two integers.

Depending on the value of ``quant``, the extracted data are returned either as a single value or a list of values.

+-------------------+-----------------------------------------------+-----------------------------+
| Value of ``quant``| Meaning                                       | Extracted data              |
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

Examples:

.. code-block:: python

    >>> String(name='name', css='.name', quant=1).parse(html)
    {'name': u'Barack Obama'}

    >>> String(name='name', css='.name', quant='1').parse(html)  # same as above
    {'name': u'Barack Obama'}

    >>> String(name='name', css='.name', quant=(1,2)).parse(html)
    {'name': [u'Barack Obama']}

    >>> String(name='name', css='.name', quant='1,2').parse(html)  # same as above
    {'name': [u'Barack Obama']}

    >>> String(name='middle-name', css='.middle', quant='?').parse(html)
    {'middle-name': None}

    >>> String(name='job-titles', css='#background-experience .section-item h4', quant='+').parse(html)
    {'job-titles': [u'President', u'US Senator', u'State Senator', u'Senior Lecturer in Law']}

    >>> String(name='friends', css='.friend', quant='*').parse(html)
    {'friends': []}

    >>> String(name='friends', css='.friend', quant='+').parse(html)
    xextract.selectors.ParsingError: Number of "friends" elements, 0, does not match the expected quantity "+".


----
attr
----

**Parsers**: `String`_, `Url`_, `DateTime`_

**Default value**: ``'href'`` for ``Url`` parser. ``'_text'`` otherwise.

Use ``attr`` parameter to specify what to extract from the matched element.

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

For the following HTML structure:

.. code-block:: html

    <span class="name">Barack <strong>Obama</strong> III.</span>
    <a href="/test">Link</a>

He are a few examples:

.. code-block:: python

    >>> String(name='name', css='.name', quant=1).parse(html)
    {'name': u'Barack  III.'}

    >>> String(name='name', css='.name', quant=1, attr='_text').parse(html)  # same as above
    {'name': u'Barack  III.'}

    >>> String(name='full-name', css='.name', quant=1, attr='_all_text').parse(html)
    {'full-name': u'Barack Obama III.'}

    >>> String(name='link', css='a', quant='1').parse(html)  # String extracts text content by default
    {'link': u'Link'}

    >>> Url(name='link', css='a', quant='1').parse(html)  # Url extracts href by default
    {'link': u'/test'}

    >>> String(name='id', css='a', quant='1', attr='id').parse(html)  # non-existent attributes return empty string
    {'id': u''}


--------
children
--------

**Parsers**: `Group`_, `Prefix`_


----------
namespaces
----------
