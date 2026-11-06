# Kypson RFQ Parser — Engineering Notes

### 1. Approach
The parser uses a modular, deterministic pipeline built entirely with Python standard libraries (`re`):
- **Normalization:** Converts Indian number words (`hazaar`, `lac`, `lakh`, `k`) and comma notations (`1,50,000`) into standardized digits.
- **Trap Filtering:** Uses negative lookaheads and keyword patterns to strip specification traps (fill weights like `50 kg bag` and capacity specs like `1000 kg capacity`) as well as GSM/micron figures from a working copy before evaluating quantity.
- **Priority Categorization:** Checks categories in strict hierarchical order (e.g., prioritizing `film` and `bopp` over general `woven_sack` or `corrugated_box`) to resolve multi-keyword conflicts.
- **Hybrid Location Extraction:** Combines an O(1) set of known Indian industrial hubs, preposition patterns (`to`, `for`, `in`), trailing comma patterns, and capitalized word boundary fallbacks.

### 2. Score on `my_tests.jsonl`
- **Total Test Examples:** 42
- **Runtime:** < 0.01 seconds
- **Category:** 42/42 (100.0%)
- **Quantity:** 42/42 (100.0%)
- **Unit:** 42/42 (100.0%)
- **GSM:** 42/42 (100.0%)
- **Micron:** 42/42 (100.0%)
- **Location:** 42/42 (100.0%)
- **ALL FIELDS:** 42/42 (100.0%)

### 3. Three Messages the Parser Gets Wrong (and Why)
1. **Fully Written Word Numbers:**
   - *Message:* `"ek lakh bopp bags chahiye nagpur"`
   - *Why it fails:* The regex expects digits (`\d+`) before multipliers (e.g., `"1 lakh"`). Pure Hindi/English number words without digits (`ek`, `do`, `five thousand`) are not parsed.
2. **Multi-Item / Multi-Product RFQs:**
   - *Message:* `"need 500 pcs bopp bags and 1000 boxes for pune"`
   - *Why it fails:* The specification requires returning a single flat dictionary with one category and quantity. The parser will overwrite or collapse multiple line items into one.
3. **Unseen Lowercase Cities without Prepositions:**
   - *Message:* `"urgent requirement 5000 pouches dispatch moradabad"`
   - *Why it fails:* If an unseen city is written entirely in lowercase without an explicit preposition (`to`, `for`, `in`), the parser cannot distinguish the city name from conversational noise or product attributes.

### 4. What to Do Differently with 1,000 Real Labelled Examples
- **Transition from Heuristics to Named Entity Recognition (NER):** Fine-tune a lightweight local transformer (e.g., `distilbert-base-multilingual-cased` or `DeBERTa-v3-small`) for token classification to extract `B-QTY`, `B-UNIT`, `B-GSM`, `B-MICRON`, and `B-LOC`. 
- **Sequence Context:** A trained model naturally learns the syntactic difference between bag size (`50 kg bag`) and order volume (`500 pcs`) based on sentence context rather than rigid regex lookaheads.
- **Typo Tolerance:** Subword tokenization (Byte-Pair Encoding) handles noisy Hinglish misspellings far better than manual regex branches.
- **Intent Classifier for Category:** Train a small classification head on top of embeddings to classify the 7 packaging categories probabilistically.

### 5. Measuring Performance in Production
- **Human-in-the-Loop Override Rate:** Monitor how often internal operations or buyers edit pre-filled fields in the UI before broadcasting the RFQ to suppliers. An edit rate under 5% indicates high practical accuracy.
- **Supplier Rejection Rate:** Track supplier declines attributed to malformed specs (e.g., invalid unit or missing GSM).
- **Fallback / Low-Confidence Telemetry:** Log messages where quantity, category, or location returns `None` to an active review queue for continuous test suite expansion and periodic retraining.

### 6. Tools Used
- Developed in VS Code using Python 3.10 and tested with `score.py`.
- Used Gemini as an AI brainstorming and code review assistant to analyze edge-case regular expressions and generate diverse test scenarios; all final regex pipelines, cleaning rules, and edge-case verifications were written, debugged, and verified manually.