********
xextract
********

*NOTE*: **xextract** is still under construction.

**xextract** is an HTML parsing library that is simple enough to write a one-liner, yet powerful enough to be a part bigger projects.

**Features**

- Simple declarative style of parsers
- Parsing of HTML and XML documents
- Write **xpaths** or **css selectors** to extract the data
- Built-in self-validation to let you know when the structure of the website has changed
- Speed - under the hood the library uses lxml library (http://lxml.de/) with compiled xpath selectors
- You can optionally define the parsers in external XML files to separate the parsing from other business logic


**Table of Contents**

.. contents::
    :local:
    :depth: 2
    :backlinks: none


====================
A little taste of it
====================

.. code-block:: python

  from xextract import Prefix, Group, String, Url
  # fetch the website
  import requests
  response = requests.get('https://www.linkedin.com/in/barackobama')

  parser = Prefix(css='#profile', children=[
      String(name='name', css='.full-name', quant=1),
      String(name='title', css='.title', quant=1),
      Group(name='jobs', css='#background-experience .section-item', quant='*', children=[
          String(name='title', css='h4', quant=1),
          String(name='company', css='h5', quant=1, attr='_all_text'),
          Url(name='company_url', css='h5 a', quant='?'),
          String(name='description', css='.description', quant='?')
      ])
  ])
  parser.parse(response.text, url=response.url)


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

    from xextract import Prefix, Group, Element, String, Url, DateTime
    import requests
    response = requests.get('https://www.linkedin.com/in/barackobama')
    html, url = response.text, response.url


To parse out the name from the Linkedin profile, call:

.. code-block:: python

    >>> String(name='name', css='.full-name', quant=1).parse(html)
    {'name': u'Barack Obama'}


You can see that the **parsed data are returned in a dictionary**.

Parameters we passed to the parser have the following meaning:

- ``name`` - dictionary key under which to store the parsed data.
- ``css`` - css selector to the HTML element containing the data.
- ``quant`` - number of HTML elements we expect to match with the css selector. In this case we expect exactly one element. If the number of elements doesn't match, ``ParsingError`` exception is raised:

    .. code-block:: python

        >>> String(name='name', css='.full-name', quant=2).parse(html)
        xextract.selectors.ParsingError: Number of "name" elements, 1, does not match the expected quantity "2".

-----

In the previous example we could have used xpath instead of css selector:

.. code-block:: python

    >>> String(name='name', xpath='*[@class="full-name"]', quant=1).parse(html)
    {'name': u'Barack Obama'}


-----

By default, ``String`` parses out the text content of the element. To extract the data from an HTML attribute, use ``attr`` parameter:

.. code-block:: python

    >>> String(name='demographics-css-class', css='#demographics', quant=1, attr='class').parse(html)
    {'demographics-css-class': u'demographic-info adr editable-item'}


-----

To parse out the number of connections, which are stored like this:

.. code-block:: html

    <div class="member-connections">
        <strong>500+</strong>
        connections
    </div>


We would like to extract the whole text "*500+ connections*".
By default, ``String`` parser extracts only the text directly from the matched elements, but not their descendants.
In the above case, if we matched ``.member-connections`` element, by default it would parse out only the text "*connections*".

To parse out the text out of every descendant element, use the ``attr`` parameter with the special value ``"_all_text"``:

.. code-block:: python

    >>> String(name='connections', css='.profile-overview .member-connections', quant=1, attr='_all_text').parse(html)
    {'connections': u'500+ connections'}


-----

To parse out the url of the profile picture, use ``Url`` parser instead of ``String``:

.. code-block:: python

    >>> Url(name='profile-picture', css='.profile-picture img', quant=1, attr='src').parse(html, url=url)
    {'profile-picture': u'https://media.licdn.com/mpr/mpr/shrink_200_200/p/2/000/1a3/129/3a73f4c.jpg'}


When you use ``Url`` parser and pass ``url`` parameter to ``parse()`` method,
the parser will parse out the absolute url address.
By default, ``Url`` parses the value out of ``"href"`` attribute of the matched element.
If you want to parse the value out of a different attribute (e.g. ``"src"``), pass it as ``attr`` parameter.

-----

To parse out the list of jobs and from each job to store the company name and the title,
use ``Group`` parser to group the data of each job together:

.. code-block:: python

    >>> Group(name='jobs', css='#background-experience .section-item', quant='*', children=[
    ...     String(name='title', css='h4', quant=1),
    ...     String(name='company', css='h5', quant=1, attr='_all_text')
    ... ]).parse(html)
    {'jobs': [
        {'company': u'United States of America', 'title': u'President'},
        {'company': u'US Senate (IL-D)', 'title': u'US Senator'},
        {'company': u'Illinois State Senate', 'title': u'State Senator'},
        {'company': u'University of Chicago Law School', 'title': u'Senior Lecturer in Law'}]}


In this case the ``Group`` parser's css selector "*#background-experience .section-item*" matched
four elements, each of those containing a single ``h4`` and ``h5`` elements.


================
Parser reference
================

------
String
------

This is the most basic parser.

---
Url
---



-------
Element
-------


=================
Parser parameters
=================

-----------
css / xpath
-----------

**Parsers**: ``Prefix``, ``Group``, ``Element``, ``String``, ``Url``, ``DateTime``

Use either ``css`` or ``xpath`` argument (but not both) to select the elements from which to parse the data.

Under the hood, css selectors are translated into equivalent xpath selectors with *cssselect* library.

For hierarchical parsers (``Prefix``, ``Group``), the descendant parsers are always selected relative to the elements matched by the parent parser.

.. code-block:: python

    # use // prefix for the root xpath
    Prefix(xpath='//*[@id="profile"]', children=[
        # this parser is translated into: //*[@id="profile"]/descendant::*[@class="full-name"]
        String(name='name', css='.full-name', quant=1),
        # this parser is translated into: //*[@id="profile"]/*[@class="title"]
        String(name='title', xpath='*[@class="title"]', quant=1),
        # this parser is translated into: //*[@class="title"]
        # because of // (see the xpath definition). Probably not what you want.
        String(name='title', xpath='//*[@class="title"]', quant=1)
    ])


-----
quant
-----

**Parsers**: ``Group``, ``Element``, ``String``, ``Url``, ``DateTime``

**Default value**: ``'*'``

Number of elements matched with either css or xpath selector is validated against the ``quant`` parameter.
If the number of elements doesn't match the expected quantity, ``ParsingError`` exception is raised.
In practice you can use this and be notified when the crawled website changes its HTML structure.

Syntax for ``quant`` mimics the regular expressions.
You can either pass them as string, single integer or a tuple of two integers.

Value of ``quant`` also modifies whether the result of parsing will be a single value or a list of values.

+-------------------+-----------------------------------------------+-----------------------------+
| Value of ``quant``| Meaning                                       | Result of parsing           |
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
