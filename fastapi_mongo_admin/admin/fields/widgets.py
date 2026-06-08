"""Widget type constants for admin forms."""

TEXT = "text"
TEXTAREA = "textarea"
NUMBER = "number"
CHECKBOX = "checkbox"
SELECT = "select"
DATE = "date"
DATETIME = "datetime-local"
EMAIL = "email"
JSON_EDITOR = "json"
OBJECT_ID = "objectid"
HIDDEN = "hidden"


def widget_for_type(field_type: str) -> str:
    """Map inferred type to HTML widget."""
    mapping = {
        "str": TEXT,
        "int": NUMBER,
        "float": NUMBER,
        "decimal": NUMBER,
        "bool": CHECKBOX,
        "datetime": DATETIME,
        "date": DATE,
        "list": JSON_EDITOR,
        "dict": JSON_EDITOR,
        "ObjectId": OBJECT_ID,
    }
    return mapping.get(field_type, TEXT)
