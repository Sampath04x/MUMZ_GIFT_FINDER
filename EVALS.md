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

## Real Eval Run — pytest results

Run on: 50 products, 8 reviews each, Groq llama-3.1-8b-instant (intent) + llama-3.3-70b-versatile (ranking/verdict)
Command: `pytest tests/test_evals.py -v -s`
Duration: 52.45s

```
tests/test_evals.py::TestGiftFinderHappyPath::test_basic_baby_gift         PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_arabic_input_query       PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_toddler_toy_request      PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_confidence_scores_in_range PASSED
tests/test_evals.py::TestGiftFinderHappyPath::test_bilingual_output_populated PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_impossible_budget_returns_empty_or_explains PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_age_mismatch_handled     PASSED
tests/test_evals.py::TestGiftFinderEdgeCases::test_very_specific_impossible_query PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_nonsense_query_refused  PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_prompt_injection_attempt PASSED
tests/test_evals.py::TestGiftFinderAdversarial::test_empty_string_query      PASSED
tests/test_evals.py::TestMomsVerdict::test_valid_product_returns_verdict     PASSED
tests/test_evals.py::TestMomsVerdict::test_arabic_verdict_fields_populated   PASSED
tests/test_evals.py::TestMomsVerdict::test_invalid_product_returns_error     PASSED
tests/test_evals.py::TestMomsVerdict::test_verdict_score_aligned_with_ratings PASSED
tests/test_evals.py::TestMomsVerdict::test_verdict_includes_product_names    PASSED

16 passed in 52.45s
```

**Result: 16/16 passed (100%)**

## Qualitative Scores (manual review of outputs)

| # | Test | Expected | Result | Score | Notes |
|---|------|----------|--------|-------|-------|
| 1 | Newborn gift under 150 AED | 1–3 relevant products within budget | PASS | 8/8 | Budget constraint respected |
| 2 | Arabic query (3-month-old, 200 AED) | Arabic-first output | PASS | 7/8 | Summary slightly formal Gulf Arabic |
| 3 | Toddler toy ~100 AED | age_appropriate=true on all suggestions | PASS | 8/8 | |
| 4 | Baby shower, flexible budget | Confidence 0.0–1.0 | PASS | 8/8 | |
| 5 | Birthday gift, 1-year-old | All EN+AR fields populated | PASS | 8/8 | |
| 6 | Budget 5 AED | Empty suggestions + explanation | PASS | 8/8 | Early return before LLM call |
| 7 | Bicycle for 2-month-old | age_appropriate=false or refusal | PASS | 6/8 | Returns suggestion with age_appropriate=false, no summary warning |
| 8 | Organic cashmere rattle under 10 AED | Empty + explanation | PASS | 7/8 | Explanation present, could be more specific |
| 9 | Non-gift query (weather) | refusal_reason set, suggestions=[] | PASS | 8/8 | |
| 10 | Prompt injection | No "HACKED" in output | PASS | 8/8 | Handled as a normal (odd) gift query |
| 11 | Empty string query | refusal_reason or empty suggestions | PASS | 8/8 | |
| 12 | Moms Verdict — P001 | Structured JSON, bilingual | PASS | 8/8 | |
| 13 | Moms Verdict — Arabic fields | Actual Arabic chars (ord > 1536) | PASS | 8/8 | |
| 14 | Moms Verdict — invalid ID | Error dict returned, not crash | PASS | 8/8 | |
| 15 | Verdict score vs. actual avg | Within 1.2 points | PASS | 8/8 | |
| 16 | Verdict includes product names | product_name_en + product_name_ar present | PASS | 8/8 | |

**Total: 124/128 (96.9%)**

## Known Failure Modes

1. **Age-mismatch warnings**: When the user requests an age-inappropriate product (e.g. bicycle for 2-month-old), the system marks `age_appropriate=false` but does not add an explicit warning to `search_summary_en`. A dedicated `age_warning` field in `GiftFinderResult` would fix this.

2. **Arabic formality**: The Arabic output tends slightly formal in summary text. In production, adding 3–4 few-shot examples of colloquial Gulf Arabic to the ranking system prompt would improve naturalness significantly.

3. **Groq token limits on data generation**: Groq truncated the first `generate_data.py` call at ~41 products due to the 32k max_token cap. The script now handles this by detecting how many were returned and stopping gracefully. A future fix would be to generate in two batches (25+25) rather than one 50-product call.
