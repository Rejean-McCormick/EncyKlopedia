# Interaction Kernel snapshot inside EncyKlopedia

This directory is a local snapshot supplied to EncyKlopedia for contract validation and integration testing.

- Upstream Interaction-Kernel remains the authority.
- EncyKlopedia must not silently fork or alter IK profiles.
- `kristal.build.request/1.0.0` declares Konnaxion/Orgo source systems and Da'at as target; EncyKlopedia therefore prepares source evidence/handoffs and does not pretend to be a conforming direct IK source for that profile.
- The bundled runtime/contracts/TCK can be used to validate future adapters.

Original uploaded snapshot is retained under `10_sources/components/interaction-kernel/originals/` for provenance.
