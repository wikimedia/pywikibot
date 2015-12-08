FROM debian:jessie

MAINTAINER Pywikibot Team <pywikibot@lists.wikimedia.org>

RUN apt-get update
RUN apt-get install --yes python3.4 python3-pip git libjpeg62-turbo libjpeg62-turbo-dev zlib1g zlib1g-dev locales

# Setup the C.UTF-8 Locale, since otherwise it defaults to an ASCII one
RUN locale-gen C.UTF-8
ENV LC_ALL C.UTF-8

# TODO: Add this to the default PYTHONPATH and PATH?
ADD . /srv/pwb

# pip version in jessie is too old :(
RUN pip3 install -U pip

RUN pip3 install -r /srv/pwb/requirements.txt
RUN pip3 install -r /srv/pwb/dev-requirements.txt
RUN pip3 install /srv/pwb/

CMD /bin/bash
