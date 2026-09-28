# Data Provenance

A result is reproducible only when the exact input and transformation path can be reconstructed.

## Minimum provenance chain
`result → experiment → protocol version → dataset version → project`

For transformations, record:
- source dataset version;
- transformation order;
- parameters and code/config identifier;
- exclusions and reason codes;
- output dataset version;
- person or process that created the revision.

## Example
EVID-001 resolves to RES-001 → EXP-001 → PROT-001:v3 → DATA-001:v1 → PRJ-001.

A later harmonization must create a new version. It must never silently replace DATA-001:v1 or PROT-001:v3.
