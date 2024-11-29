"""Title translate module."""
#
# (C) Pywikibot team, 2003-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot
from pywikibot import config, date


def translate(
    page=None,
    hints: list[str] | None = None,
    auto: bool = True,
    removebrackets: bool = False,
    site=None
) -> list[pywikibot.Link]:
    """Return a list of links to pages on other sites based on hints.

    Entries for single page titles list those pages. Page titles for
    entries such as "all:" or "xyz:" or "20:" are first built from the
    page title of 'page' and then listed.

    .. versionchanged:: 9.6
       Raise ``RuntimeError`` instead of ``AssertionError`` if neither
       *page* nor *site* parameter is given.

    :param auto: If  true, known year and date page titles are
        autotranslated to all known target languages and inserted into
        the list.
    :param removebrackets: If True, a trailing pair of brackets and the
        text between them is removed from the page title.
    :raises RuntimeError: Either page or site parameter must be given.
    """
    if not page and not site:
        raise RuntimeError(
            'Either page or site parameter must be given with translate()')

    site = site or page.site
    result = set()

    if hints is None:
        hints = []

    for h in hints:
        # argument may be given as -hint:xy where xy is a language code
        codes, _, newname = h.partition(':')
        if not newname:
            # if given as -hint:xy or -hint:xy:, assume that there should
            # be a page in language xy with the same title as the page
            # we're currently working on ...
            if page is None:
                continue
            newname = page.title(with_ns=False,
                                 without_brackets=removebrackets)
        if codes.isdigit():
            codes = site.family.languages_by_size[:int(codes)]
        elif codes == 'all':
            codes = list(site.family.codes)
        else:
            codes = site.family.language_groups.get(codes, codes.split(','))

        for newcode in codes:
            if newcode in site.codes:
                if newcode != site.code:
                    ns = page.namespace() if page else 0
                    link = pywikibot.Link(newname,
                                          site.getSite(code=newcode),
                                          default_namespace=ns)
                    result.add(link)
            elif config.verbose_output:
                pywikibot.info(f'Ignoring unknown language code {newcode}')

    # Autotranslate dates into all other languages, the rest will come from
    # existing interwiki links.
    if auto and page:
        # search inside all dictionaries for this link
        dict_name, value = page.autoFormat()
        if dict_name:
            pywikibot.info(f'TitleTranslate: {page.title()} was recognized as '
                           f'{dict_name} with value {value}')
            for entry_lang, entry in date.formats[dict_name].items():
                if entry_lang not in site.codes:
                    continue

                if entry_lang != page.site.lang:
                    link = pywikibot.Link(entry(value),
                                          site.getSite(entry_lang))
                    result.add(link)

    return list(result)
