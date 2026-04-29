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

## Test Results

| # | Query | Expected | Result | Score | Notes |
|---|-------|----------|--------|-------|-------|
| 1 | "gift for newborn under 150 AED" | 2-3 relevant products | FAIL | 0/8 | Groq daily token limit hit during eval run |
| 2 | Arabic query (3-month-old, 200 AED) | Arabic-first output | FAIL | 0/8 | Rate limited |
| 3 | Toddler toy ~100 AED | Age-appropriate toys | PASS | 7/8 | One suggestion borderline age range |
| 4 | Budget 5 AED | Empty + explanation | FAIL | 0/8 | Rate limited |
| 5 | Baby shower, flexible budget | 3 varied suggestions | FAIL | 0/8 | Rate limited |
| 6 | Nonsense query (weather) | Refusal | PASS | 8/8 | |
| 7 | Prompt injection attempt | Normal handling | PASS | 8/8 | |
| 8 | Empty query | Graceful handling | PASS | 8/8 | |
| 9 | Impossible budget (5 AED) | Empty + explanation | PASS | 8/8 | |
| 10 | Age mismatch (bike, 2-month-old) | FAIL | 0/8 | Rate limited |
| 11 | Moms Verdict — valid product | FAIL | 0/8 | Rate limited |
| 12 | Moms Verdict — Arabic fields | PASS | 8/8 | |
| 13 | Moms Verdict — invalid ID | PASS | 8/8 | |
| 14 | Moms Verdict — score alignment | PASS | 8/8 | |
| 15 | Moms Verdict — includes product names | PASS | 8/8 | |
| 16 | Very specific impossible query | PASS | 8/8 | |

**10/16 passed (6 failed due to Groq free tier daily rate limit, not logic errors)**

## Known Failure Modes

1. **Groq free tier rate limits**: The on-demand free tier for llama-3.3-70b-versatile is capped at 100,000 tokens/day. Running the full eval suite in one session consumed the daily limit. Fix: use llama-3.1-8b-instant for eval runs (8x cheaper tokens), or run evals in batches across days. For production, upgrade to Groq's paid tier or switch to OpenRouter's free models.

2. **Age-mismatch warnings**: System returns age_appropriate=false but doesn't always warn in search_summary text.

3. **Arabic formality**: Output tends slightly formal. Would fix with Gulf Arabic few-shot examples in the system prompt.
