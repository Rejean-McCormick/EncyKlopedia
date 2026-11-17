# Spek 0.4: Standalone Core and Source Connectors

**Spek is an autonomous publishing engine.** Kristal and Konstellation are possible sources, not mandatory runtimes or parent applications. Existing `examples/article.json` compiles without any connector, online service, or source-system installation. A Spek installation can contain many independent publications, backed by different reader-policy-scoped exports.

## Trust boundaries

1. A source system owns its knowledge, source identity, and reader policy. It exports a **derived, reader-visible selection**.
2. A **Spek connector** captures or reads an export and applies an operator-reviewed mapping. Every semantic assertion binding is pinned to a hash of the exported assertion payload. Exported source IDs must be visible within the selected context.
3. A **Spek article source** remains a derivative. It never claims to be the upstream state or to revalidate upstream cryptographic commitments.
4. An independent language channel supplies short expressions, either **SemantiK Architect** or **AI-preconstructed sentences**. They are alternatives *per phrase*, never a combined claim of provenance.
5. Spek validates slots and builds HTML/PDF/LaTeX/document.json. Approval to publish is a separate, external decision.

**Important:** An assertion payload hash is only a consistency pin. It does not prove scientific truth, authorization, correspondence between the supplied expression and the assertion, signature validity, or Kristal JCS commitments. The mapping and phrase equivalence must be reviewed by humans or by an independently qualified system.

## Connector surface

| Adapter | Input | Scope checks | Notes |
|---|---|---|---|
| Native file | `kristal.layout-article-source/0.1` | Spek typed-contract validation | Works offline, no external dependency |
| `konstellation` | Konstellation `ResultSet 0.2` captured from `/api/query` | Pinned `datasetRef`, `readerPolicyRef`; `evaluation=complete`, no pagination; `witnessesComplete`; assertion payload SHA-256 | Does not infer slot kinds, scientific status, or translations |
| `exchange` | `spek.exchange/0.1` | Pinned dataset/policy; `authorized_local_preview`, `complete=true`; hashes for assertions **and** source payloads | Any other Kristal-derived system or third-party tool can export this stable interchange format |

A bridge mapping file (`spek.bridge-map/0.1`) declares an approved Spek template, source assertion/evidence bindings and an optional `navigation_template` such as `https://example.org/explore?focus={id}`. The URL pattern is *operator-defined*, not an assertion about Konstellation's actual routes. HTTP links are accepted only for local loopback; public links must use HTTPS.

The current adapters read **exports**. They do not write back to source systems, create permissions, contact the canonical Kristal API, or rewrite the canonical state. A network capture command is available as an explicit, optional step for Konstellation only.

## Konstellation — local, reversible demonstration

From the root of this repository, using the **synthetic** ResultSet fixture:

```powershell
python -m spek bridge-import --adapter konstellation --input examples/bridge/konstellation-resultset.json --template examples/article.json --mapping examples/bridge/konstellation-mapping.json --out bridge-article.json
python -m spek check --source bridge-article.json
python -m spek build --source bridge-article.json --out dist-bridge --formats html,pdf,tex
python -m spek verify-site dist-bridge
python -m http.server 8000 --directory dist-bridge
```

Open `http://localhost:8000/en/`, choose a card and **Explore source**. The panel shows the opaque external reference and offers an operator-configured **View in source system** link. Replace the demo URL in the mapping with a real, reviewed Konstellation deep-link template before deployment. No live server is contacted by these commands.

### Optional live ResultSet capture

Use an actual Konstellation QuerySpec JSON, as documented by that server, with its Reader Policy context. Capture the **complete** result before mapping it:

```powershell
$env:KONSTELLATION_TOKEN = "<your-local-token>"
python -m spek bridge-fetch-konstellation --base-url https://your-konstellation.example --query-file query.json --token-env KONSTELLATION_TOKEN --out resultset.json
python -m spek bridge-import --adapter konstellation --input resultset.json --template examples/article.json --mapping your-reviewed-mapping.json --out article.json
```

The capture uses only `POST /api/query`, forwards a bearer token only on the requested origin (no redirects), enforces size/time limits, and requires an exhaustive ResultSet. It has **not been tested against your running Konstellation server**. The local synthetic fixture was validated against the supplied upstream JSON Schema.

Never commit real bearer tokens or private result sets to GitHub. Scope checks occur on the export; Spek cannot independently recreate or enforce the source server's reader authorization for static HTML. A publicly deployed Spek page exposes its included text and metadata to anyone who can fetch it. **Review the actual export and disclosure approval before making it public.**

## Other systems — generic exchange

```powershell
python -m spek bridge-import --adapter exchange --input examples/bridge/external-system-exchange.json --template examples/article.json --mapping examples/bridge/external-system-mapping.json --out other-article.json
python -m spek build --source other-article.json --out dist-exchange
```

An exporter must emit a JSON object like:

```json
{
  "format": "spek.exchange/0.1",
  "complete": true,
  "context": {
    "dataset_ref": "export:version:pinned",
    "reader_policy_ref": "reviewed:reader-scope",
    "export_status": "authorized_local_preview"
  },
  "assertions": [{"id": "a.claim", "payload": {"statement": "opaque upstream payload"}}],
  "sources": [{"id": "s.proof", "payload": {"locator": "opaque source metadata"}}]
}
```

`export_status` authorizes **local preview only**. It does **not** authorize public deployment. Mapping must enumerate *all* required Spek article template units and evidence references, pair them with exact upstream IDs, and pin the SHA-256 of each payload with Spek's canonical internal digest (not a Kristal canonical JCS digest). See `examples/bridge/external-system-mapping.json`.

## Bidirectional navigation

- **Konstellation → Spek:** an operator selects a reader-visible result, captures/export it, compiles a Spek page, and may link to its URL from Konstellation (host integration remains to be implemented in Konstellation).
- **Spek → Konstellation/other:** Source Explorer contains the mapped source reference and a configurable deep link. This already works in exported static HTML.

The static page has no implicit authenticated session and makes no API calls. Live updates, Konstellation UI buttons, identity federation and source authorization synchronization are **not implemented**. There is no plug-in loaded inside Konstellation.

## Spek v0.5 educational extension

Spek now also supports curated, read-only Ekole/Kompose **public/demo excerpts** using `spek.educational-projection/1`. Five versioned educational layout contracts are independent of the source adapter. See [Educational Layouts](EDUCATIONAL_LAYOUTS.md), [Educational Connectors](EDUCATIONAL_CONNECTORS.md), and [Educational Privacy](EDUCATIONAL_PRIVACY.md). Spek neither orchestrates missions nor certifies curricula nor authorizes restricted static publication.
