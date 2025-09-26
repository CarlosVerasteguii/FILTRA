# External APIs

### OpenRouter API
- **Purpose:** Obtain LLM-powered scoring narrative and qualitative analysis.
- **Documentation:** https://openrouter.ai
- **Base URL(s):** https://openrouter.ai/api/v1
- **Authentication:** Bearer token via `Authorization: Bearer ${OPENROUTER_API_KEY}` with required `HTTP-Referer` and `X-Title` headers.
- **Rate Limits:** Default ~60 req/min depending on plan; client enforces exponential backoff via `tenacity`.

**Key Endpoints Used:**
- `POST /api/v1/chat/completions` - Submit combined resume/JD prompt and receive analysis payload.

**Integration Notes:** Deterministic parameters (`temperature`, `seed`, `model`) controlled by CLI options; degrade gracefully with cached/mock responses on failures; log minimal metadata to honor privacy constraints; warm-up command performs dry-run request to verify connectivity.

_Only external API integration required; HuggingFace models are cached locally via transformers._