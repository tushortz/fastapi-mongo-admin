"""Boolean changelist label tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import Product, ProductAdmin


def test_boolean_display_cell() -> None:
    admin = ProductAdmin(Product)
    true_cell = admin.boolean_display_cell(
        "active",
        {"active": True},
        true_label="Yes",
        false_label="No",
    )
    false_cell = admin.boolean_display_cell(
        "active",
        {"active": False},
        true_label="Yes",
        false_label="No",
    )
    assert true_cell == {"boolean": True, "label": "Yes"}
    assert false_cell == {"boolean": False, "label": "No"}
    assert admin.boolean_display_cell("name", {"name": "Phone"}, true_label="Yes", false_label="No") is None


@pytest.mark.asyncio
async def test_changelist_renders_boolean_labels(client: AsyncClient) -> None:
    response = await client.get("/admin/products/")
    assert response.status_code == 200
    assert 'class="bool-label bool-label--true"' in response.text
    assert 'class="bool-label bool-label--false"' in response.text
    assert ">Yes<" in response.text
    assert ">No<" in response.text
