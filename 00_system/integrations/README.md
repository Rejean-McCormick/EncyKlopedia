# External integrations

EncyK `0.12.0` does not vendor upstream Integration Kernel, Kristal/Kristall, Médiathèque or Kompiler repositories.

Current compatibility baseline:

| System | Baseline | EncyK relationship |
|---|---|---|
| Médiathèque kOA | `0.2.0` | persistent source authority; canonical EncyK handoff target |
| source catalog | `koa.source-catalog/2.0.0` | consumer contract for source/snapshot/representation ownership |
| Interaction Kernel | `2.0.0-dev.2` | optional downstream transport/admission after source ownership |
| DaaT | `DaaT` / `daat` | optional IK↔Kristal contract-mapping boundary; not an EncyK stage |
| Kristal | `kristal_state/6.0` | portable epistemic artifact contract; external to EncyK |
| Kristal/Kristall | `7.0.0-draft.3.2` | semantic identity and meta-orchestration authority |
| Kompiler | `0.5.0` | read-only context compiler; not an EncyK stage |

Upstream repositories remain authoritative for their own contracts. EncyK pins only the compatibility metadata it needs in `00_system/contracts/knowledge-baseline.json`.
