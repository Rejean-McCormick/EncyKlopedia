"""Configuration explicite; les gros index restent sur D: et ne sont jamais copiés."""
from __future__ import annotations
from dataclasses import dataclass, asdict, fields
from pathlib import Path
import json
import os

ROOT = Path(__file__).resolve().parent.parent

def _work_default():
    root = Path(r'D:\EncyKlopedia') if os.name == 'nt' else Path.home()/'EncyKlopediaV32'
    return root/'30_working'/'encyk_v32'

@dataclass
class Settings:
    # Les chemins sont configurables et jamais présumés existants.
    unesco_root: str = str(ROOT/'ecosystem'/'UNESCO_Kristals')
    wikipedia_sql: str = r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en.sqlite'
    wikidata_sql: str = r'D:\EncyKlopedia\30_working\wikidata\wikidata.compact.sqlite'
    wikipedia_xml: str = r'D:\EncyKlopedia\30_working\wikipedia_en_uncompressed\enwiki-latest-pages-articles-multistream.xml'
    wikipedia_direct_index: str = r'D:\EncyKlopedia\80_search_indexes\mediatheque-references\wikipedia_en_direct_pages_v21.sqlite'
    catalogue_v25: str = r'D:\EncyKlopedia\80_search_indexes\EncyKlopedia\catalogue_global_unesco_wikipedia_v25.sqlite'
    station_v30: str = r'D:\EncyKlopedia\30_working\poste_chatgpt_v30\station_v30.sqlite'
    work_root: str = str(_work_default())
    kristal_roots: list[str] = None
    select_pack_size: int = 150
    selection_excerpt_chars: int = 3500
    enrich_pack_articles: int = 60
    enrich_word_budget: int = 200000
    enrich_byte_budget: int = 45 * 1024 * 1024
    graph_per_anchor_limit: int = 2500
    lane_count: int = 10
    extraction_profile: str = 'encyk.generic.v1'
    prepare_scan_limit: int = 5000
    source_retry_seconds: int = 3600
    source_epoch: str = ''

    def __post_init__(self):
        if self.kristal_roots is None:
            self.kristal_roots = [str(ROOT/'ecosystem'/'UNESCO_Kristals'),
                                 str(ROOT/'ecosystem'/'UNESCO_Workbench'/'candidates')]

    @property
    def db_path(self):
        return Path(self.work_root)/'encyk_v32.sqlite'

    @property
    def packs_path(self):
        return Path(self.work_root)/'packs'

    @classmethod
    def load(cls, path=None):
        where = Path(path or os.getenv('ENCYK_CONFIG', ROOT/'config'/'settings.json'))
        if not where.is_file():
            result = cls()
        else:
            data=json.loads(where.read_text(encoding='utf-8-sig'))
            known={x.name for x in fields(cls)}
            if not isinstance(data,dict):raise ValueError('Configuration : objet JSON attendu')
            unknown=set(data)-known
            if unknown:raise ValueError('Clés de configuration inconnues : '+', '.join(sorted(unknown)))
            result=cls(**data)
        # Environment overrides win; no scanning of a hidden system path.
        env={'ENCYK_UNESCO_ROOT':'unesco_root','ENCYK_WIKIPEDIA_SQL':'wikipedia_sql',
             'ENCYK_WIKIDATA_SQL':'wikidata_sql','ENCYK_WORK_ROOT':'work_root',
             'ENCYK_WIKIPEDIA_XML':'wikipedia_xml','ENCYK_DIRECT_INDEX':'wikipedia_direct_index',
             'ENCYK_KRISTAL_ROOTS':'kristal_roots'}
        for name,field_name in env.items():
            if name in os.environ:
                value=os.environ[name]
                if field_name=='kristal_roots':value=value.split(os.pathsep)
                setattr(result,field_name,value)
        if type(result.lane_count) is not int or not 1 <= result.lane_count <= 10:raise ValueError('lane_count doit être entre 1 et 10')
        if type(result.select_pack_size) is not int or not 1 <= result.select_pack_size <= 4000:raise ValueError('select_pack_size hors bornes')
        if type(result.enrich_pack_articles) is not int or not 1 <= result.enrich_pack_articles <= 120:raise ValueError('enrich_pack_articles hors bornes')
        for name in ('enrich_word_budget','enrich_byte_budget','prepare_scan_limit','source_retry_seconds','selection_excerpt_chars','graph_per_anchor_limit'):
            value=getattr(result,name)
            if type(value) is not int or value<=0:raise ValueError(name+' doit être un entier positif')
        if not isinstance(result.extraction_profile,str) or not result.extraction_profile.strip():
            raise ValueError('extraction_profile requis')
        return result

    def paths_status(self):
        return {k: {'path':getattr(self,k),'exists':Path(getattr(self,k)).exists()}
                for k in ('unesco_root','wikipedia_sql','wikidata_sql','wikipedia_xml',
                          'wikipedia_direct_index','catalogue_v25','station_v30','work_root')}

    def save_example(self,path):
        path=Path(path)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(asdict(self),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
