"""Targeted diagnostics: actual columns, query plans and a single XML sample."""
from pathlib import Path
from .sql import read_source

def run(settings):
    result={'status':'OK','sources':{},'warnings':[],'capabilities':{}}
    requirements={
      'wikipedia_sql':{'wiki_qid':{'qid','page_id'},'wiki_pages':{'page_id','ns','title','redirect','latest_revision','content_bytes'}},
      'wikidata_sql':{'entity':{'id'},'name':{'id'},'meta':{'key','value'},'entity_edge':{'subject_id','property_id','target_id','statement_count','best_rank'}},
      'wikipedia_direct_index':{'pages':{'page_id','byte_offset','byte_length','namespace','title','revision_id','is_redirect'}}}
    for key in ('unesco_root','wikipedia_sql','wikidata_sql','wikipedia_xml','wikipedia_direct_index','catalogue_v25','station_v30'):
        path=Path(getattr(settings,key));result['sources'][key]={'exists':path.exists(),'path':str(path)}
        if not path.exists():result['warnings'].append(key+' absent : '+str(path))
        if key not in requirements or not path.is_file():continue
        try:
            with read_source(path) as db:
                missing={table:sorted(cols-{r[1] for r in db.execute('PRAGMA table_info('+table+')')}) for table,cols in requirements[key].items()}
                missing={table:cols for table,cols in missing.items() if cols}
                result['capabilities'][key]={'available':not missing,'missing_columns':missing}
                if missing:
                    result['warnings'].append(key+' : colonnes absentes '+str(missing));continue
                if key=='wikidata_sql':
                    complete=db.execute("SELECT value FROM meta WHERE key='complete'").fetchone()
                    if not complete or str(complete[0]).lower() not in ('true','1'):
                        result['capabilities'][key]['available']=False
                        result['warnings'].append('Index Wikidata déclaré incomplet')
                queries=[]
                if key=='wikipedia_sql':queries=[("SELECT p.page_id FROM wiki_qid q JOIN wiki_pages p ON p.page_id=q.page_id WHERE q.qid=? AND p.ns=0",('Q1',))]
                elif key=='wikidata_sql':queries=[('SELECT subject_id FROM entity_edge WHERE target_id=? AND property_id=? AND subject_id>? ORDER BY subject_id LIMIT 100',(1,31,0))]
                plans=[r[3] for sql,params in queries for r in db.execute('EXPLAIN QUERY PLAN '+sql,params)]
                result['capabilities'][key]['query_plan']=plans
                if any('SCAN ' in x.upper() for x in plans):result['warnings'].append(key+' : plan de requête avec SCAN; vérifier les index avant campagne')
        except Exception as exc:result['warnings'].append(key+' : '+str(exc))
    result['capabilities']['enrichment_fulltext']={'available':False}
    if result['capabilities'].get('wikipedia_direct_index',{}).get('available') and Path(settings.wikipedia_xml).is_file():
        try:
            from .pipeline import _read_article
            with read_source(settings.wikipedia_direct_index) as ix:
                page=ix.execute('SELECT page_id FROM pages WHERE namespace=0 AND is_redirect=0 LIMIT 1').fetchone()
            if not page:raise ValueError('Index direct vide')
            raw,revision,title=_read_article(settings,page[0])
            result['capabilities']['enrichment_fulltext']={'available':True,'sample_page_id':page[0],'revision':revision,'bytes':len(raw)}
        except Exception as exc:result['warnings'].append('Lecture XML échantillon : '+str(exc))
    result['capabilities']['kristal_admission']={'available':False,'reason':'Authoring Kit non qualifié; aucune écriture canonique'}
    if result['warnings']:result['status']='PARTIAL'
    return result
