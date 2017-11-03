# -*- coding: utf-8 -*-
"""Family module for Wikidata."""
#
# (C) Pywikibot team, 2012-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import config
from pywikibot import family

# The Wikidata family


class Family(family.WikimediaFamily):

    """Family class for Wikidata."""

    name = 'wikidata'
    test_codes = ('test', )

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.langs = {
            'wikidata': 'www.wikidata.org',
            'test': 'test.wikidata.org',
        }

        self.interwiki_forward = 'wikipedia'

        self.category_redirect_templates = {
            'wikidata': (
                'Category redirect',
            ),
        }

        # Subpages for documentation.
        self.doc_subpages = {
            '_default': ((u'/doc', ), ['wikidata']),
        }

        # Disable cosmetic changes
        config.cosmetic_changes_disable.update({
            'wikidata': ('wikidata', 'test')
        })

    def interface(self, code):
        """Return 'DataSite'."""
        return 'DataSite'

    def calendarmodel(self, code):
        """Default calendar model for WbTime datatype."""
        return 'https://www.wikidata.org/entity/Q1985727'

    def shared_geo_shape_repository(self, code):
        """Return Wikimedia Commons as the repository for geo-shapes."""
        # Per geoShapeStorageFrontendUrl settings in Wikibase
        return ('commons', 'commons')

    def shared_tabular_data_repository(self, code):
        """Return Wikimedia Commons as the repository for tabular-datas."""
        # Per tabularDataStorageFrontendUrl settings in Wikibase
        return ('commons', 'commons')

    def default_globe(self, code):
        """Default globe for Coordinate datatype."""
        return 'earth'

    def globes(self, code):
        """Supported globes for Coordinate datatype."""
        return {
            'ariel': 'https://www.wikidata.org/entity/Q3343',
            'callisto': 'https://www.wikidata.org/entity/Q3134',
            'ceres': 'https://www.wikidata.org/entity/Q596',
            'deimos': 'https://www.wikidata.org/entity/Q7548',
            'dione': 'https://www.wikidata.org/entity/Q15040',
            'earth': 'https://www.wikidata.org/entity/Q2',
            'enceladus': 'https://www.wikidata.org/entity/Q3303',
            'eros': 'https://www.wikidata.org/entity/Q16711',
            'europa': 'https://www.wikidata.org/entity/Q3143',
            'ganymede': 'https://www.wikidata.org/entity/Q3169',
            'gaspra': 'https://www.wikidata.org/entity/Q158244',
            'hyperion': 'https://www.wikidata.org/entity/Q15037',
            'iapetus': 'https://www.wikidata.org/entity/Q17958',
            'io': 'https://www.wikidata.org/entity/Q3123',
            'jupiter': 'https://www.wikidata.org/entity/Q319',
            'lutetia': 'https://www.wikidata.org/entity/Q107556',
            'mars': 'https://www.wikidata.org/entity/Q111',
            'mercury': 'https://www.wikidata.org/entity/Q308',
            'mimas': 'https://www.wikidata.org/entity/Q15034',
            'miranda': 'https://www.wikidata.org/entity/Q3352',
            'moon': 'https://www.wikidata.org/entity/Q405',
            'oberon': 'https://www.wikidata.org/entity/Q3332',
            'phobos': 'https://www.wikidata.org/entity/Q7547',
            'phoebe': 'https://www.wikidata.org/entity/Q17975',
            'pluto': 'https://www.wikidata.org/entity/Q339',
            'rhea': 'https://www.wikidata.org/entity/Q15050',
            'steins': 'https://www.wikidata.org/entity/Q150249',
            'tethys': 'https://www.wikidata.org/entity/Q15047',
            'titan': 'https://www.wikidata.org/entity/Q2565',
            'titania': 'https://www.wikidata.org/entity/Q3322',
            'triton': 'https://www.wikidata.org/entity/Q3359',
            'umbriel': 'https://www.wikidata.org/entity/Q3338',
            'venus': 'https://www.wikidata.org/entity/Q313',
            'vesta': 'https://www.wikidata.org/entity/Q3030',
        }
