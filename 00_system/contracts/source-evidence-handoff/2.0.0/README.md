# Source Evidence Handoff 2.0.0

Canonical **EncyK → Médiathèque kOA** handoff.

EncyK owns discovery, acquisition, scope selection and lossless extraction. The handoff transfers a content-addressed evidence bundle to the persistent source authority. After acceptance, Médiathèque owns durable source bytes/snapshots/representations and may issue stable `koa-media://` locators.

This contract intentionally does **not** contain a Kristal Referent Registry, DaaT mapping, KQ/KP/KA/KS identity, Mesh/axis data, or crystallization output.

Handoff compatibility:

- EncyK: `0.12.0`
- Médiathèque kOA: `>= 0.2.0`
- source catalog: `koa.source-catalog/2.0.0`

Downstream IK/DaaT/Kristal/Kristall/Kompiler versions are deliberately **not encoded in this source-storage contract**. Their current compatibility baseline is documented separately in `00_system/contracts/knowledge-baseline.json`.
