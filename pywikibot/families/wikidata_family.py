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
        return 'http://www.wikidata.org/entity/Q1985727'

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
            'ariel': 'http://www.wikidata.org/entity/Q3343',
            'callisto': 'http://www.wikidata.org/entity/Q3134',
            'ceres': 'http://www.wikidata.org/entity/Q596',
            'deimos': 'http://www.wikidata.org/entity/Q7548',
            'dione': 'http://www.wikidata.org/entity/Q15040',
            'earth': 'http://www.wikidata.org/entity/Q2',
            'enceladus': 'http://www.wikidata.org/entity/Q3303',
            'eros': 'http://www.wikidata.org/entity/Q16711',
            'europa': 'http://www.wikidata.org/entity/Q3143',
            'ganymede': 'http://www.wikidata.org/entity/Q3169',
            'gaspra': 'http://www.wikidata.org/entity/Q158244',
            'hyperion': 'http://www.wikidata.org/entity/Q15037',
            'iapetus': 'http://www.wikidata.org/entity/Q17958',
            'io': 'http://www.wikidata.org/entity/Q3123',
            'jupiter': 'http://www.wikidata.org/entity/Q319',
            'lutetia': 'http://www.wikidata.org/entity/Q107556',
            'mars': 'http://www.wikidata.org/entity/Q111',
            'mercury': 'http://www.wikidata.org/entity/Q308',
            'mimas': 'http://www.wikidata.org/entity/Q15034',
            'miranda': 'http://www.wikidata.org/entity/Q3352',
            'moon': 'http://www.wikidata.org/entity/Q405',
            'oberon': 'http://www.wikidata.org/entity/Q3332',
            'phobos': 'http://www.wikidata.org/entity/Q7547',
            'phoebe': 'http://www.wikidata.org/entity/Q17975',
            'pluto': 'http://www.wikidata.org/entity/Q339',
            'rhea': 'http://www.wikidata.org/entity/Q15050',
            'steins': 'http://www.wikidata.org/entity/Q150249',
            'tethys': 'http://www.wikidata.org/entity/Q15047',
            'titan': 'http://www.wikidata.org/entity/Q2565',
            'titania': 'http://www.wikidata.org/entity/Q3322',
            'triton': 'http://www.wikidata.org/entity/Q3359',
            'umbriel': 'http://www.wikidata.org/entity/Q3338',
            'venus': 'http://www.wikidata.org/entity/Q313',
            'vesta': 'http://www.wikidata.org/entity/Q3030',
        }
