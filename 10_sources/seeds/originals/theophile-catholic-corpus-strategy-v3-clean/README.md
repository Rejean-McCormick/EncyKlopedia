# Théophile — Stratégie du corpus intellectuel catholique

**Version 2.0 · 24 septembre 2026**

Ce dépôt documente la stratégie de présentation, de démonstration et de gouvernance d'un corpus numérique structuré de la tradition intellectuelle catholique, présenté publiquement sous le nom **Théophile**.

Le principe directeur est simple :

> **Montrer d'abord un objet utile, inspectable et déjà substantiel. Expliquer ensuite l'architecture et la gouvernance si l'intérêt existe.**

Le projet n'est pas, au premier chef, un chatbot. Le durable est un **corpus textuel structuré, sourcé, versionné et indépendant d'un moteur d'IA particulier**. Le chatbot est aujourd'hui l'interface la plus simple pour le consulter.

## État factuel de l'édition actuelle

L'édition `corpus-catholique-v0.2` comprend notamment :

- 398 positions documentées ;
- 528 assertions structurées ;
- 138 notices de sources, pour 137 URL distinctes ;
- 57 auteurs ou instances documentaires ;
- 39 reconstructions argumentatives ;
- 76 relations de lecture ;
- 15 classifications.

Le validateur de l'édition contrôle le schéma, les empreintes, les références internes, les totaux, certains filtres sensibles, les reçus de repérage textuel et une reconstruction hors ligne byte-identical.

Ces contrôles attestent l'intégrité et la reproductibilité de l'artefact. Ils ne constituent pas une approbation doctrinale du Saint-Siège.

## Positionnement

Le corpus a été construit avec une forte assistance automatisée, incluant l'IA générative pour la recherche, la comparaison, la synthèse candidate et l'organisation. Le résultat n'est toutefois pas un modèle entraîné.

La couche canonique est du **texte structuré**. Elle peut être :

- inspectée ;
- versionnée ;
- recherchée localement ;
- traduite ;
- reconstruite ;
- utilisée avec différents moteurs d'IA ;
- utilisée sans IA générative.

Une interface générative peut se tromper. Le corpus canonique, lui, **ne génère pas de nouvelles affirmations à la volée** : il expose des assertions déjà compilées, leurs sources, leur contexte et leur statut.

## Funnel stratégique

```text
courriel très court
      ↓
démo utile en 3 questions
      ↓
one-pager
      ↓
corpus téléchargeable
      ↓
documentation technique
      ↓
conversation avec un interlocuteur compétent
      ↓
édition institutionnelle gouvernée par l'Église, si désirée
```

Le premier contact doit donner envie d'essayer l'objet. Il ne doit pas porter tout le poids de la philosophie du projet.

## Identité publique

**Théophile**  
Architecte de systèmes opérables  
https://www.theophile.systems/  
theophile.systems@gmail.com

Théophile est le nom d'usage public du bâtisseur pour cette initiative. Le ton recommandé est direct, calme, littéral, candide et non spectaculaire.

## Règle de confiance

**Séparer les contextes est légitime. Fabriquer une provenance trompeuse ne l'est pas.**

Le premier paquet contient uniquement ce qui est nécessaire pour évaluer le corpus. La provenance présentée doit être exacte, simple et cohérente avec l’identité publique Théophile.

## Carte de la documentation

### Stratégie interne — ne pas envoyer dans le premier paquet

- [`docs/internal/00-north-star.md`](docs/internal/00-north-star.md)
- [`docs/internal/01-strategy.md`](docs/internal/01-strategy.md)
- [`docs/internal/02-positioning-theophile.md`](docs/internal/02-positioning-theophile.md)
- [`docs/internal/03-trust-and-provenance.md`](docs/internal/03-trust-and-provenance.md)
- [`docs/internal/04-outreach-funnel.md`](docs/internal/04-outreach-funnel.md)
- [`docs/internal/05-routing.md`](docs/internal/05-routing.md)
- [`docs/internal/06-success-metrics.md`](docs/internal/06-success-metrics.md)
- [`docs/internal/07-risk-register.md`](docs/internal/07-risk-register.md)
- [`docs/internal/08-narrative-guardrails.md`](docs/internal/08-narrative-guardrails.md)
- [`docs/internal/09-decision-log.md`](docs/internal/09-decision-log.md)

### Doctrine produit

- [`docs/product/10-product-thesis.md`](docs/product/10-product-thesis.md)
- [`docs/product/11-corpus-model.md`](docs/product/11-corpus-model.md)
- [`docs/product/12-quality-and-validation.md`](docs/product/12-quality-and-validation.md)
- [`docs/product/13-ai-boundary.md`](docs/product/13-ai-boundary.md)
- [`docs/product/14-cost-and-operations.md`](docs/product/14-cost-and-operations.md)
- [`docs/product/15-multilingual.md`](docs/product/15-multilingual.md)
- [`docs/product/16-sovereignty-and-forks.md`](docs/product/16-sovereignty-and-forks.md)
- [`docs/product/17-demo-scenarios.md`](docs/product/17-demo-scenarios.md)
- [`docs/product/18-benchmark-plan.md`](docs/product/18-benchmark-plan.md)

### Packaging

- [`docs/package/20-first-contact-package.md`](docs/package/20-first-contact-package.md)
- [`docs/package/21-branding-and-naming.md`](docs/package/21-branding-and-naming.md)
- [`docs/package/22-provenance-metadata.md`](docs/package/22-provenance-metadata.md)
- [`docs/package/23-demo-checklist.md`](docs/package/23-demo-checklist.md)
- [`docs/package/24-release-checklist.md`](docs/package/24-release-checklist.md)

### Documents publics / Vatican

- [`public/EMAIL-FIRST-CONTACT.md`](public/EMAIL-FIRST-CONTACT.md)
- [`public/ONE-PAGER.md`](public/ONE-PAGER.md)
- [`public/README-VATICAN.md`](public/README-VATICAN.md)
- [`public/TECHNICAL-NOTE.md`](public/TECHNICAL-NOTE.md)
- [`public/FAQ.md`](public/FAQ.md)
- [`public/DEMO-SCRIPT.md`](public/DEMO-SCRIPT.md)
