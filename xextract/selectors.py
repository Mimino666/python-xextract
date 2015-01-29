from cssselect import GenericTranslator

from .quantity import Quantity


class SelectorError(Exception):
    pass


class BaseSelector(object):
    def __init__(self, name=None, css=None, xpath=None, num='*'):
        self.name = name
        if (xpath is None) == (css is None):
            raise SelectorError('Exactly one of `xpath` or `css` attributes must be specified.')

        if xpath is not None:
            self.raw_xpath = xpath
        else:
            self.raw_xpath = GenericTranslator().css_to_xpath(css)
        self.compiled_xpath = None
        self.quantity = Quantity(num)


class Element(BaseSelector):
    def __init__(self, group=None, *args, **kwargs):
        super(Element, self).__init__(*args, **kwargs)
        self.group = group
        self.children = []


class String(BaseSelector):
    def __init__(self, attr=None, *args, **kwargs):
        super(String, self).__init__(*args, **kwargs)
        self.attr = attr

        if self.name is None:
            raise SelectorError('Attribute `name` must be set for String selectors.')


class Url(String):
    pass
