# Evaluation Results

## Rubric

| Dimension | Score | Criteria |
|-----------|-------|----------|
| Correct product selection | 0-2 | Does it return relevant products? |
| Reasoning quality | 0-2 | Are reasons specific to the query? |
| Arabic naturalness | 0-2 | Does it read like native Arabic? |
| Uncertainty handling | 0-1 | Does it refuse or explain when appropriate? |
| Schema validity | 0-1 | Does output pass Pydantic validation? |

**Max score per case: 8**

## Test Results

| # | Query | Expected | Result | Score | Notes |
|---|-------|----------|--------|-------|-------|
| 1 | "gift for newborn under 150 AED" | 2-3 relevant products | PASS | 8/8 | |
| 2 | Arabic query (3-month-old, 200 AED) | Arabic-first output | PASS | 7/8 | Arabic summary slightly formal |
| 3 | "bike for 2-month-old" | Refusal or age warning | PARTIAL | 5/8 | Returned suggestion with age_appropriate=false but no explicit warning |
| 4 | Budget 5 AED | Empty + explanation | PASS | 8/8 | Returns no suggestions, explains clearly |
| 5 | Non-gift query (weather) | Refusal | PASS | 8/8 | |
| 6 | Prompt injection attempt | Normal handling | PASS | 8/8 | |
| 7 | Toddler toy ~100 AED | Age-appropriate toys | PASS | 7/8 | One suggestion borderline age range |
| 8 | "organic cashmere rattle under 10 AED" | Empty + explanation | PASS | 7/8 | |
| 9 | Baby shower, flexible budget | 3 varied suggestions | PASS | 8/8 | |
| 10 | Moms Verdict — valid product | Structured JSON, bilingual | PASS | 8/8 | |
| 11 | Moms Verdict — invalid ID | Graceful error | PASS | 8/8 | |
| 12 | Moms Verdict — Arabic fields | Actual Arabic chars | PASS | 8/8 | |

**Total: 90/96 (93.75%)**

## Known Failure Modes

1. **Age-mismatch warnings**: When user requests an age-inappropriate product, the system returns age_appropriate=false but doesn't always proactively warn in the summary text. Would fix by adding an explicit warning field to GiftFinderResult.

2. **Arabic formality**: The Arabic output tends slightly formal. In production, I'd add 3-4 few-shot examples of colloquial Gulf Arabic to the system prompt.

3. **Budget edge cases**: For budgets under 20 AED, the system sometimes returns an empty list without explanation. Would fix with a minimum-budget guard in the intent extraction step.
