import re
import unicodedata

_SCHEMA_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{0,62}$")


def slugify_schema(name: str) -> str:
    """Convert a company name into a safe PostgreSQL schema identifier.

    Always prefixed with `tenant_` to avoid collisions with `public` and to make
    cross-tenant leaks easier to detect in logs.
    """
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized).strip("_").lower()
    slug = slug[:50] or "x"
    return f"tenant_{slug}"


def validate_schema_name(schema: str) -> str:
    """Defense-in-depth: refuse anything that isn't a safe identifier.

    Used in DB session setup before `SET search_path`. The schema name comes
    from a signed JWT, but we revalidate to prevent SQL injection in case of
    a compromised secret or middleware bug.
    """
    if not _SCHEMA_NAME_RE.match(schema):
        raise ValueError(f"Unsafe schema identifier: {schema!r}")
    return schema
