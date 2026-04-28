# Tradeoffs and Design Decisions

## Why this problem

Chose Gift Finder + Moms Verdict because:
- Real business value: gift discovery is a top use case for baby e-commerce platforms
- Covers the required AI complexity: RAG + structured output + bilingual + evals
- Honest scope for 5 hours: two tight features done well > one sprawling feature half-done

## Problems I rejected

**Returns Intelligence**: Predicting high-risk returns requires historical order data — thousands of rows with features like "did the customer view similar products before buying?", "was there a size mismatch?" This is a supervised classification problem. Without real historical data, any demo would be illustrative, not evaluable. Rejected.

**Customer Service Email Triage**: Strong problem, but real value comes from integration with Mumzworld's actual ticket system. A standalone prototype would just be "paste an email here" — not meaningfully different from a ChatGPT wrapper. Also harder to eval rigorously without real email samples. Rejected.

**WhatsApp Personal Shopper**: Great product idea, real-time enough to be impressive. Rejected because building a WhatsApp integration in 5 hours would mean most time goes to infra (Twilio, webhooks) not AI. The AI part is essentially the same as Gift Finder.

## Architecture choices

**ChromaDB over Pinecone/Weaviate**: No signup needed, runs locally, persists to disk. For a demo, this is strictly better — reviewer can clone and run without managing credentials.

**Two-model approach (Flash + Pro)**: Intent extraction doesn't need high-quality output — it just needs valid JSON with the right fields. Flash is cheaper and fast enough. Pro is used only for user-facing reasoning where quality matters.

**Synthetic data via Gemini**: The brief says "bring or generate your own data." I used Gemini 2.5 Pro to generate 60 products with Arabic names and reviews. This is legitimate — what matters is whether the AI pipeline handles the data well, not whether the products are real.

## What I'd build next

- A confidence threshold that triggers a human fallback ("I'm not sure about this — want to chat with our team?")
- Age-progression recommendations: track a child's age and proactively surface what they need next month
- Arabic dialect detection: Gulf Arabic vs. Egyptian Arabic vs. Levantine — different tone for each
- A real eval harness using Gemini as a judge to automatically grade Arabic naturalness on every PR
