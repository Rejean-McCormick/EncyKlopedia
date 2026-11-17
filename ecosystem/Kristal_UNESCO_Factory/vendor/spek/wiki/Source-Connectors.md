# Source Connectors

Spek supports three paths:

- Native Spek article source JSON, no bridge required.
- Konstellation's reader-scoped `ResultSet 0.2` exported by `/api/query` and pinned to a bridge mapping.
- A generic `spek.exchange/0.1` export produced by any other Kristal or third-party system.

A bridge validates complete exports, confirms dataset/reader-policy refs against an explicit mapping, checks assertion payload hashes, and records external identifiers in Source Explorer. It does **not** validate scientific content or determine whether a sentence correctly paraphrases an external assertion.

## Try Konstellation's synthetic export

```powershell
python -m spek bridge-import --adapter konstellation --input examples/bridge/konstellation-resultset.json --template examples/article.json --mapping examples/bridge/konstellation-mapping.json --out bridge-article.json
python -m spek build --source bridge-article.json --out dist-bridge
python -m spek verify-site dist-bridge
```

For real Konstellation data, `bridge-fetch-konstellation` supports an explicitly supplied QuerySpec, base URL and environment-sourced bearer token. This is an opt-in network step; **live interoperability has not yet been validated with a running Konstellation server**.

## Try another source

```powershell
python -m spek bridge-import --adapter exchange --input examples/bridge/external-system-exchange.json --template examples/article.json --mapping examples/bridge/external-system-mapping.json --out another-source.json
```

The example links use reserved demonstration domains; configure actual upstream deep-link routes in your mapping. No adapter modifies upstream data. Public website exposure requires separate authorization.

See `docs/STANDALONE_AND_CONNECTORS.md` for the contract, security assumptions and export JSON example.

## Educational adapters (v0.5)

`import-educational --adapter ekole|kompose` is a separate, curated projection importer. It never calls upstream school services or bypasses access controls; see [[Ekole Integration]] and [[Kompose Integration]].
