"""Family module for Wikidata."""
#
# (C) Pywikibot team, 2012-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import config, family


# The Wikidata family
class Family(family.WikimediaFamily):

    """Family class for Wikidata."""

    name = 'wikidata'

    langs = {
        'wikidata': 'www.wikidata.org',
        'test': 'test.wikidata.org',
        'beta': 'wikidata.beta.wmflabs.org',
    }

    # Sites we want to edit but not count as real languages
    test_codes = ['test', 'beta']

    interwiki_forward = 'wikipedia'

    category_redirect_templates = {
        'wikidata': (
            'Category redirect',
        ),
    }

    # Subpages for documentation.
    doc_subpages = {
        '_default': (('/doc', ), ['wikidata']),
    }

    # Disable cosmetic changes
    config.cosmetic_changes_disable.update({
        'wikidata': ('wikidata', 'test', 'beta')
    })

    def interface(self, code) -> str:
        """Return 'DataSite'."""
        return 'DataSite'

    def calendarmodel(self, code) -> str:
        """Default calendar model for WbTime datatype."""
        return 'http://www.wikidata.org/entity/Q1985727'

    def default_globe(self, code) -> str:
        """Default globe for Coordinate datatype."""
        return 'earth'

    def globes(self, code):
        """Supported globes for Coordinate datatype."""
        return {
            'ariel': 'http://www.wikidata.org/entity/Q3343',
            'bennu': 'http://www.wikidata.org/entity/Q11558',
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
            'ryugu': 'http://www.wikidata.org/entity/Q1385178',
            'steins': 'http://www.wikidata.org/entity/Q150249',
            'tethys': 'http://www.wikidata.org/entity/Q15047',
            'titan': 'http://www.wikidata.org/entity/Q2565',
            'titania': 'http://www.wikidata.org/entity/Q3322',
            'triton': 'http://www.wikidata.org/entity/Q3359',
            'umbriel': 'http://www.wikidata.org/entity/Q3338',
            'venus': 'http://www.wikidata.org/entity/Q313',
            'vesta': 'http://www.wikidata.org/entity/Q3030',
        }
