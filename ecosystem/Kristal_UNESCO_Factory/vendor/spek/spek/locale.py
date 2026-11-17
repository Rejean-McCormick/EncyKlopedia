UI = {
 'fr': {
  'eyebrow':'PUBLICATION STRUCTURÉE', 'demo':'DÉMONSTRATION — NON VALIDÉE SCIENTIFIQUEMENT',
  'abstract':'Résumé', 'result-card':'Résultat structuré', 'argument-map':'Chaîne argumentative',
  'comparison':'Comparaison méthodologique', 'claim':'Proposition', 'conditions':'Conditions de validité',
  'evidence':'Éléments de preuve', 'uncertainty':'Réserves et limites', 'implications':'Conséquences',
  'thesis':'Thèse', 'premises':'Prémisses', 'inference':'Lien logique', 'objection':'Objection',
  'conclusion':'Conclusion', 'topic':'Question étudiée', 'criterion':'Critère',
  'approach_a':'Approche A', 'approach_b':'Approche B', 'synthesis':'Synthèse',
  'limitations':'Limites', 'trace':'Traçabilité', 'source':'Origine', 'source_status':'Statut',
  'fixture':'Données illustratives ; ni publication scientifique, ni certification SemantiK',
  'source_unchecked':'Identité canonique non vérifiée', 'source_checked':'Référence à un snapshot fournie et recoupée (pas de vérification JCS)',
  'article':'Article', 'lang':'Langue', 'contents':'Sommaire', 'prototype':'Prototype technique',
  'evidence_notice':'Références de démonstration : non évaluées indépendamment',
  'realizations':'Réalisations', 'layouts':'Mises en page', 'pdf':'PDF', 'latex':'Source LaTeX', 'document':'Modèle de document', 'exports':'Formats',
 },
 'en': {
  'eyebrow':'STRUCTURED PUBLICATION', 'demo':'DEMONSTRATION — NOT SCIENTIFICALLY VALIDATED',
  'abstract':'Abstract', 'result-card':'Structured result', 'argument-map':'Argument chain',
  'comparison':'Method comparison', 'claim':'Claim', 'conditions':'Conditions of applicability',
  'evidence':'Evidence', 'uncertainty':'Qualifications and limits', 'implications':'Implications',
  'thesis':'Thesis', 'premises':'Premises', 'inference':'Logical link', 'objection':'Objection',
  'conclusion':'Conclusion', 'topic':'Research question', 'criterion':'Criterion',
  'approach_a':'Approach A', 'approach_b':'Approach B', 'synthesis':'Synthesis',
  'limitations':'Limitations', 'trace':'Traceability', 'source':'Origin', 'source_status':'Status',
  'fixture':'Illustrative inputs; neither a scientific publication nor certified SemantiK',
  'source_unchecked':'Canonical state identity not verified', 'source_checked':'Supplied snapshot reference cross-checked (not JCS-verified)',
  'article':'Article', 'lang':'Language', 'contents':'Contents', 'prototype':'Technical prototype',
  'evidence_notice':'Illustrative references: not independently assessed',
  'realizations':'Realizations', 'layouts':'Layouts', 'pdf':'PDF', 'latex':'LaTeX source', 'document':'Document model', 'exports':'Exports',
 },
 'it': {
  'eyebrow':'PUBBLICAZIONE STRUTTURATA', 'demo':'DIMOSTRAZIONE — NON CONVALIDATA SCIENTIFICAMENTE',
  'abstract':'Riassunto', 'result-card':'Risultato strutturato', 'argument-map':'Catena argomentativa',
  'comparison':'Confronto metodologico', 'claim':'Affermazione', 'conditions':'Condizioni di validità',
  'evidence':'Elementi di prova', 'uncertainty':'Riserve e limiti', 'implications':'Implicazioni',
  'thesis':'Tesi', 'premises':'Premesse', 'inference':'Nesso logico', 'objection':'Obiezione',
  'conclusion':'Conclusione', 'topic':'Questione di ricerca', 'criterion':'Criterio',
  'approach_a':'Approccio A', 'approach_b':'Approccio B', 'synthesis':'Sintesi',
  'limitations':'Limiti', 'trace':'Tracciabilità', 'source':'Origine', 'source_status':'Stato',
  'fixture':'Dati illustrativi; né pubblicazione scientifica né SemantiK certificato',
  'source_unchecked':'Identità canonica non verificata', 'source_checked':'Riferimento allo snapshot fornito e confrontato (senza verifica JCS)',
  'article':'Articolo', 'lang':'Lingua', 'contents':'Indice', 'prototype':'Prototipo tecnico',
  'evidence_notice':'Riferimenti dimostrativi: non valutati in modo indipendente',
  'realizations':'Realizzazioni', 'layouts':'Layout', 'pdf':'PDF', 'latex':'Sorgente LaTeX', 'document':'Modello del documento', 'exports':'Formati',
 }
}

# Semantic roles for explicitly bound specialized editorial layouts.
_SPECIALIZED_SLOTS = {
 'fr': {
  'context':'Contexte','scope':'Périmètre','entities':'Entités','relations':'Relations','limits':'Limites',
  'stages':'Étapes déclarées','links':'Liens déclarés','axes':'Axes','entries':'Entrées déclarées',
  'period_context':'Période déclarée','accounts':'Comptes','reconciliations':'Rapprochements déclarés',
  'concepts':'Concepts','specializations':'Relations de spécialisation',
  'observations':'Observations','constraints':'Contraintes','sources':'Sources','attributions':'Attributions',
 },
 'en': {
  'context':'Context','scope':'Scope','entities':'Entities','relations':'Relations','limits':'Limits',
  'stages':'Declared stages','links':'Declared links','axes':'Axes','entries':'Declared entries',
  'period_context':'Declared period','accounts':'Accounts','reconciliations':'Declared reconciliations',
  'concepts':'Concepts','specializations':'Specialization relations',
  'observations':'Observations','constraints':'Constraints','sources':'Sources','attributions':'Attributions',
 },
 'it': {
  'context':'Contesto','scope':'Ambito','entities':'Entità','relations':'Relazioni','limits':'Limiti',
  'stages':'Fasi dichiarate','links':'Collegamenti dichiarati','axes':'Assi','entries':'Registrazioni dichiarate',
  'period_context':'Periodo dichiarato','accounts':'Conti','reconciliations':'Riconciliazioni dichiarate',
  'concepts':'Concetti','specializations':'Relazioni di specializzazione',
  'observations':'Osservazioni','constraints':'Vincoli','sources':'Fonti','attributions':'Attribuzioni',
 },
}
for _lang,_labels in _SPECIALIZED_SLOTS.items():
    UI[_lang].update(_labels)

# Source explorer vocabulary is localized, but never implies certification.
INSPECTOR_UI = {
 'fr': {
  'open':'Explorer la source','origin':'Source sémantique','unit':'Unité','kind':'Type','epistemic':'Qualification','origin_type':'Origine du document',
  'state':'État Kristal','commitment':'Engagement de l’état','unavailable':'Non fourni','proofs':'Preuves et références','proof_status':'Statut de la preuve','locator':'Localisation',
  'realization':'Réalisation linguistique','provider':'Fournisseur','realization_status':'Statut','key':'Clé de réalisation','request':'Requête',
  'runtime':'Ensemble d’exécution','words':'Mots et attributs','word':'Mot','lemma':'Lemme','pos':'Catégorie','features':'Attributs',
  'links':'Liens linguistiques','not_supplied':'Non renseigné','token_note':'Segmentation de surface uniquement. Aucun attribut grammatical non fourni n’est déduit.',
  'annotation':'Qualification des annotations','none':'Aucune référence rattachée','input':'Empreinte de la source','technical':'Référence technique',
  'manual_fixture':'Exemple manuel','surface_only':'Surface uniquement','reviewed':'Révisé','qualified':'Qualifié',
 },
 'en': {
  'open':'Explore source','origin':'Semantic source','unit':'Unit','kind':'Type','epistemic':'Qualification','origin_type':'Document origin',
  'state':'Kristal state','commitment':'State commitment','unavailable':'Not supplied','proofs':'Evidence and references','proof_status':'Evidence status','locator':'Locator',
  'realization':'Language realization','provider':'Provider','realization_status':'Status','key':'Realization key','request':'Request',
  'runtime':'Runtime set','words':'Words and attributes','word':'Word','lemma':'Lemma','pos':'Part of speech','features':'Features',
  'links':'Linguistic links','not_supplied':'Not supplied','token_note':'Surface tokenization only. Missing grammatical attributes are not inferred.',
  'annotation':'Annotation qualification','none':'No attached references','input':'Source fingerprint','technical':'Technical reference',
  'manual_fixture':'Manual illustration','surface_only':'Surface only','reviewed':'Reviewed','qualified':'Qualified',
 },
 'it': {
  'open':'Esplora la fonte','origin':'Fonte semantica','unit':'Unità','kind':'Tipo','epistemic':'Qualificazione','origin_type':'Origine del documento',
  'state':'Stato Kristal','commitment':'Impegno dello stato','unavailable':'Non fornito','proofs':'Prove e riferimenti','proof_status':'Stato della prova','locator':'Posizione',
  'realization':'Realizzazione linguistica','provider':'Fornitore','realization_status':'Stato','key':'Chiave di realizzazione','request':'Richiesta',
  'runtime':'Insieme di esecuzione','words':'Parole e attributi','word':'Parola','lemma':'Lemma','pos':'Parte del discorso','features':'Caratteristiche',
  'links':'Collegamenti linguistici','not_supplied':'Non fornito','token_note':'Segmentazione superficiale soltanto. Gli attributi grammaticali mancanti non vengono dedotti.',
  'annotation':'Qualificazione delle annotazioni','none':'Nessun riferimento collegato','input':'Impronta della fonte','technical':'Riferimento tecnico',
  'manual_fixture':'Esempio manuale','surface_only':'Solo superficie','reviewed':'Revisionato','qualified':'Qualificato',
 },
}

# v0.4 standalone connector and realization provenance vocabulary.
INSPECTOR_UI['fr'].update(external_ref='Référence externe', open_graph='Voir dans le système source', channel='Voie linguistique', model='Modèle IA', generation='Génération', review='Révision humaine')
INSPECTOR_UI['en'].update(external_ref='External reference', open_graph='View in source system', channel='Language channel', model='AI model', generation='Generation', review='Human review')
INSPECTOR_UI['it'].update(external_ref='Riferimento esterno', open_graph='Apri nel sistema sorgente', channel='Canale linguistico', model='Modello IA', generation='Generazione', review='Revisione umana')

INSPECTOR_UI['fr'].update(system='Système source', dataset='Jeu de données', policy='Politique de lecture', projection='Empreinte de projection')
INSPECTOR_UI['en'].update(system='Source system', dataset='Dataset', policy='Reader policy', projection='Projection fingerprint')
INSPECTOR_UI['it'].update(system='Sistema sorgente', dataset='Dataset', policy='Politica di lettura', projection='Impronta della proiezione')

UI['fr'].update({'concept-card': 'Fiche notion', 'learning-path': 'Parcours de notions', 'evidence-comparison': 'Comparaison de sources', 'observation-inference': 'Observation et interprétation', 'chronology': 'Chronologie documentée', 'definition': 'Définition', 'examples': 'Exemples', 'counterexamples': 'Contre-exemples', 'context': 'Contexte', 'limits': 'Limites', 'objective': 'Objectif', 'prerequisites': 'Préalables', 'steps': 'Étapes', 'reflection': 'Question de réflexion', 'question': 'Question', 'source_a': 'Source A', 'source_b': 'Source B', 'perspective_a': 'Perspective A', 'perspective_b': 'Perspective B', 'observations': 'Observations', 'interpretation': 'Interprétation', 'verification': 'Comment vérifier', 'events': 'Événements'})

UI['en'].update({'concept-card': 'Concept card', 'learning-path': 'Learning path', 'evidence-comparison': 'Source comparison', 'observation-inference': 'Observation and inference', 'chronology': 'Documented timeline', 'definition': 'Definition', 'examples': 'Examples', 'counterexamples': 'Counterexamples', 'context': 'Context', 'limits': 'Limits', 'objective': 'Learning objective', 'prerequisites': 'Prerequisites', 'steps': 'Steps', 'reflection': 'Reflection question', 'question': 'Question', 'source_a': 'Source A', 'source_b': 'Source B', 'perspective_a': 'Perspective A', 'perspective_b': 'Perspective B', 'observations': 'Observations', 'interpretation': 'Interpretation', 'verification': 'How to check', 'events': 'Events'})

UI['it'].update({'concept-card': 'Scheda concetto', 'learning-path': 'Percorso di apprendimento', 'evidence-comparison': 'Confronto delle fonti', 'observation-inference': 'Osservazione e inferenza', 'chronology': 'Cronologia documentata', 'definition': 'Definizione', 'examples': 'Esempi', 'counterexamples': 'Controesempi', 'context': 'Contesto', 'limits': 'Limiti', 'objective': 'Obiettivo', 'prerequisites': 'Prerequisiti', 'steps': 'Passaggi', 'reflection': 'Domanda di riflessione', 'question': 'Domanda', 'source_a': 'Fonte A', 'source_b': 'Fonte B', 'perspective_a': 'Prospettiva A', 'perspective_b': 'Prospettiva B', 'observations': 'Osservazioni', 'interpretation': 'Interpretazione', 'verification': 'Come verificare', 'events': 'Eventi'})
