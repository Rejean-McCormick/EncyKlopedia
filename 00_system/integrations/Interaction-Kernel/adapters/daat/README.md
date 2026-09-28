# Da’at reference adapter

Da’at is the baseline IK participant in front of Kristal. It authenticates/admits IK, applies a versioned mapping profile, invokes pinned Kristal-native contracts, validates outputs, then returns Receipts/Events carrying Kristal-owned ArtifactRefs.

Da’at consumes source-owned snapshots/ExportManifests. It does not own or directly mutate Konnaxion/Orgo operational databases, and it does not turn IK into an artifact store. Cross-boundary completion is asynchronous and reference-based.
