# matchers.py
# Original author: Krzysiek Goj
# Copyright (C) 2008 Orestis Markou
# All rights reserved
# E-mail: orestis@orestis.gr

# http://orestis.gr

# Released subject to the BSD License 

import re
try:
    all
except:
     def all(iterable):
         for element in iterable:
             if not element:
                 return False
         return True

def matchCaseInsensitively(base):
    return lambda comp: comp.lower().startswith(base.lower())

def matchCaseSensitively(base):
    return lambda comp: comp.startswith(base)

CAMEL_GROUP_RE = re.compile('[0-9]+|[^#][#]*|[#]+'.replace('#', 'a-z'))
def camelGroups(word):
    return CAMEL_GROUP_RE.findall(word)

def matchCamelCasedPrecise(base):
    baseGr = camelGroups(base)
    baseLen = len(baseGr)
    def check(comp):
        compGr = camelGroups(comp)
        return baseLen <= len(compGr) and all(matchCaseSensitively(bg)(cg) for bg, cg in zip(baseGr, compGr))
    return check

def matchCamelCased(base):
    baseGr = camelGroups(base)
    baseLen = len(baseGr)
    def check(comp):
        compGr = camelGroups(comp)
        return baseLen <= len(compGr) and all(matchCaseInsensitively(bg)(cg) for bg, cg in zip(baseGr, compGr))
    return check

def matchSmartass(base):
    rev_base_letters = list(reversed(base.lower()))
    def check(comp):
        stack = rev_base_letters[:]
        for group in camelGroups(comp):
            lowered = group.lower()
            while True:
                if lowered and stack:
                    if lowered.startswith(stack[-1]):
                        stack.pop()
                    lowered = lowered[1:]
                else:
                    break
        return not stack
    return check

def matchFuzzyCS(base):
    regex = re.compile('.*'.join([] + list(base) + []))
    return lambda comp: bool(regex.match(comp))

def matchFuzzyCI(base):
    regex = re.compile('.*'.join([] + list(base) + []), re.IGNORECASE)
    return lambda comp: bool(regex.match(comp))


class MatchDict(object):
    _MATCHERS = {
        'case-sensitive': matchCaseSensitively,
        'case-insensitive': matchCaseInsensitively,
        'camel-case': matchCamelCased,
        'camel-case-sensitive': matchCamelCasedPrecise,
        'smartass': matchSmartass,
        'fuzzy-ci': matchFuzzyCI,
        'fuzzy-cs': matchFuzzyCS,
    }

    def __getitem__(self, item):
        return self._MATCHERS.get(item, matchCaseInsensitively)

MATCHERS = MatchDict()
