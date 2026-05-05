"""Fixed Knowledge Base section registry for SMM brand context."""

from __future__ import annotations

from typing import Final

DEFAULT_KNOWLEDGE_SECTION: Final[str] = "brand_overview"

KNOWLEDGE_SECTIONS: Final[tuple[dict[str, str], ...]] = (
    {
        "key": "brand_overview",
        "label": "Brend haqida",
        "description": "Kompaniya tarixi, pozitsiyasi, missiyasi va asosiy farqlari.",
    },
    {
        "key": "products_services",
        "label": "Mahsulot va xizmatlar",
        "description": "Xizmatlar, mahsulotlar, paketlar va ular qanday foyda berishi.",
    },
    {
        "key": "target_audience",
        "label": "Auditoriya",
        "description": "Mijoz segmentlari, ehtiyojlar, og'riqlar va xarid motivlari.",
    },
    {
        "key": "voice_tone",
        "label": "Ovoz va uslub",
        "description": "Yozish ohangi, taqiqlangan iboralar va brendning nutq qoidalari.",
    },
    {
        "key": "faq",
        "label": "FAQ",
        "description": "Ko'p so'raladigan savollar va tayyor javoblar.",
    },
    {
        "key": "pricing_offers",
        "label": "Narxlar va aksiyalar",
        "description": "Narxlar, chegirmalar, bonuslar, tariflar va mavsumiy takliflar.",
    },
    {
        "key": "social_proof",
        "label": "Natijalar va sharhlar",
        "description": "Mijoz fikrlari, case study, raqamlar, sertifikatlar va ishonch signallari.",
    },
    {
        "key": "policies_processes",
        "label": "Qoidalar va jarayonlar",
        "description": "Yetkazish, qaytarish, yozilish, kafolat va ichki ish jarayonlari.",
    },
)

KNOWLEDGE_SECTION_KEYS: Final[frozenset[str]] = frozenset(
    section["key"] for section in KNOWLEDGE_SECTIONS
)


def validate_knowledge_section(value: str | None) -> str:
    key = (value or DEFAULT_KNOWLEDGE_SECTION).strip().lower()
    if key not in KNOWLEDGE_SECTION_KEYS:
        raise ValueError(f"Unknown knowledge section: {key}")
    return key
