********
xextract
********

*NOTE*: library is still under construction.

**xextract** is an HTML parsing library that solves the following problems for you:

- Simple declarative style of parsers
- Parsing of HTML and XML documents
- Use xpaths or css selectors to extract the data
- Parsers are self-validating and let you know when the structure of website has changed
- Speed - under the hood the library uses lxml library (http://lxml.de/) with compiled xpath selectors
- You can optionally define the parsers in external XML files to separate the parsing from other business logic


====================
A little taste of it
====================

.. code-block:: python

  from xextract import Prefix, Group, String, Url
  # fetch web page
  import requests
  response = requests.get('https://www.linkedin.com/in/barackobama')

  parser = Prefix(css='#profile', children=[
      String(name='name', css='.full-name', quant=1),
      String(name='title', css='.title', quant=1),
      Group(name='experience', css='#background-experience .section-item', quant='*', children=[
          String(name='title', css='h4', quant=1),
          String(name='company', css='h5', quant=1, attr='_all_text'),
          Url(name='company_url', css='h5 a', quant='?'),
          String(name='description', css='.description', quant='?')
      ])
  ])
  parser.parse_html(response.text, url=response.url)


Output:

.. code-block:: python

  {'name': u'Barack Obama',
   'title': u'President of the United States of America',
   'experience': [
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

Python 2.6, 2.7 and 3.x are supported.


===========
Basic usage
===========

In the examples below we will demonstrate how to parse the data from a Linkedin profile,
so include the following code to the top of the file:

.. code-block:: python

    from xextract import Prefix, Group, Element, String, Url
    import requests
    response = requests.get('https://www.linkedin.com/in/barackobama')
    html, url = response.text, response.url


To parse out the name from the Linkedin profile, call:

.. code-block:: python

    >>> String(name='name', css='.full-name', quant=1).parse_html(html)
    {'name': u'Barack Obama'}


You can see that the parsed data are returned in a dictionary.

Parameters we passed to the parser have the following meaning:

- ``name`` - dictionary key under which to store the parsed data.
- ``css`` - css selector to the HTML element.
- ``quant`` - number of an HTML elements we expect to match with the css selector. In this case we expect exactly one element with the css class ``full-name``. If the number of elements wouldn't match, ``ParsingError`` exception is raised:

    .. code-block:: python

        >>> String(name='name', css='.full-name', quant=2).parse_html(html)
        xextract.selectors.ParsingError: Number of "name" elements, 1, does not match the expected quantity "2".

-----

In the previous example we could have used xpath instead of css selector:

.. code-block:: python

    >>> String(name='name', xpath='*[@class="full-name"]', quant=1).parse_html(html)
    {'name': u'Barack Obama'}


-----

By default ``String`` parses out the text content of the element. To extract the data from an HTML attribute, pass ``attr`` parameter:

.. code-block:: python

    >>> String(name='demographics-css-class', css='#demographics', quant=1, attr='class').parse_html(html)
    {'demographics-css-class': u'demographic-info adr editable-item'}


-----

To parse out the number of connections, which are stored like this:

.. code-block:: html

    <div class="member-connections">
        <strong>500+</strong>
        connections
    </div>


We would like to extract the whole string "*500+ connections*".
By default ``String`` parser extracts only the text from the matched elements, but not their descendants.
In the above case, if we matched ``.member-connections`` element, by default it would parse out only the string "*connections*".

To parse out the text out of every descendant element, pass the ``attr`` parameter with the special value ``_all_text``:

.. code-block:: python

    >>> String(name='connections', css='.profile-overview .member-connections', quant=1, attr='_all_text').parse_html(html)
    {'connections': u'500+ connections'}


-----

To parse out the url of the profile picture, use ``Url`` parser instead of ``String``:

.. code-block:: python

    >>> Url(name='profile-picture', css='.profile-picture img', quant=1, attr='src').parse_html(html, url=url)
    {'profile-picture': u'https://media.licdn.com/mpr/mpr/shrink_200_200/p/2/000/1a3/129/3a73f4c.jpg'}


When you use ``Url`` parser and pass ``url`` parameter to ``parse_html()`` method,
the parser will parse out the absolute url address.
We have also passed ``attr`` parameter to the parser with which we specified that we want
to parse the value out of an HTML attribute ``src``.


=========
Reference
=========

-----------
css / xpath
-----------

Use either ``css`` or ``xpath`` argument (but not both) to select from which elements to parse the data.

Under the hood, css selectors are translated into equivalent xpath selectors and then compiled for better performance.

In hierarchical parsers (``Prefix``, ``Group``), the descendant parsers are always selected relative to the elements matched by the parent parser.

.. code-block:: python

    # use // prefix for the root xpath
    Prefix(xpath='//*[@id="profile"]', children=[
        # this parser is translated into: //*[@id="profile"]/descendant::*[@class="full-name"]
        String(name='name', css='.full-name', quant=1),
        # this parser is translated into: //*[@id="profile"]/*[@class="title"]
        String(name='title', xpath='*[@class="title"]', quant=1)
    ])


-----
quant
-----

Number of matched elements is compared to the ``quant`` argument.
If the number of elements doesn't match the expected quantity, ``ParsingError`` exception is raised.

This argument is very useful to specify expectations about the document structure
and be notified, when the expectations are not met.
In practice you can use this and be notified when the crawled website changes its HTML structure.

Syntax for ``quant`` mimics the regular expressions.
You can either pass them as string, single integer or a tuple of two integers.

Value of ``quant`` also modifies whether the parsing process will return a single value or a list of values.

+-------------------+-----------------------------------------------+-----------------------------+
| Value of ``quant``| Meaning                                       | Return from parsing         |
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
|                   | You can pass either string or tuple.          |                             |
+-------------------+-----------------------------------------------+-----------------------------+
