# Kompose Integration

Kompose orchestrates capsules, roles, missions and authorized sessions; Spek **only renders an explicitly public, preauthorized excerpt**. Kompose's reader selects prewritten, source-linked answers via `(kristal_id, topic_id, question_id)` and requires upstream access checks. Spek does not grant access or join sessions.

```
python -m spek import-educational --adapter kompose --input examples/education/kompose-public-excerpt.json --out-dir education-kompose
python -m spek build --source education-kompose/article.json --realizations education-kompose/realizations.json --out dist-kompose
```

The source includes `integrations/kompose/integration-manifest.example.json` as a **candidate** PresentationPort integration describing `render_kristals` and no student/teacher data export. It is not installed into Kompose and has not been tested with a live server. See [[Educational Privacy]].
