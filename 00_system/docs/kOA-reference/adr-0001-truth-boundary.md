# ADR-0001: Truth Boundary (historical)

**Status:** Superseded by ADR-0008 on 2026-09-16  
**Historical date:** 2026-02-27

This ADR captured the former Kristal v4-oriented model in which validation gated compilation and one canonical Exchange represented the truth boundary.

It is retained for decision history only. It is **not** the active architecture for Kristal v5.

Active rules are defined by:

- `adr-0008-kristal-v5-epistemic-lifecycle.md`
- `../..//40-integration/kristal-v5/`

The retained historical assumptions that are no longer normative include:

- universal `Claim-IR → Resolved Claim-IR → validation → compile` ordering;
- universal “no compile on fail”;
- a single “canonical truth” status;
- treating validation, reference status and publication as one boundary.
