#!/usr/bin/env python3
"""Triage diagnostique UNESCO v28, sans reconditionner les packs et sans toucher aux preuves.

Usage: python priorisation_unesco_v28.py --packs DIR_OR_ZIP [--sortie DOSSIER]
       python priorisation_unesco_v28.py --csv prebatch.csv [--sortie DOSSIER]

Le score de PRIORITE ne produit JAMAIS une decision automatique APPROVE/REJECT.
"""
import argparse, collections, csv, datetime, html, io, json, math, os, re, sys, unicodedata, zipfile
from pathlib import Path

VERSION = '1.0.0'
NOISE_PREFIXES = ('articles with ', 'all wikipedia ', 'cs1 ', 'wikipedia ', 'pages using ', 'short description', 'use mdy ', 'use dmy ', 'articles needing ', 'all articles ', 'webarchive ', 'commons category ', 'coordinates on ', 'pages with ', 'articles lacking ', 'cleanup ', 'wikidata ', 'pages containing ', 'article ', 'citation ', 'articles containing ')
STOP = {'the','and','with','for','from','in','of','to','a','an','on','at','or','by','education','educational','de','la','des','les','et','en','du','etude','education','article','school','schools'}
EDUCATION = {'school','schools','college','colleges','university','universities','education','educational','educator','teachers','teacher','teaching','students','student','curriculum','classroom','pedagogy','pedagogical','learning','literacy','schooling','instruction','bilingual','academic','academies','campus','primary','secondary','scholarship','desegregation','desegration','training','kindergarten','schoolboard','university','instructional'}
GENERAL = {'city','cities','counties','county','municipality','municipalities','towns','geography','geographical','capital','state','states','province','provinces','metropolitan','district','regional','region','settlements','communities','people','people from','people of','neighborhood','neighbourhood'}
GEO_PATTERNS = [r'\b(cities|towns|counties|neighborhoods|municipalities|geography) (in|of)\b',r'\b(state|national) capitals\b', r'\b(geography of|urban districts|populated places)\b']


def norm(s):
    v=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode('ascii').lower()
    return re.sub(r'[^a-z0-9]+',' ',v).strip()


def tokens(s): return set(norm(s).split())


def readint(val):
    try:return max(0,int(float(val or 0)))
    except (TypeError,ValueError):return 0


def readfloat(val):
    try:return float(val)
    except (TypeError,ValueError):return 0.


def jsonlines(raw):
    return [json.loads(s) for s in raw.decode('utf-8-sig').splitlines() if s.strip()]


def read_csv_bytes(raw): return list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))


def read_pack(file):
    with zipfile.ZipFile(file) as z:
        if z.testzip() is not None: raise ValueError('ZIP corrompu')
        files=z.namelist()
        src=[n for n in files if re.search(r'(^|/)REVUE_v28_.*\.csv$',n,re.I)]
        if len(src)!=1:raise ValueError('REVUE_v28 unique absente')
        rows=read_csv_bytes(z.read(src[0])); js=next((n for n in files if n.endswith('CONTEXTES_DOCUMENTAIRES_V28.jsonl')),None)
        context={c['candidate_id']:c for c in jsonlines(z.read(js))} if js else {}
        if len({r['candidate_id'] for r in rows})!=len(rows): raise ValueError('Identifiants dupliques')
        # Contrôle informatif du manifeste avant exploitation.
        m=next((n for n in files if n.endswith('MANIFEST_CONTEXTE_V28.json')),None)
        if m:
            import hashlib
            manifest=json.loads(z.read(m))
            expected=manifest.get('source_csv_sha256')
            if expected and expected!=hashlib.sha256(z.read(src[0])).hexdigest(): raise ValueError('Empreinte source incoherente')
        return rows,context


def features(row,c=None):
    c=c or {}
    art=c.get('article') or {}
    concept=c.get('concept') or {}
    title=art.get('titre') or row.get('title') or ''
    labels=' '.join((concept.get('titre_en') or [])+(concept.get('titre_fr') or [])+(concept.get('autres_libelles_en') or [])) or row.get('concept_en','')
    title_terms=tokens(title); concept_terms=tokens(labels)-STOP
    categories=[norm(t) for t in art.get('categories_wikipedia',[]) if not norm(t).startswith(NOISE_PREFIXES)]
    cat_terms=tokens(' '.join(categories))
    sources=[e.get('article_source','') for e in c.get('evidence',[]) if isinstance(e,dict)]
    sourceterms=tokens(' '.join(sources))
    evidence=c.get('evidence',[])
    link_count=readint(row.get('link_evidence')) or sum(e.get('type_lien')=='WIKILINK' for e in evidence)
    cat_count=readint(row.get('category_evidence')) or sum(e.get('type_lien')=='SHARED_CATEGORY' for e in evidence)
    subcat_count=readint(row.get('subcategory_evidence')) or sum(e.get('type_lien')=='SUBCATEGORY' for e in evidence)
    direct_sources={norm(e.get('article_source','')) for e in evidence if e.get('type_lien')=='WIKILINK'}
    note=' '.join((concept.get('note_portee_en') or [])+(concept.get('note_portee_fr') or []))
    articletext=' '.join(str(art.get(field) or '') for field in ('introduction','extrait_intro','extrait','resume','texte'))
    # Exclure les categories de maintenance Wikipedia : elles introduiraient du bruit.
    f={
      'direct_links':min(link_count,5)/5,
      'direct_sources':min(len(direct_sources),4)/4,
      'category_links':min(cat_count,5)/5,
      'subcategory_links':min(subcat_count,4)/4,
      'seeds':min(readint(row.get('seed_count')),5)/5,
      'title_concept_overlap':len(concept_terms & title_terms)/max(1,len(concept_terms)),
      'category_concept_overlap':len(concept_terms & cat_terms)/max(1,len(concept_terms)),
      'source_concept_overlap':len(concept_terms & sourceterms)/max(1,len(concept_terms)),
      'title_educational':float(bool(title_terms & EDUCATION)),
      'category_educational':float(bool(cat_terms & EDUCATION)),
      'source_educational':float(bool(sourceterms & EDUCATION)),
      'generic_geography':float(any(re.search(p,x) for x in categories for p in GEO_PATTERNS)),
      'article_is_abstract':float(bool(title_terms & {'virtue','wisdom','reason','rights','violence','multiculturalism','legislation','bias','demography','justice','globalization','decentralization','language','religion','philosophy','law'})),
      'title_substantive':float(bool(title_terms & {'desegregation','education','educational','school','schools','college','colleges','university','universities','schooling','pedagogy','teaching','instruction','bilingual','curriculum','teacher','teachers'})),
      'text_available':float(bool(articletext.strip())),
      'text_concept':float(bool(concept_terms & tokens(articletext))),
      'scope_note':float(bool(note.strip())),
    }
    return f


# Modele logistique regulier appris sur cinq lots termines (550 propositions).
# La prediction n'est qu'un signal de PRIORITE, pas une decision documentaire.
# Le fichier modele est accompagne d'un rapport de validation hors lot.
def model_score(f,model):
    z=model['intercept']
    for name,weight in model['coefficients'].items():z+=weight*f.get(name,0)
    return 1/(1+math.exp(-max(-30,min(30,z))))


def analyze_one(row,context,model):
    ft=features(row,context)
    p=model_score(ft,model)
    evidence=[]
    if ft['direct_links']>0: evidence.append('liens directs')
    if ft['title_concept_overlap']>0: evidence.append('titre proche du concept')
    if ft['category_concept_overlap']>0: evidence.append('categories thematiques')
    if ft['title_educational']:evidence.append('titre scolaire/educatif')
    if ft['generic_geography']:evidence.append('geographie generique')
    if not ft['direct_links'] and ft['category_links']:evidence.append('categorie partagee seule')
    if not ft['text_available']:evidence.append('sans extrait article')
    return p, ', '.join(evidence) or 'indices faibles',ft


def iter_inputs(path):
    if path.is_file() and path.suffix.lower()=='.zip':yield path;return
    if path.is_dir():
        for p in sorted(path.rglob('v28_*.zip')):
            if p.name.startswith('RETOUR'):continue
            yield p
        return
    raise ValueError('Fournir un ZIP v28 ou un dossier contenant des ZIP v28')


def main(argv=None):
    ap=argparse.ArgumentParser(description='Analyse NON DESTRUCTIVE de priorite UNESCO v28')
    g=ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--packs',type=Path,help='ZIP source v28 ou dossier a scanner')
    g.add_argument('--csv',type=Path,help='CSV de candidats AVANT generation des packs')
    ap.add_argument('--sortie',type=Path,default=Path.cwd()/'RAPPORT_PRIORISATION_V28')
    ap.add_argument('--top',type=int,default=50)
    args=ap.parse_args(argv)
    model=json.loads((Path(__file__).parent/'modele_priorisation_v28.json').read_text(encoding='utf-8'))
    out=args.sortie;out.mkdir(parents=True,exist_ok=True)
    scores=[];errors=[]
    if args.csv:
        r=read_csv_bytes(args.csv.read_bytes()); datasets=[(args.csv.name,r,{})]
    else:
        datasets=[]
        for p in iter_inputs(args.packs):
            try:
                r,c=read_pack(p);datasets.append((p.name,r,c))
            except Exception as ex:errors.append(f'{p}: {ex}')
    for source,rows,ctx in datasets:
        for row in rows:
            key=row.get('candidate_id') or row.get('id') or ''
            if not key:errors.append(f'{source}: ligne sans candidate_id');continue
            p,why,ft=analyze_one(row,ctx.get(key),model)
            scores.append({'source':source,'candidate_id':key,'concept_id':row.get('concept_id',''),
                           'concept_en':row.get('concept_en',''),'page_id':row.get('page_id',''),
                           'title':row.get('title',''),'priorite_score':round(100*p,2),
                           'signaux':why,'score_origine':row.get('priority',''),
                           'preuve_sha256':row.get('evidence_sha256',''),
                           'nb_liens':row.get('link_evidence',''),
                           'nb_categories_partagees':row.get('category_evidence','')})
    scores.sort(key=lambda a:-a['priorite_score'])
    csvpath=out/'PRIORITES_CANDIDATS_V28.csv'
    cols=['source','candidate_id','concept_id','concept_en','page_id','title','priorite_score','signaux','score_origine','preuve_sha256','nb_liens','nb_categories_partagees']
    with csvpath.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(scores)
    bins=collections.Counter('haut >= 50' if x['priorite_score']>=50 else 'moyen 20-50' if x['priorite_score']>=20 else 'faible < 20' for x in scores)
    report={'outil':'priorisation_v28','version':VERSION,'date':datetime.datetime.now().isoformat(timespec='seconds'),
            'mode':'diagnostic_lecture_seule','candidats':len(scores),'packs':len(datasets),
            'repartition_indicative':dict(bins),'erreurs':errors,
            'precision':'Score de triage seulement, jamais decision APPROVE/REJECT. Classement sans remplacement de packs ni mise a jour des bases.',
            'haut_du_classement':scores[:max(0,args.top)]}
    (out/'BILAN_PRIORISATION_V28.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f'PRIORISATION UNESCO v28 | {len(scores)} candidats, {len(datasets)} lots/CSV',
           'Mode diagnostic : aucune modification de tache, preuve, base ou pack.',
           'Les scores ne sont PAS des decisions documentaires.',
           f'Repartition indicative : {dict(bins)}','',
           'TOP :']
    for x in scores[:max(0,args.top)]:lines.append(f"{x['priorite_score']:5.1f}  {x['candidate_id']} | {x['concept_en']} | {x['title']}")
    if errors:lines.extend(['','ERREURS :']+errors)
    (out/'BILAN_PRIORISATION_V28.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
    print('\n'.join(lines[:10]));print('RAPPORT :',out)
    return 0 if not errors else 2

if __name__=='__main__':sys.exit(main())
