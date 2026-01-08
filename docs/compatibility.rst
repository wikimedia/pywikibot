*********************
Version compatibility
*********************

This page summarizes Pywikibot compatibility with Python and MediaWiki versions.

Python and MediaWiki version support
====================================

Released Pywikibot versions support all actively maintained Python and MediaWiki
versions at the time of release:

=================  =====================  ======  ====  =======  =================  ================
Pywikibot version  Python version         No GIL  PyPy  GraalPy  MediaWiki version  1st Release Date
=================  =====================  ======  ====  =======  =================  ================
11.0+              3.9–3.15               ⚠️      ✅    ⚠️       1.31–1.46          2026
10.0–10.7.4        3.8–3.14               ❓      ✅    ❌       1.31–1.44          2025-03-01
9.0–9.6.3          3.7–3.13               ❓      ✅    ❌       1.27–1.42          2024-03-08
8.0–8.6            3.6.1–3.12             ❌      ✅    ❌       1.27–1.41          2023-01-21
7.0–7.7.3          3.5.3–3.11             ❌      ✅    ❌       1.23–1.39          2022-02-26
6.0–6.6.5          3.5–3.10               ❌      ❌    ❌       1.23–1.37          2021-03-16
5.0–5.6            3.5–3.10               ❌      ❌    ❌       1.19–1.36          2020-10-19
4.0–4.3            3.5–3.9                ❌      ❌    ❌       1.14–1.36          2020-08-04
3.0.20190301+      2.7.4–2.7.18, 3.4–3.8  ❌      ❌    ❌       1.14–1.33          2019-03-01
3.0.20180403+      2.7.2–2.7.18, 3.4–3.8  ❌      ❌    ❌       1.14–1.31          2018-04-03
3.0.20170403+      2.6–2.7.18, 3.3–3.8    ❌      ❌    ❌       1.14–1.29          2017-04-04
2.0                2.7, 3.3–3.5           ❌      ❌    ❌       1.14–1.25          2015-05-25
1.0                2.5–2.7                ❌      ❌    ❌       1.2–1.24           2003–2016
=================  =====================  ======  ====  =======  =================  ================

.. admonition:: Version status legend

   **No GIL** – Free-Threading Python build (CPython 3.13+);
   runs without the Global Interpreter Lock (GIL), allowing true multithreading (:pep:`703`).

   | ❌ **not available** – functionality does not exist for this version
   | ❓ **not tested** – has not been verified yet
   | ⚠️ **unstable** – active development, breaking changes possible
   | 🧪 **beta** – feature complete, testing phase
   | ✅ **stable** – production ready
   | 🛡️ **resilient** – long-term proven, robust operation

.. note::
   All versions listed refer to the **stable releases**. Early releases before
   version 3.0 were considered "perpetual beta". The first Pywikibot package,
   formerly known as Pywikipediabot, is also called "trunk" or a "compat" release.

.. seealso::
   - `Status of Python versions <https://devguide.python.org/versions/>`__
   - `Status of MediaWiki versions <https://www.mediawiki.org/wiki/Version_lifecycle>`__.
