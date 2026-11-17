# Ekole Integration

Ekole remains the owner of curriculum, source selections, editorial review, and student-readable releases. Spek can import **only a deliberately filtered exported projection**, not an Ekole repository or teacher workspace.

```
python -m spek import-educational --adapter ekole --input examples/education/ekole-curated-preview.json --out-dir education-ekole
python -m spek build --source education-ekole/article.json --realizations education-ekole/realizations.json --out dist-education
python -m spek verify-site dist-education
```

The example is invented and trilingual, not approved educational material. The export records audience, classification, dataset, reader policy and upstream review. Spek never upgrades these claims to publication permission. Refer to [[Educational Privacy]] and [[Educational Layout Pack]].
