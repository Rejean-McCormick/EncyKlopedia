# Standalone Architecture

**Spek is an independent local-first publishing product**, not a Konstellation plug-in. It needs only Python and local article/realization/layout files. Optional connectors can import data from separate Kristals, Konstellation or other source systems.

Knowledge authority remains upstream. Spek accepts explicitly mapped reader-visible exports, composes typed layouts, and produces derived publications. It never commits to a Kristal state or grants publication approval.

```text
Kristal A  ─┐
Kristal B  ─┼─→ approved export / Spek native input ─┐
Other APIs ─┘                                        │
Konstellation → ResultSet 0.2 → Spek bridge adapter ─┤
                                                     ↓
SemantiK Architect ───────┐            Spek Document Model
                          ├──→ short expressions → layouts → HTML/PDF/LaTeX
Preconstructed AI text ──┘            + Source Explorer
```

**One channel per phrase:** `semantik_architect` OR `ai_preconstructed`; legacy v0.3 fixtures remain labeled `legacy`. A static publication can carry provenance, but cannot automatically enforce a remote reader policy.

See [Source Connectors](Source-Connectors) and [Language Channels](Language-Channels). More precise source code: `docs/STANDALONE_AND_CONNECTORS.md`.
