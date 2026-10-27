// Non-authoritative French presentation dictionary. The original predicates,
// identifiers, provenance, and assertion statuses remain unchanged.
// Unknown Wikidata properties are NOT assigned guessed meanings.
const WIKIDATA_FR = Object.freeze({
  P50: 'Auteur', P921: 'Sujet principal', P1433: 'Publié dans',
  P629: 'Édition ou traduction de', P747: 'Éditions ou traductions',
  P800: 'Œuvre notable', P361: 'Fait partie de', P527: 'Comprend',
  P155: 'Précédé par', P156: 'Suivi par', P1889: 'À distinguer de',
  P170: 'Créateur', P737: 'Influencé par', P144: 'Inspiré de',
  P98: 'Éditeur scientifique', P138: 'Nommé d’après',
  P184: 'Directeur de thèse', P185: 'Étudiant en doctorat',
  P1066: 'A étudié auprès de', P710: 'Participant', P674: 'Personnages',
});
const RELATIONS_FR = Object.freeze({
  academicien_sur_liste_publiee: 'Source attestant une inscription sur une liste d’académiciens',
  membre_liste_historique: 'Mention dans une liste historique',
  membre_quinquennat: 'Membre pendant un quinquennat',
  pontificat_recense: 'Pontificat recensé',
  prix_attribue: 'Prix attribué',
  prix_annonce: 'Prix annoncé',
  titre_ecclesial_reconnu: 'Source relative au titre ecclésiastique',
  saintete_reconnue: 'Source relative à la sainteté reconnue',
  historic_author_reference: 'Référence d’auteur historique',
  source_url_recorded: 'Adresse de source répertoriée',
  documented_by: 'Documenté par',
  historic_theme: 'Thème historique',
  has_documented_position: 'Position documentée',
  has_open_research_claim: 'Hypothèse de recherche ouverte',
  candidate_correspondence_from_skope: 'Correspondance proposée (non vérifiée)',
  hypothesized_candidate_qid: 'Identifiant Wikidata proposé (non vérifié)',
  v9_node_kind: 'Type d’élément dans la projection',
});

export function readableCode(text) {
  const raw = String(text ?? '');
  if (/^P[1-9]\d{0,8}$/i.test(raw)) return `Propriété Wikidata ${raw.toUpperCase()} (libellé indisponible)`;
  if (/^Q[1-9]\d{0,12}$/i.test(raw)) return `Élément Wikidata ${raw.toUpperCase()} (libellé indisponible)`;
  return raw.replace(/([a-z0-9])([A-Z])/g, '$1 $2')
    .replace(/[_:./-]+/g, ' ').replace(/\s+/g, ' ').trim()
    .replace(/^./, c => c.toUpperCase());
}
export function semanticLabel(predicate, { configured = null, rangeKind = '' } = {}) {
  const raw = String(predicate || '');
  // A locally supplied, explicit mapping takes precedence (never reinterpret IDs).
  if (typeof configured === 'string' && configured.trim() && configured !== raw) {
    const value=configured.trim();
    // Old viewer profiles duplicated the opaque property ID in the human label.
    // Do not overwrite an intentional, independently meaningful custom label.
    if (!(WIKIDATA_FR[raw] && value.toUpperCase().endsWith(`(${raw.toUpperCase()})`))) return value;
  }
  if (WIKIDATA_FR[raw]) return WIKIDATA_FR[raw];
  if (RELATIONS_FR[raw]) return RELATIONS_FR[raw];
  return readableCode(raw) || 'Relation sans libellé';
}
// Only normalize known diagnostic prefixes of noncanonical hypothesis titles.
// This is text presentation, not a change of epistemic status or identity.
const HYPOTHESIS_PREFIX = Object.freeze({
  wikidata_identity: 'Identité Wikidata proposée',
  recognition_roster_reference: 'Référence de liste de reconnaissance à vérifier',
  recognition_roster_reference_candidate: 'Référence de liste à vérifier',
  historical_roster_reference: 'Référence historique à vérifier',
});
export function readableNodeLabel(raw, kind='') {
  const label=String(raw ?? '');
  if (/^[PQ][1-9]\d+$/i.test(label)) return readableCode(label);
  if (!['unconfirmed_research_claim','unconfirmed_research_candidate'].includes(kind)) return label;
  const match=/^([a-z][a-z0-9_]+)\s*[·:—]\s*(.+)$/.exec(label);
  const presented = match && HYPOTHESIS_PREFIX[match[1]] ? `${HYPOTHESIS_PREFIX[match[1]]} · ${match[2]}` : label;
  return presented.length <= 300 ? presented : label;
}
export const WIKIDATA_PRESENTATION = WIKIDATA_FR;
export const KNOWN_RELATION_PRESENTATION = RELATIONS_FR;

const STATES_FR = Object.freeze({
  unspecified:'Non précisé', not_evaluated:'Non évalué',
  read_only_local_projection:'Projection locale en lecture seule',
  sourced:'Sourcé', validated:'Validé', disputed:'Contesté',
  hypothesis:'Hypothèse', claimed:'Déclaré', reviewed:'Révisé',
  rejected:'Rejeté', retracted:'Rétracté', superseded:'Remplacé',
  candidate:'Candidat', unverified:'Non vérifié',
});
export function readableStatus(value) {
  const raw=String(value ?? '');
  return STATES_FR[raw] || readableCode(raw) || 'Non précisé';
}

export function normalizeTerm(value) {
  return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
    .toLowerCase().replace(/[’']/g, ' ').replace(/[_–—-]+/g, ' ')
    .replace(/[^a-z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim();
}
const words = value => normalizeTerm(value).split(' ').filter(Boolean);

// Word-boundary matching prevents `aquin` from matching the suffix of `Joaquín`.
// Spelling tolerance is only used if no stronger matches exist for the query.
export function orientationScore(entity, rawQuery) {
  const q=normalizeTerm(rawQuery);
  if (!q) return 0;
  const label=normalizeTerm(entity?.label);
  const aliases=(entity?.aliases || []).map(normalizeTerm);
  if(label===q) return 180;
  if(aliases.includes(q)) return 170;
  if(label.startsWith(q+' ')) return 155;
  if(words(label).includes(q)) return 150;
  if(aliases.some(a=>words(a).includes(q))) return 145;
  if(q.length>=3 && words(label).some(w=>w.startsWith(q))) return 130;
  if(q.length>=3 && aliases.some(a=>words(a).some(w=>w.startsWith(q)))) return 120;
  if(q.includes(' ') && label.includes(q)) return 115;
  if(q.length>=4 && words(entity?.description).includes(q)) return 45;
  return 0;
}
export function rankOrientation(entities, term, limit=16, preferredType='') {
  const matches=entities.map(entity=>({entity,score:orientationScore(entity,term)})).filter(x=>x.score>0);
  const hasStrong=matches.some(x=>x.score>=115);
  const ordered = matches.filter(x=>!hasStrong || x.score>=115)
    .sort((a,b)=>b.score-a.score ||
      Number(b.entity.type===preferredType)-Number(a.entity.type===preferredType) ||
      a.entity.label.localeCompare(b.entity.label,'fr') || a.entity.id.localeCompare(b.entity.id));
  // Diversify the first page by *visible label*, not by identity. Nothing is
  // merged in the graph or treated as the same person: duplicates remain as
  // distinct results and are considered after the diverse first pass.
  const seen = new Set(), diverse=[], duplicates=[];
  for (const item of ordered) {
    const name=normalizeTerm(item.entity.label);
    if(seen.has(name)) duplicates.push(item);
    else {seen.add(name);diverse.push(item);}
  }
  return diverse.concat(duplicates).slice(0,limit);
}
