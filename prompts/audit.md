You are conducting a comprehensive technical and correctness audit of an MCP (Model Context
Protocol) server that connects LLMs (Claude, ChatGPT, Gemini) to an Oracle CPQ Cloud environment.
This server will answer real business questions about live quotes, pricing, products, and
configuration — accuracy and hallucination-prevention are the highest priority, above general
code quality.

Audit the entire codebase in this project and produce a structured report. Do not summarize
generically — cite specific files, functions, and line numbers for every finding. For every issue,
state: (a) what's wrong, (b) why it matters specifically for an LLM-facing CPQ tool, (c) a concrete
fix, (d) priority (P0/P1/P2/P3).

Use this exact structure for your output:

═══════════════════════════════════════
1. EXECUTIVE SUMMARY
═══════════════════════════════════════
- Overall assessment (2-3 sentences)
- Top 5 risks ranked by severity
- Is this safe to connect to a production CPQ environment today? Yes/No + why

═══════════════════════════════════════
2. MCP PROTOCOL CORRECTNESS
═══════════════════════════════════════
Check and report on:
- Tool definitions: are input schemas strict (required fields, enums, types, min/max, format
  constraints) or loosely typed with `any`/optional-everything?
- Tool descriptions: are they precise enough that an LLM won't misuse them, or vague enough to
  invite guessing? Flag any tool description that doesn't explicitly state what the tool does NOT
  do, what happens on empty results, and what units/formats values are returned in.
- Are tool names and descriptions disambiguated from each other (no overlapping purpose that
  would make an LLM pick the wrong one)?
- Resource vs Tool usage — is static/cacheable data (catalog, attribute definitions) modeled as
  Resources where appropriate, or is everything a Tool call?
- Transport implementation (stdio / Streamable HTTP) — correctness, session handling, error
  propagation back to the client per MCP spec
- Are tool responses returned as structured JSON with explicit schemas, or as loosely formatted
  strings the LLM has to parse/guess at?
- Pagination handling for list-type CPQ endpoints — does the server truncate silently, or does it
  communicate truncation to the LLM explicitly?

═══════════════════════════════════════
3. HALLUCINATION & ACCURACY RISK AUDIT (HIGHEST PRIORITY)
═══════════════════════════════════════
This is the most important section. For an LLM answering business-critical CPQ questions
(pricing, quote status, approvals), go through every tool and flag:

a) SILENT FAILURE MODES
   - Does any code path return an empty/null result that could be misread by the LLM as
     "confirmed zero/none" instead of "lookup failed"?
   - Are CPQ API errors (4xx/5xx, timeouts, auth failures) caught and surfaced as explicit
     structured errors to the LLM, or do they get swallowed, logged only server-side, or
     returned as ambiguous empty payloads?
   - Are partial results (e.g., pagination cut short, one sub-call in a multi-call tool failed)
     clearly labeled as partial rather than presented as complete?

b) DATA FIDELITY
   - Are numeric values (prices, quantities, discounts) passed through as raw numbers/strings
     from CPQ with correct precision, or is there any rounding/formatting/unit conversion in the
     server code that could introduce drift from source-of-truth?
   - Are currency, date, and locale formats preserved explicitly (not left for the LLM to infer)?
   - Is there any transformation logic (mapping CPQ field codes to friendly names, computing
     derived values) that could be wrong or go stale if CPQ config changes? Flag every place the
     server "interprets" CPQ data rather than passing it through.
   - Environment ambiguity: if the server (or a future multi-env version) can query multiple CPQ
     environments (dev/test/prod), is the environment/instance ALWAYS explicit in both the
     request and the response, so the LLM can never present dev/test data as production data (or
     vice versa) without saying so?

c) PROMPT-LEVEL GROUNDING
   - Do tool descriptions instruct the LLM to only state facts returned by tool calls, and to
     explicitly say "not found" / "unable to retrieve" rather than inferring or filling gaps?
   - Is there a system-level instruction (in the MCP server's tool descriptions or a prompts/
     resource) telling the LLM not to perform pricing math itself when a pricing tool exists, not
     to guess CPQ field meanings, and not to answer from general Oracle CPQ knowledge instead of
     live tool data?
   - Are timestamps/"as of" markers included in every data-returning tool response, so the LLM
     can correctly caveat freshness instead of implying real-time certainty?

d) IDENTIFIER SAFETY
   - Are quote IDs, product IDs, etc. validated for format before being sent to CPQ? Could a
     malformed or LLM-hallucinated ID silently match the wrong record, or does the server
     correctly error out?
   - Any risk of the LLM fabricating a plausible-looking ID and the server returning a
     "closest match" instead of a hard not-found?

e) TOOL-CALL DISCIPLINE
   - Are there any tools whose names/descriptions might tempt the LLM to answer from memory
     instead of calling them (e.g., a generic "explain CPQ concept" tool that overlaps with the
     LLM's own training knowledge)? Flag ambiguity between "live data tools" and "general
     knowledge" — these must be clearly separated.

Deliverable for this section: a table of every tool, its hallucination risk level (High/Med/Low),
and the specific fix needed.

═══════════════════════════════════════
4. SECURITY & AUTH AUDIT
═══════════════════════════════════════
- OAuth/credential handling: are CPQ client secrets, tokens, or API keys ever exposed to the LLM
  client, logged in plaintext, or committed in code/config?
- Token lifecycle: refresh handling, expiry, retry-on-401 logic
- Is the MCP server itself authenticated (API key, OAuth) if exposed over HTTP, given it may be
  reachable outside localhost (e.g., via Tailscale Funnel)?
- Input sanitization: any risk of injection into CPQ API calls (query params, BML-related calls)
  from LLM-supplied arguments?
- Least privilege: does the CPQ service account/token used have write access where only read
  access is needed? Flag any tool that could mutate CPQ data (create/update/delete) and confirm
  it has extra guardrails (explicit confirmation flow, restricted scope) vs read-only tools.
- Multi-tenant/multi-environment credential isolation — could a bug cause a dev-environment
  token to be used against a prod call or vice versa?
- Rate limiting / abuse protection against the CPQ backend (could a chatty LLM loop hammer CPQ
  with repeated calls?)

═══════════════════════════════════════
5. ERROR HANDLING & RESILIENCE
═══════════════════════════════════════
- Consistent error shape across all tools (structured, LLM-parseable, not raw stack traces)
- Timeout handling on CPQ REST calls
- Retry logic (with backoff) for transient CPQ failures vs. fail-fast for real errors
- Graceful degradation if CPQ is down/unreachable — does the server say so clearly?
- Logging: enough server-side detail for debugging without leaking secrets into logs

═══════════════════════════════════════
6. CODE QUALITY & MAINTAINABILITY
═══════════════════════════════════════
- Type safety (TS types/interfaces for CPQ payloads — are they modeled explicitly or is `any`
  used liberally?)
- Separation of concerns: CPQ API client vs. MCP tool layer vs. transport layer
- Config management: environment-specific values (base URLs, client IDs) — hardcoded vs.
  externalized (env vars/config files)?
- Duplication across tool implementations that could be refactored into shared helpers
  (especially CPQ auth/token logic, response shaping)
- Test coverage: unit tests for tool logic, integration tests against a CPQ sandbox/mocked
  responses

═══════════════════════════════════════
7. OBSERVABILITY
═══════════════════════════════════════
- Are tool calls logged with enough context to reconstruct "what did the LLM ask CPQ and what
  did it get back" for later debugging of a wrong answer?
- Any metrics/health-check surface (relevant since this may sit behind Uptime Kuma)?

═══════════════════════════════════════
8. PRIORITIZED ACTION PLAN
═══════════════════════════════════════
Consolidate every finding from sections 2-7 into a single prioritized list:

P0 (blocks safe use — fix before connecting to any real environment):
P1 (fix before broader/production use):
P2 (should fix soon, not blocking):
P3 (nice to have / polish):

For each item: file/location, one-line description, effort estimate (S/M/L).

═══════════════════════════════════════
9. GENERAL IMPROVEMENT IDEAS (beyond fixing bugs)
═══════════════════════════════════════
Suggest forward-looking improvements such as:
- Caching strategy for slow-changing CPQ data (catalog/config) to reduce latency and API load
- Whether any tools should be split/merged for clearer LLM tool-selection
- Response shaping improvements (e.g., pre-computed summaries alongside raw data)
- Whether a "confidence/freshness" field on responses would help downstream LLMs caveat answers
- Any multi-environment (dev/test/prod) architecture improvements
- Whether adding an eval/regression test suite (fixed set of Q&A pairs against a CPQ sandbox,
  checked against expected values) would help catch accuracy regressions over time

Be specific and reference this codebase throughout — do not give generic MCP best-practice
advice unless you tie it to an actual gap you found in this code.