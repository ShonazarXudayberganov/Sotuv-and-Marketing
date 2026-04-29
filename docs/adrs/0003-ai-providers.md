# ADR-0003: AI provayder strategiyasi

**Holat:** Qabul qilingan
**Sana:** 2026-04-29

## Kontekst

LLM, embedding, audio va image AI uchun provayder tanlash.

## Variantlar

### A. Single provider (faqat OpenAI yoki Anthropic)
- ✅ Sodda
- ❌ Single point of failure

### B. Multi-provider, fallback bilan
- ✅ Resilience
- ✅ Cost optimization
- ❌ Murakkabroq abstraction

### C. Self-hosted models
- ✅ Cost (uzoq muddat)
- ✅ Privacy
- ❌ Sifat past (open models o'zbek tilida)
- ❌ Infra murakkab

## Qaror

**Variant B — Multi-provider.**

| Vazifa | Asosiy | Backup |
|---|---|---|
| LLM (Claude family) | Anthropic Claude | OpenAI GPT-4 |
| Embedding | OpenAI text-embedding-3 | — |
| Audio | OpenAI Whisper | — |
| Image | OpenAI gpt-image | DALL-E 3 |

## Sabablar

- Claude — eng yaxshi reasoning, o'zbek tilida ham yaxshi
- GPT-4 — ishonchli backup, mavjud
- Embedding — OpenAI text-embedding-3-small arzon va sifatli
- Whisper — eng yaxshi audio (o'zbek qo'llab-quvvatlash)

## Oqibatlar

- Abstraction layer kerak (`app/ai/providers/`)
- Cost monitoring per-provider
- Fallback test — har sprint
