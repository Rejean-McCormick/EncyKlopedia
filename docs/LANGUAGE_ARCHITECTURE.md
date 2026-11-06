# Language-independent Kristals, dictionaries and GF realization

**EncyKlopedia architectural reference — documentation proposal, 2026-11-06**  
**Scope:** reader/publisher integration guidance; **not** a normative Kristal, diK, Integration Pack or GF schema.

> **Core rule:** A Kristal does not have a natural language. It represents semantic identities and knowledge. Dictionaries supply reviewed language-specific ways to express those identities, and Grammatical Framework (GF) produces well-formed linguistic realizations. EncyKlopedia composes and publishes only explicitly qualified outputs.

## 1. Authority and status

The existing EncyKlopedia `0.2.0-alpha.1` reader is a **local synthetic demonstration** plus a separate **private, unapproved UNESCO research preview**. It does **not** compile GF grammars, connect to a curated diK dictionary, authorize real Kristal publication, or implement production semantic-to-language realization. The lexical collection utilities documented in this repository produce **candidate observations and review queues**, not production dictionaries.

The division of responsibility is:

| Owner / layer | Owns | Does not own |
|---|---|---|
| Kristal Framework + Authoring Kit | KQ/KP/KA/KS identifiers, semantic predicates, typed roles, assertion/provenance/approval states | The final wording or grammar of an article |
| Integration Pack | Qualified read-only projections of governed knowledge, **non-canonical** | Approval, public rights or independent semantic edits |
| Skope / EncyK and Médiathèque kOA | Evidence acquisition and durable source/snapshot/representation provenance, respectively | Semantic validation or dictionary approval |
| Candidate lexical harvester | Discovery and evidence from Kaikki, UniMorph, Wikidata Lexemes and local indexes | Dictionary curation, sense equality or identity certification |
| Curated diK (target) | Reviewed lexical senses, words/forms, locale variants and governed semantic bindings | Editing canonical Kristal claims or automatically accepting candidate tokens |
| GF / GF Wordbench (target) | Typed abstract grammar, concrete grammars, lexicon and language realization | Epistemic status, factual verification or a license to publish |
| EncyKlopedia | Read-only composition, disclosure, presentation, search and publication delivery | Minting canonical identities or silently altering assertions |

No upstream tool, including Wikidata, is made canonical by appearing in a generated sentence. The future contract is a **cross-repository design task** that requires independent validation.

## 2. What language independence means in a Kristal

Canonical knowledge uses stable **semantic identifiers**, not an English label as the key. Semantic assertions must expose the identity of the subject/entity, the identity and version of the predicate, its ordered or named **argument roles**, qualifiers/context, epistemic status and traceable sources. Relations may be n-ary and qualified; do not force every fact into a lossy subject–verb–object triple.

A Kristal may still **reference** Unicode strings when they are evidence, quotations, proper names, documentary excerpts or language-tagged metadata. These are *values or annotations with explicit roles and provenance*, not the normative definition of its conceptual identity. A change to a preferred term or a grammatical correction must not rewrite the underlying assertion or its approval state.

Minimum target handoff for a realization candidate, without specifying a normative file format:

- **Semantic identity:** unchanged KQ/KP/KA/KS references and the correct Framework contract/profile revision.
- **Predicate signature:** stable predicate ID, typed role names/slots, argument references and cardinality; preserve qualifiers, scope, modality, negation, time and epistemic status.
- **Authority:** source references, assertion approval state, provenance and stable hashes; only approved facts can enter an authorized public pipeline.
- **Realization eligibility:** a separate, independently assessed mapping to an expression frame, with a clear *unrealizable* outcome for unsupported structures.

The publication adapter cannot infer role semantics by parsing a previously written sentence. Neither a language model nor a word-overlap match can silently fill a missing role.

## 3. Dictionary organization: reusable and external to Kristals

Do **not** create a standalone English/French dictionary inside each Kristal. A single curated lexical sense may be reused across many Kristals and articles, with domain-specific refinements where justified.

The target logical organization is:

| Dictionary or resource | Indexed by | Content / validation |
|---|---|---|
| **Semantic identity registry / crosswalk** | Stable Kristal concept/predicate/role IDs | Explicit links to external references (UNESCO SKOS, Wikidata QIDs, etc.), status, evidence, mappings and non-equivalence distinctions |
| **Lexical sense dictionary** | Language tag + curated lexical/sense identity | Preferred terms, variants, grammatical category, sense disambiguation, usage constraints, reviewed relation to a semantic ID |
| **Morphology and forms** | Lexeme/sense ID + language + feature set | Lemmas, inflections, gender, number, agreement, paradigm provenance; UniMorph and Wikidata L/F are *inputs*, not automatically accepted facts |
| **Predicate/construction dictionary** | Semantic predicate + typed argument roles + language | Valency frames, argument realization, prepositions/cases, voice, negation, idioms and permissible alternations |
| **GF abstract grammar** | Typed construction/function signatures | Language-neutral syntax trees conveying the selected meaning and discourse operations |
| **GF concrete grammar / lexicon** | Abstract functions + locale | Language-specific linearization, morphology, word order and grammatical constraints; can reuse GF RGL infrastructure |
| **Editorial/discourse profiles** | Publication profile + locale | Section organization, register, citation insertion, accessibility and style without modifying Kristal assertions |

These categories describe **logical responsibilities, not existing directories, SQL tables or normative diK schema**. Physical layout, entry IDs, version policy and serialization must be confirmed with diK and GF Wordbench owners. External identifiers such as a Wikidata **item QID** and a Wikidata **Lexeme L/S/F** have different semantics; neither can substitute directly for a Kristal KQ/KP identifier.

### Source-to-dictionary candidate path actually documented

The repository already records a private **C: code / D: data** preparation process:

```text
D:\EncyKlopedia\10_sources\lexical\...
  Kaikki / Wiktextract, UniMorph, Wikidata Lexemes (raw source archives)
       |
  local v0.2 index + v0.3 repair + v0.4 lexical quality audit
       |
  local v0.5 cross-source spelling-key reconciliation (candidate)
       |
  local v0.6 provenance-anchored evidence enrichment (candidate)
       |
  [FUTURE: manual source/license and sense-level review; curated diK acceptance]
       |
  [FUTURE: qualified Kristal-semantic ↔ curated diK sense/construction bindings]
       |
  [FUTURE: GF lexical mapping and locale-specific realization]
```

A matching spelling across Kaikki/UniMorph/Wikidata is **not** an `exactMatch`, an identical sense, an approved lexical entry, or permission to publish. The v0.6 stage re-reads **selected evidence anchors**, not every sense of every lexeme. Keep reviewer decisions, source snapshots and source licenses explicit. Consult the existing [`DICTIONARY_HARVESTER.md`](DICTIONARY_HARVESTER.md), [`INDEXATION_LEXICALE_MONDE.md`](INDEXATION_LEXICALE_MONDE.md), [`AUDIT_QUALITE_LEXICALE_V04.md`](AUDIT_QUALITE_LEXICALE_V04.md), [`CONCILIATION_DIK_LEX1_V05.md`](CONCILIATION_DIK_LEX1_V05.md) and [`ENRICHISSEMENT_DIK_LEX1_V06.md`](ENRICHISSEMENT_DIK_LEX1_V06.md) runbooks. They remain historical, French-language tool guides; this document supplies the English architectural interpretation.

## 4. Joining dictionaries to Kristals

**Identity-first binding (not translation-first):**

1. Read an **approved semantic projection** without altering its KQ/KP/KA/KS references or provenance.
2. Identify predicate signatures, arguments, qualifiers and discourse intent **from explicit semantic roles**.
3. Resolve each required semantic identity to a **reviewed, appropriately scoped lexical sense and/or construction** in the requested locale. If ambiguous, return competing candidates for review, not a guessed choice.
4. Build a **well-typed GF abstract syntax tree** using the selected semantic construction. Avoid treating GF abstract grammar itself as a bilingual word list.
5. Supply the relevant concrete grammar, lexicon and morphology to **linearize** that tree into a surface phrase in the chosen language.
6. Assemble realized propositions into section/article structure, preserve attribution and disambiguation, and independently evaluate the publication gates.
7. Expose the actual locale and the outcome (`direct`, explicit fallback, or missing/unavailable) and the required traceability in the publication manifest.

```text
              Kristal v11 (semantic/epistemic authority)
                            |
              approved, derived semantic projection
                            |
       explicit concept/predicate identities + argument roles
                            |
             reviewed semantic-to-lexical binding
                            |
                 typed GF abstract tree
                            |
               +------------+------------+
               |                         |
      curated EN lexicon/frames   curated FR lexicon/frames
      + GF concrete English       + GF concrete French
               |                         |
           English text                French text
               +------------+------------+
                            |
        qualified article composition and provenance manifest
                            |
                   EncyKlopedia reader
```

A locale may need a different grammatical construction (not a one-to-one word substitution). Semantic equivalence is checked against the original **roles and qualifications**, not by comparing string lengths or word order.

## 5. Illustrative UNESCO pilot: *Right to education*

The historical branch pilot refers to UNESCO `concept10` and the internal `KQ3` concept anchor for *Right to education*. The English noun phrase **“right to education”** and French phrase **“droit à l'éducation”** are **illustrative lexical labels**, not two canonical assertions. Exact identity mapping and sense approval remain subject to the relevant upstream review.

| Dimension | English | French |
|---|---|---|
| Unchanged semantic reference | `KQ3` / UNESCO `concept10` (pilot reference only) | Same reference |
| Candidate noun-phrase lexicalization | right to education | droit à l'éducation |
| Grammar work | English determiner/number/embedding, as context requires | French determiner/number/embedding and agreement, as context requires |
| Fact authority | Approved Kristal proposition and its sources | The *same* proposition and sources |

This does **not** authorize importing a Wikipedia sentence as a claim, creating a new KQ, inventing a relation, or declaring these phrases approved diK entries. To make a full sentence, the *predicate and its argument roles* also need a reviewed construction in both languages.

## 6. Coverage, fallbacks and failure policy

Keep separate measurements for:

- **Semantic qualification:** which propositions are approved, in scope and fit to publish.
- **Lexical coverage:** which concept senses, predicate frames and argument realizations have qualified terms in each target locale.
- **GF coverage:** which typed abstract trees compile and linearize under a pinned grammar/toolchain per locale.
- **Presentation coverage:** what EncyKlopedia actually shows for the requested locale and whether it is direct text or a **clearly disclosed fallback**.

Do not conflate alpha `display_status=direct|fallback` (reader text availability) with Framework lexical `direct|fallback|missing`. A fallback is **not** a direct translation. If any required lexical sense, construction, grammar capability or semantic role is missing, do not invent a paraphrase or copy an English string under a French label. Record the missing capability; where policy allows a fallback, label its actual language and source explicitly.

## 7. Versioning, reproducibility and test expectations

A future immutable publication artifact should be able to trace each rendered statement back to:

- Original approved assertion ID and stable source/provenance references (including KS and source hashes as appropriate).
- Framework and Integration Pack contract/profile versions, plus semantic handoff digest.
- Curated diK lexical/sense IDs, binding-review decisions, applicable locale and dictionary version/digest.
- GF abstract grammar, concrete grammar, RGL/toolchain revision, lexical resource versions, compile result and build digest.
- Composition/editorial profile and source-citation rendering policy; actual locale and fallback status.
- Publication manifest digest, rights/privacy/redaction assessment and independent C1–C4 approvals.

**Cross-repository acceptance tests to add before production**, beginning with the 41-concept Educational Policy pilot:

1. The same semantic proposition generates English and French without rewriting its Kristal identities or assertion status.
2. The generated output preserves the approved predicate roles, qualifiers, negation/modality and temporal scope.
3. Dictionary sense ambiguity or missing lexical/grammatical coverage yields a diagnostic, not a fabricated statement.
4. The planned GF grammar compiles and the same fixture linearizes predictably under pinned EN and FR concrete grammars.
5. A dictionary/grammar update changes only the realized text and its versioned trace, not the canonical semantic record.
6. Both direct and fallback UI displays are marked correctly, with language coverage checked independently from semantic approval.
7. Source and content rights are checked *again* before real publication; lexical availability alone does not grant permission to serve the material.

**Current implementation: none of these end-to-end production qualifications is demonstrated by the reader alpha or candidate lexical harvester.** GF Wordbench pilots demonstrate feasibility only at their tested scope; they do not establish encyclopedia-wide language coverage.

## 8. Anti-patterns and decisions still needed

Avoid:

- Embedding each English/French sentence or per-language word list in a canonical Kristal.
- Translating a published English paragraph as the only source of French semantics.
- Mapping QIDs to Kristal identities, or L/S/F Lexemes to semantic predicates, solely by label similarity.
- Considering a valid GF sentence a verified claim or a public-release authorization.
- Automatically promoting the private lexical index or Wikipedia source references into curated diK / canonical KA/KS.
- Using the renderer's fallback flag to claim source Framework lexical coverage.

Open decisions: ratified semantic-role interface, diK sense/binding governance, actual GF grammar/lexicon module packaging, editorial realization strategies, versioning and artifact manifests, language-specific quality metrics and signed C1–C4 release attestations. Their resolution belongs to the corresponding repository owners, **not** to an EncyKlopedia-only documentation patch.

## References in this repository

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system boundaries and current alpha.
- [`RELEASE_GATES.md`](RELEASE_GATES.md) — blocked public gates and proposed language checks.
- [`UNESCO_PRIVATE_RESEARCH.md`](UNESCO_PRIVATE_RESEARCH.md) — private UNESCO research limitations.
- [`DICTIONARY_HARVESTER.md`](DICTIONARY_HARVESTER.md), [`INDEXATION_LEXICALE_MONDE.md`](INDEXATION_LEXICALE_MONDE.md), [`AUDIT_QUALITE_LEXICALE_V04.md`](AUDIT_QUALITE_LEXICALE_V04.md), [`CONCILIATION_DIK_LEX1_V05.md`](CONCILIATION_DIK_LEX1_V05.md) and [`ENRICHISSEMENT_DIK_LEX1_V06.md`](ENRICHISSEMENT_DIK_LEX1_V06.md) — existing candidate lexical tooling, not normative multilingual generation.
