# Educational Privacy

Spek is a static publisher, not an authenticated student portal. It **must not** embed learner identities, individualized assessments, teacher-only solutions, student media, session grants, private diagnoses, consent metadata or hidden classroom access controls in public HTML/JSON/PDF.

The `spek.educational-projection/1` import accepts curated `public_demo` or already reviewed `public_released_excerpt` only, for **local preview**. Structural allowlist checks reject unrecognized fields and sensitive file locators; no technical filter can certify the privacy of arbitrary natural-language prose. Review the entire exported data with the school/institution. Kompose authorization, Ekole pedagogy and source/publication rights remain independent decisions.

See [[Ekole Integration]] and [[Kompose Integration]].
