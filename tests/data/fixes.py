"""Collection of fixes for tests."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
# flake8 cannot detect that fixes is defined via pywikibot.fixes
if 'fixes' not in globals():
    fixes = {}

fixes['has-msg'] = {
    'regex': False,
    'msg': {
        'en': 'en',
        'de': 'de',
    },
    'replacements': [
        ('1', '2'),
    ]
}

fixes['has-msg-tw'] = {
    'regex': False,
    'msg': 'replace-replacing',
    'replacements': [
        ('1', '2'),
    ]
}

fixes['no-msg'] = {
    'regex': False,
    'replacements': [
        ('1', '2'),
    ]
}

fixes['all-repl-msg'] = {
    'regex': False,
    'replacements': [
        ('1', '2', 'M1'),
    ]
}

fixes['partial-repl-msg'] = {
    'regex': False,
    'replacements': [
        ('1', '2', 'M1'),
        ('3', '4'),
    ]
}

fixes['has-msg-multiple'] = {
    'regex': False,
    'msg': {
        'en': 'en',
        'de': 'de',
    },
    'replacements': [
        ('1', '2'),
        ('3', '4'),
        ('5', '6'),
    ]
}

fixes['no-msg-title-exceptions'] = {
    'regex': False,
    'exceptions': {
        'title': ['Declined'],
        'require-title': ['Allowed'],
    },
    'replacements': [
        ('1', '2'),
    ]
}

fixes['no-msg-callable'] = {
    'regex': False,
    'replacements': [
        ('1', lambda match: str(match.start())),
    ]
}
