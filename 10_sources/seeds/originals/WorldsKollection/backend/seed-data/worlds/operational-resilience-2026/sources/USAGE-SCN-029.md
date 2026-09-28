---
id: "SCN-029"
title: "Replay the Cyberattack Without Inventing Hindsight."
locale: "en"
problem_family: "action_learning_loops"
problem_family_label: "Action & learning loops break"
scenario_type: "canonical_archetype"
hook: "A post-mortem is misleading if it judges yesterday’s decisions using information that only became available today."
failure_mechanisms:
  - "hindsight_bias"
  - "context_loss"
  - "memory_failure"
  - "blame_distortion"
scale: "organization→network"
urgency: "high"
stakes:
  - "security"
  - "money"
  - "essential_service"
coordination_gap: "high"
domains:
  - "cybersecurity"
  - "learning"
koali_patterns:
  - "Turn action into a lesson"
  - "Reconstruct context and provenance"
  - "See patterns over time"
  - "Maintain a changing shared situation"
koali_components:
  - "Orgo"
  - "Kristal"
real_case_ids:
  - "CHANGE_HEALTH"
  - "COLUMBIA"
evidence_status: "scenario_archetype_with_documented_parallels"
koali_runtime_status: "COMPOSED · runtime UNVERIFIED"
---

# Replay the Cyberattack Without Inventing Hindsight.

> A post-mortem is misleading if it judges yesterday’s decisions using information that only became available today.

## The problem

After an incident, the full attack path looks obvious. During the incident it was not. If the organization reconstructs only the final truth, it cannot distinguish reasonable decisions under uncertainty from avoidable mistakes.

## What breaks

- Hindsight Bias
- Context Loss
- Memory Failure
- Blame Distortion

## Who holds part of the picture

- security
- IT
- operations
- leadership

## With Koali

Koali preserves the time-indexed incident state. A replay can show exactly which facts, hypotheses and options were available before each decision, then compare them with what was learned later.

## Human authority

Authorized humans and institutions retain their existing legal, professional and democratic authority. Koali structures knowledge, coordination and traceability; it does not take sovereign or professional decisions.

## What success looks like

- The relevant state remains visible across handoffs and time.
- Responsibilities, unresolved questions and escalation paths are explicit.
- The outcome produces reusable memory for the next comparable case.

## Real-world parallels

### Change Healthcare Cybersecurity Incident — U.S. HHS

HHS described the 2024 cyberattack as having unprecedented nationwide impact on patients and health-care providers.

**Relation to scenario:** `STRONG ANALOGUE`  
**Source:** https://www.hhs.gov/hipaa/for-professionals/special-topics/change-healthcare-cybersecurity-incident-frequently-asked-questions/index.html

### Columbia Accident Investigation Board Report

The CAIB found ineffective communication, three independent imagery requests, reliance on informal channels and inadequate discussion of assumptions and uncertainty.

**Relation to scenario:** `STRONG ANALOGUE`  
**Source:** https://history2.nasa.gov/columbia/reports/CAIBreportv1.pdf

## Boundary

The documented cases illustrate analogous failure mechanisms. They do not establish that Koali would have prevented the event or guaranteed a different outcome.

## Koali loop

`signals → shared meaning → evidence → choice → responsibility → action → verification → memory → better knowledge`
