# Konnaxion reference adapter

This adapter maps IK Profiles to the existing Konnaxion bridge boundary without replacing Konnaxion-owned domain state.

- `accountability.impact.publish` maps to the existing `orgo_bridge_publish` request shape.
- `governance.decision.execute` is emitted from an immutable `DecisionRecord` view through an injected durable emission port.
- The adapter itself does not create Orgo Case/Task records.
