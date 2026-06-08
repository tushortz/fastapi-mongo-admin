Internationalization and Themes
===============================

The admin includes built-in UI translations and a light/dark theme toggle in the
header. No configuration is required — both features work out of the box.

Supported languages
-------------------

.. list-table::
   :header-rows: 1

   * - Code
     - Language
   * - ``en``
     - English (default)
   * - ``fr``
     - Français
   * - ``pt``
     - Português
   * - ``ru``
     - Русский
   * - ``it``
     - Italiano
   * - ``ch``
     - 中文
   * - ``es``
     - Español
   * - ``de``
     - Deutsch
   * - ``ar``
     - العربية (RTL layout)

Language selection
------------------

**Header dropdown** — select a language from the admin header. The choice is
stored in the ``admin_lang`` cookie (1-year expiry).

**Query string** — force a language and persist it:

.. code-block:: text

   /admin/products/?lang=fr

The admin redirects once to set the cookie, then serves the page in French.

Theme toggle
------------

**Header button** — sun/moon icon toggles light and dark mode.

**Cookie** — ``admin_theme`` stores ``light`` or ``dark``.

**localStorage** — client-side JavaScript also persists theme preference for
instant toggling without a round trip.

**Query string:**

.. code-block:: text

   /admin/products/?theme=dark

RTL support
-----------

Arabic (``ar``) automatically enables right-to-left layout via the ``is_rtl``
template context variable.

Template usage
--------------

Translations are available as ``t`` in all templates:

.. code-block:: html

   <h1>{{ t('site_administration') }}</h1>
   <button>{{ t('save') }}</button>
   <span>{{ t('showing_results', start=1, end=25, total=100) }}</span>

Theme is applied via the ``data-theme`` attribute on the root ``<html>`` element,
along with ``lang`` and optional ``dir="rtl"`` for Arabic.

Preference API
--------------

POST ``/admin/preferences/`` with form fields:

* ``lang`` — language code
* ``theme`` — ``light`` or ``dark``
* ``next_url`` — redirect target after setting preferences

Programmatic cookie setting
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from fastapi_mongo_admin.views.preferences import set_preference_cookies

   response = RedirectResponse(url="/admin/")
   set_preference_cookies(response, lang="fr", theme="dark")

Adding translations
-------------------

Translations live in ``fastapi_mongo_admin/i18n/translations.py``. Each language
maps message keys to translated strings. To add a new language:

1. Add the language code to ``SUPPORTED_LANGUAGES`` in ``translator.py``
2. Add a translation dict in ``translations.py``
3. If RTL, add the code to ``RTL_LANGUAGES``

Customizing translations
------------------------

For app-specific strings in custom templates, use your own i18n solution or
hardcode labels. The built-in ``t`` helper only covers admin UI strings.

CSS themes
----------

* ``fastapi_mongo_admin/static/css/lightmode.css``
* ``fastapi_mongo_admin/static/css/darkmode.css``

The active theme is controlled by ``[data-theme="light"]`` and
``[data-theme="dark"]`` selectors on the root element.

See :doc:`api-reference` for preference and translator APIs.
