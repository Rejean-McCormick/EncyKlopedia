# Interaction Kernel availability in EncyKlopedia v0.9

The earlier v0.8 package only had kOA integration references. v0.9 additionally includes the user-supplied Interaction-Kernel snapshot under:

`00_system/integrations/Interaction-Kernel/`

The snapshot contains:

- profile/contracts schemas;
- Python and TypeScript runtimes;
- TCK vectors;
- Da'at adapter/lock files;
- Kristal pin metadata;
- documentation and ADRs.

The original supplied archive is retained under `10_sources/components/interaction-kernel/originals/`.

## Authority

The bundled directory is a local reference/integration snapshot. The upstream Interaction-Kernel repository remains authoritative. EncyKlopedia does not silently alter IK contracts.

`kristal.build.request/1.0.0` declares Konnaxion/Orgo source systems and Da'at as the target. Therefore EncyKlopedia still prepares source-owned evidence/handoffs; it does not claim to emit a conforming direct IK build request as an EncyKlopedia source system.
