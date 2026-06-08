Date, Time, and Save Messages
=============================

Date and time display
---------------------

``date`` and ``datetime`` model fields are formatted for display on:

* Changelist columns
* Readonly fields on add/change forms

Editable form inputs still use ISO strings (``YYYY-MM-DD`` and ``YYYY-MM-DDTHH:MM``)
for HTML date and datetime-local widgets.

Default formats
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1

   * - Type
     - Example
   * - ``date``
     - ``8 Apr 2026``
   * - ``datetime``
     - ``8 Apr 2026, 7:32pm``

Configuration
~~~~~~~~~~~~~

Set formats on ``ModelAdmin``:

.. code-block:: python

   class OrderAdmin(ModelAdmin):
       date_format = "j M Y"
       datetime_format = "%d/%m/%Y %H:%M"

Two format styles are supported:

**Django-style tokens** (no ``%``):

.. list-table::
   :header-rows: 1

   * - Token
     - Meaning
   * - ``j``
     - Day without leading zero
   * - ``M``
     - Short month name
   * - ``Y``
     - Four-digit year
   * - ``g``
     - 12-hour hour without leading zero
   * - ``i``
     - Minutes with leading zero
   * - ``a``
     - ``am`` / ``pm``

Example: ``"j M Y, g:ia"`` → ``8 Apr 2026, 7:32pm``

**strftime** (with ``%``):

.. code-block:: python

   datetime_format = "%Y-%m-%d %H:%M"

Hooks
~~~~~

Override formatting per model:

.. code-block:: python

   def format_datetime_value(self, value) -> str:
       return my_custom_formatter(value)

   def format_date_value(self, value) -> str:
       return my_custom_formatter(value)

Implementation lives in ``fastapi_mongo_admin.formatting``.

Save notifications
------------------

After a successful **add** or **change**, the admin:

1. Redirects to the model changelist (``/admin/{collection}/``)
2. Sets a one-time flash cookie with the saved item's label
3. Shows a green success banner at the top of the changelist

Messages (English defaults):

* **Add:** ``"{object}" was added successfully.``
* **Change:** ``"{object}" was saved successfully.``

The ``{object}`` label is resolved by ``ModelAdmin.object_repr()``:

1. First ``list_display_links`` column
2. First ``list_display`` column
3. Common fields: ``name``, ``title``, ``slug``, ``email``, ``order_number``, ``code``
4. Document ``id``
5. Model name (fallback)

Example:

.. code-block:: python

   class CategoryAdmin(ModelAdmin):
       list_display_links = ["name"]
       # Saving "Electronics" shows: "Electronics" was saved successfully.

Override the label:

.. code-block:: python

   def object_repr(self, request, obj: dict) -> str:
       return f"{obj.get('first_name', '')} {obj.get('last_name', '')}".strip()

Flash cookies are cleared after the banner is shown. HTMX pagination partials do
not re-display the message.

Internationalization
~~~~~~~~~~~~~~~~~~~~

Message keys ``saved_added`` and ``saved_changed`` are translated in all
supported languages. See :doc:`i18n-theme`.
