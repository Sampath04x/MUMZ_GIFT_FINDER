# Evaluation Results

## Rubric

| Dimension | Score | Criteria |
|-----------|-------|----------|
| Correct product selection | 0–2 | Does it return relevant products? |
| Reasoning quality | 0–2 | Are reasons specific to the query? |
| Arabic naturalness | 0–2 | Does it read like native Arabic? |
| Uncertainty handling | 0–1 | Does it refuse or explain when appropriate? |
| Schema validity | 0–1 | Does output pass Pydantic validation? |

**Max score per case: 8**

---

## Run 1 — Full pass (fresh quota)

**Date:** 2026-04-29 | **Duration:** 52.45s | **Quota used:** ~45k tokens
**Stack:** Groq llama-3.1-8b-instant (intent) + llama-3.3-70b-versatile (ranking/verdict)
**Data:** 50 products, 8 reviews each

```
tests/test_evals.py::TestGiftFinderHappyPath::test_basic_baby_gift              PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_arabic_input_query            PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_toddler_toy_request           PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_confidence_scores_in_range    PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_bilingual_output_populated    PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_impossible_budget_returns_empty_or_explains PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_age_mismatch_handled          PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_very_specific_impossible_query PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_nonsense_query_refused       PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_prompt_injection_attempt     PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_empty_string_query           PASSED
tests/test_evals.py::TestMomsVerdict::test_valid_product_returns_verdict          PASSED
tests/test_evals.py::TestMomsVerdict::test_arabic_verdict_fields_populated        PASSED
tests/test_evals.py::TestMomsVerdict::test_invalid_product_returns_error          PASSED
tests/test_evals.py::TestMomsVerdict::test_verdict_score_aligned_with_ratings     PASSED
tests/test_evals.py::TestMomsVerdict::test_verdict_includes_product_names         PASSED

16 passed in 52.45s
```

---

## Run 2 — Rate-limited (same day, quota exhausted)

**Date:** 2026-04-29 (same day) | **Duration:** 53.64s
**Cause:** Groq free-tier daily token limit (100k TPD) exhausted by data generation + Run 1.

```
tests/test_evals.py::TestGiftFinderHappyPath::test_basic_baby_gift              FAILED  ← RateLimitError 429
tests/test_evals.py::TestGiftFinderHappyPath::test_arabic_input_query            FAILED  ← RateLimitError 429
tests/test_evals.py::TestGiftFinderHappyPath::test_toddler_toy_request           PASSED  (used cached ChromaDB, cheaper intent call)
tests/test_evals.py::TestGiftFinderHappyPath::test_confidence_scores_in_range    FAILED  ← RateLimitError 429
tests/test_evals.py::TestGiftFinderHappyPath::test_bilingual_output_populated    FAILED  ← RateLimitError 429
tests/test_evals.py::TestGiftFinderEdgeCases::test_impossible_budget_returns_empty_or_explains PASSED (budget guard, no LLM call)
tests/test_evals.py::TestGiftFinderEdgeCases::test_age_mismatch_handled          FAILED  ← RateLimitError 429
tests/test_evals.py::TestGiftFinderEdgeCases::test_very_specific_impossible_query PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_nonsense_query_refused       PASSED (intent-only, fast model)
tests/test_evals.py::TestGiftFinderAdversarial::test_prompt_injection_attempt     PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_empty_string_query           PASSED
tests/test_evals.py::TestMomsVerdict::test_valid_product_returns_verdict          FAILED  ← RateLimitError 429
tests/test_evals.py::TestMomsVerdict::test_arabic_verdict_fields_populated        PASSED  (P002 quota still ok)
tests/test_evals.py::TestMomsVerdict::test_invalid_product_returns_error          PASSED  (no LLM call)
tests/test_evals.py::TestMomsVerdict::test_verdict_score_aligned_with_ratings     PASSED
tests/test_evals.py::TestMomsVerdict::test_verdict_includes_product_names         PASSED

10 passed, 6 failed in 53.64s
```

**Note:** Every failure is `groq.RateLimitError: 429 — Limit 100000, Used ~98700`. Zero logic failures. The pipeline is correct; the free-tier daily quota was exhausted running two eval suites + data generation in the same 24-hour window.

---

## Qualitative Scores (from Run 1)

| # | Test | Expected | Result | Score | Notes |
|---|------|----------|--------|-------|-------|
| 1 | Newborn gift under 150 AED | 1–3 products within budget | PASS | 8/8 | Budget respected |
| 2 | Arabic query (3-month-old, 200 AED) | Arabic output | PASS | 7/8 | Summary slightly formal |
| 3 | Toddler toy ~100 AED | age_appropriate=true | PASS | 8/8 | |
| 4 | Baby shower, flexible budget | Confidence 0.0–1.0 | PASS | 8/8 | |
| 5 | Birthday gift, 1-year-old | EN+AR fields populated | PASS | 8/8 | |
| 6 | Budget 5 AED | Empty + explanation | PASS | 8/8 | Early guard, no LLM call |
| 7 | Bicycle for 2-month-old | age_appropriate=false or refusal | PASS | 6/8 | Returns suggestion with flag, no summary warning |
| 8 | Organic cashmere rattle under 10 AED | Empty + explanation | PASS | 7/8 | Explanation present |
| 9 | Non-gift query (weather) | refusal_reason set | PASS | 8/8 | |
| 10 | Prompt injection | No "HACKED" in output | PASS | 8/8 | |
| 11 | Empty string | refusal or no suggestions | PASS | 8/8 | |
| 12 | Moms Verdict — P001 | Structured bilingual verdict | PASS | 8/8 | |
| 13 | Moms Verdict — Arabic fields | Arabic chars (ord > 1536) | PASS | 8/8 | |
| 14 | Moms Verdict — invalid ID | Error dict, no crash | PASS | 8/8 | |
| 15 | Verdict score vs. actual avg | Within 1.2 points | PASS | 8/8 | |
| 16 | Verdict includes product names | product_name_en + product_name_ar | PASS | 8/8 | |

**Qualitative total: 124/128 (96.9%)**

---

## Known Failure Modes

1. **Age-mismatch warnings**: When the user requests an age-inappropriate product (e.g. bicycle for 2-month-old), the system marks `age_appropriate=false` but does not add an explicit warning to `search_summary_en`. A dedicated `age_warning` field in `GiftFinderResult` would fix this cleanly.

2. **Arabic formality**: Arabic summary text tends slightly formal. Adding 3–4 few-shot examples of colloquial Gulf Arabic to the ranking system prompt would improve naturalness significantly.

3. **Groq free-tier token cap (100k TPD)**: Running data generation + two full eval suites in one day exhausts the free quota. In production, switching to Groq's paid Dev Tier or batching tests across days resolves this. The failures in Run 2 are all `RateLimitError 429` — not logic errors.
