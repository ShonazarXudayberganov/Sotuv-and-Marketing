import pytest

from app.core.tenancy import slugify_schema, validate_schema_name


def test_slugify_basic():
    assert slugify_schema("Akme Salon") == "tenant_akme_salon"


def test_slugify_strips_unicode_and_punctuation():
    assert slugify_schema("Akmé — Salon!") == "tenant_akme_salon"


def test_slugify_empty_falls_back_to_x():
    assert slugify_schema("???") == "tenant_x"


def test_slugify_length_capped():
    long_name = "x" * 200
    result = slugify_schema(long_name)
    assert len(result) <= 63
    assert result.startswith("tenant_")


def test_validate_schema_name_accepts_safe():
    assert validate_schema_name("tenant_akme_salon") == "tenant_akme_salon"


@pytest.mark.parametrize(
    "bad",
    [
        "DROP TABLE",
        "tenant; DROP TABLE users; --",
        "Tenant_With_Caps",
        "1starts_with_digit",
        "",
        "a" * 64,
    ],
)
def test_validate_schema_name_rejects_unsafe(bad: str):
    with pytest.raises(ValueError):
        validate_schema_name(bad)
