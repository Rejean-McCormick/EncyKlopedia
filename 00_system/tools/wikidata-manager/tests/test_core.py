import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from common import encode_wid,decode_wid,normalize_name
from build_compact_index import process_entity

def test_ids():
    for x in ['Q937','P19','L22']: assert decode_wid(encode_wid(x))==x

def test_names(): assert normalize_name('Éinstein, Albert')=='einstein albert'

def test_presence_without_literal_leak():
    e={'id':'Q1','type':'item','labels':{'en':{'value':'X'}},'aliases':{},'descriptions':{},'claims':{'P19':[{'rank':'normal','mainsnak':{'datatype':'wikibase-item','snaktype':'value','datavalue':{'type':'wikibase-entityid','value':{'id':'Q60'}}}}], 'P569':[{'rank':'normal','mainsnak':{'datatype':'time','snaktype':'value','datavalue':{'type':'time','value':{'time':'+1900-01-01T00:00:00Z','precision':9}}}}]}}
    ent,n,p,edges,c=process_entity(e,['en'])
    assert any(x[1]==19 for x in p); assert edges[0][2]==encode_wid('Q60'); assert c[0][2]==1900
