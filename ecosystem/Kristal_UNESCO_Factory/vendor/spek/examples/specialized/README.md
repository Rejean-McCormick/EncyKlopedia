# Démonstrations de layouts spécialisés (NON PUBLIABLES)

Ces fichiers contiennent uniquement des exemples fictifs de rôles typés et des formulations manuelles (`status=fixture`) en français, anglais et italien. Ils ne représentent aucun contenu de Kristal et ne proviennent pas de SemantiK Architect.

Depuis la racine Spek, pour une démonstration HTML/PDF/TeX :

```powershell
py -3 -m spek build --source examples/specialized/taxonomy-tree-article.json --realizations examples/specialized/taxonomy-tree-realizations.json --layouts layouts --formats html,tex,pdf --out C:\Temp\spek-specialized-demo
```

Pour un brouillon Markdown local (toujours démonstration) :

```powershell
py -3 -m spek build-wiki --source examples/specialized/taxonomy-tree-article.json --realizations examples/specialized/taxonomy-tree-realizations.json --archetype modele-multiplexe --slug exemple-taxonomie --language fr --out C:\Temp\spek-wiki-specialized-demo --demonstration
```

Un véritable article Wiki nécessite une sélection explicite d’assertions, les réalisations SemantiK qualifiées, la provenance d’état et les autorisations de publication externes C1/C2/C3.
