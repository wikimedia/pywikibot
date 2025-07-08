# -*- coding: utf-8 -*-


from http import HTTPStatus
from pywikibot import family
import requests


class Family(family.Family):

    @classmethod
    def __post_init__(self):
        response = requests.get('https://liquipedia.net/api.php?action=listwikis', headers={'accept-encoding': 'gzip'})
        if response.status_code != HTTPStatus.OK:
            print(response.text)
            return
        wikis = response.json()
        for game in wikis['allwikis'].keys():
            self.langs[game] = 'liquipedia.net'

    name = 'liquipedia'

    def scriptpath(self, code):
        return '/' + code

    def protocol(self, code):
        return u'https'
