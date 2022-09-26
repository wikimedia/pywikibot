"""Decorators for Page objects."""
#
# (C) Pywikibot team, 2017-2022
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot.exceptions import (
    Error,
    OtherPageSaveError,
    PageSaveRelatedError,
)
from pywikibot.tools import add_full_name, manage_wrapping


# decorating this function leads sphinx to hide it
def _allow_asynchronous(func):
    """
    Decorator to make it possible to run a BasePage method asynchronously.

    This is done when the method is called with kwarg asynchronous=True.
    Optionally, you can also provide kwarg callback, which, if provided, is
    a callable that gets the page as the first and a possible exception that
    occurred during saving in the second thread or None as the second argument.

    :meta public:
    """
    def handle(func, self, *args, **kwargs):
        do_async = kwargs.pop('asynchronous', False)
        callback = kwargs.pop('callback', None)
        err = None
        try:
            func(self, *args, **kwargs)
        # TODO: other "expected" error types to catch?
        except Error as edit_err:
            err = edit_err  # edit_err will be deleted in the end of the scope
            link = self.title(as_link=True)
            if do_async:
                pywikibot.error('page {} not saved due to {}\n'
                                .format(link, err))
            pywikibot.log(f'Error saving page {link} ({err})\n',
                          exc_info=True)
            if not callback and not do_async:
                if isinstance(err, PageSaveRelatedError):
                    raise err
                raise OtherPageSaveError(self, err)
        if callback:
            callback(self, err)

    def wrapper(self, *args, **kwargs) -> None:
        if kwargs.get('asynchronous'):
            pywikibot.async_request(handle, func, self, *args, **kwargs)
        else:
            handle(func, self, *args, **kwargs)

    manage_wrapping(wrapper, func)

    return wrapper


#: `_allow_asynchronous` decorated with :func:`tools.add_full_name`
allow_asynchronous = add_full_name(_allow_asynchronous)
