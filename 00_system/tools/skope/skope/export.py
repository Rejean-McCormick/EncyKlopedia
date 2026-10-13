"""Proposition Skope -> EncyK, non canonique et sans JSON source inventé."""
from __future__ import annotations
import hashlib
import io
import json
import re
import zipfile
from .db import meta
from .scope import explore


def canonical(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))


def proposal(conn,recipe,scope_key=None,guidance=None,target=None):
    report=explore(conn,recipe)
    if report['truncated']:
        raise ValueError('Exploration tronquée: augmentez max_entities ou réduisez le périmètre avant de préparer un scope EncyK')
    selected=[n for n in report['nodes'] if re.fullmatch(r'Q[0-9]+',n['id'])]
    if len(selected)!=len(report['nodes']):raise ValueError('Seules les entités QID sont admises dans le scope proposé')
    key=scope_key or ('skope-'+report['root'].lower())
    if not re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,65}',key):raise ValueError('scope_key invalide')
    source=meta(conn)
    fingerprint='sha256:'+hashlib.sha256(canonical({'source':report['source_snapshot_digest'],'recipe':report['recipe'],'selected':sorted(x['id'] for x in selected)}).encode()).hexdigest()
    registry_path='10_sources/seeds/active/skope/'+key+'.seed.json'
    scope_path='00_system/tools/scope-builder/config/scopes/'+key+'.scope.json'
    seeds={'schema_version':'skope-encyk-seed-registry/1.0','registry_key':key,'status':'proposal_requires_review','title':'Sélection Skope '+key,
           'source_snapshot_digest':report['source_snapshot_digest'],'selection_fingerprint':fingerprint,
           'records':[{'key':n['id'].lower(),'display_name':n['label'],'wikidata_qid':n['id'],'representation_kind':'other',
                'skope_reasons':n['reasons']} for n in selected]}
    config={'schema_version':'encyklopedia-scope/v3','scope_key':key,'title':'Sélection Skope (proposition à réviser)',
            'root_source':{'kind':'registry','path':registry_path},
            'root_semantics':{'role':'skope_selected_root','kind':'other'},
            'requires_complete_global_index':True,'discovery_backend':'index',
            'discovery':{'include_all_entity_relations_from_roots':False,'reverse_root_relations':{},'follow_rules':[],
                         'max_entities':max(10000,len(selected)+10),'max_edges':1000},
            'evidence':{'preserve_full_entity_json':True,'preserve_qualifiers':True,'preserve_references':True,
                        'preserve_sitelinks':True,'preserve_all_literal_values':True},
            'proposal_provenance':{'producer':'skope-encyk-proposal/1.0','selection_fingerprint':fingerprint,
                                   'source_snapshot_digest':report['source_snapshot_digest'],
                                   'arketype_guidance_format':guidance.get('format') if guidance else None,
                                   'status':'working_requires_human_review'}}
    manifest={'format':'skope-encyk-proposal/1.0','status':'working_non_canonical','selection_fingerprint':fingerprint,
              'scope_key':key,'source_snapshot_digest':report['source_snapshot_digest'],
              'source_identity_strength':source['source_identity_strength'],
              'selected_entities':len(selected),'raw_source_json_included':False,
              'publication_authorized':False,'activation_authorized':False,'evidence_available':False,
              'limitations':['Index EncyK compact agrégé, dépourvu des statement IDs et de la source JSON complète',
                             'Examen humain et contrôle du dump obligatoires avant copie dans les chemins actifs',
                             'La qualification et le handoff relèvent du pipeline EncyK et de Médiathèque']}
    if target:
        manifest['target_kristal']={k:target[k] for k in ('slug','state_ref','domain')}
        manifest['target_kristal_binding']='review_only_no_canonical_write'
        config['proposal_provenance']['target_kristal_state_ref']=target['state_ref']
    return report,registry_path,seeds,scope_path,config,manifest


def bundle(conn,recipe,scope_key=None,guidance=None,target=None):
    report,registry_path,seeds,scope_path,config,manifest=proposal(conn,recipe,scope_key,guidance,target)
    files={
      'manifest.json':manifest,
      'review/scope.recipe.json':report['recipe'],
      'review/scope.report.json':report,
      'staged/'+registry_path:seeds,
      'staged/'+scope_path:config,
    }
    if guidance is not None:
        files['review/arketype.scope-guidance.json']=guidance
    if target is not None:
        files['review/target-kristal.json']=target
    readme='''# Proposition de périmètre EncyK / Skope\n\nNON CANONIQUE — aucune autorisation d'activation, publication, ou admission n'est accordée.\n\n1. Examiner `review/scope.report.json` (branches, convergence et sélection).\n2. Vérifier le dump/index source, le Kristal choisi sous `review/target-kristal.json` et les guides Arketype (conception seulement).\n3. Copier explicitement les **deux** fichiers sous `staged/` à la racine du dépôt EncyK (mêmes chemins relatifs, sans le préfixe staged/).\n4. Exécuter le pipeline habituel (`harvest.ps1 -Scope <scope_key>`), avec le même dump et un index global complet.\n5. EncyK extrait alors séparément le JSON intégral depuis la source d'origine et prépare le handoff Médiathèque.\n6. Relier les sources au Kristal choisi via la chaîne de validation/authoring ; aucune injection canonique n'est incluse dans ce ZIP.\n\nL'index SQLite de découverte ne contient PAS les JSON source, les qualificatifs ni les références complètes. Le graphe et la liste Skope ne peuvent jamais remplacer une preuve.\n'''.replace('<scope_key>',manifest['scope_key'])
    bio=io.BytesIO()
    with zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in sorted(files):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(json.dumps(files[name],ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode())
        info=zipfile.ZipInfo('README.md',(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,readme.encode())
    return bio.getvalue()
