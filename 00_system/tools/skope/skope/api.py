"""Local-only HTTP server for Skope. Never binds publicly unless explicitly configured."""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs,urlparse
import json
import mimetypes
import os
from contextlib import closing
from .db import connect,meta,find,node
from .scope import branches_for_root,explore,validate_recipe
from .export import bundle
from . import massive,extraction
DEFAULT_PORT=8767

STATIC=Path(__file__).parent/'static'

class App(BaseHTTPRequestHandler):
    db_path=None
    starting_recipe=None
    arketype_guidance=None
    target_kristal=None
    def send_data(self,code,data,ctype='application/json; charset=utf-8',headers=None):
        if not isinstance(data,bytes):data=json.dumps(data,ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type',ctype)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for k,v in (headers or {}).items():self.send_header(k,v)
        self.end_headers();self.wfile.write(data)
    def _check_host(self):
        host=self.headers.get('Host','').split(':')[0].strip('[]').lower()
        return host in ('127.0.0.1','localhost','::1')
    def send_file(self,path,filename):
        self.send_response(200)
        self.send_header('Content-Type','application/zip')
        self.send_header('Content-Disposition','attachment; filename="'+filename+'"')
        self.send_header('Content-Length',str(path.stat().st_size))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.end_headers()
        with path.open('rb') as stream:
            while True:
                buf=stream.read(256*1024)
                if not buf:break
                self.wfile.write(buf)
    def _check_origin(self):
        origin=self.headers.get('Origin','')
        if not origin:return True  # Python CLI and other non-browser local callers
        try:
            parsed=urlparse(origin)
            return (parsed.scheme=='http' and parsed.hostname in ('127.0.0.1','localhost','::1')
                    and parsed.port==self.server.server_port)
        except ValueError:
            return False
    def do_GET(self):
        if not self._check_host():return self.send_data(403,{'error':'loopback_host_required'})
        route=urlparse(self.path);args=parse_qs(route.query)
        try:
            if route.path.startswith('/api/'):
                if route.path=='/api/extract/profiles':
                    return self.send_data(200,extraction.profiles())
                if route.path=='/api/extract/latest':
                    return self.send_data(200,extraction.latest(self.db_path))
                if route.path=='/api/extract/status':
                    return self.send_data(200,extraction.status(self.db_path,args.get('job',[''])[0]))
                if route.path=='/api/large/result.zip':
                    job=args.get('job',[''])[0]
                    result=massive.prepare_result_zip(self.db_path,job)
                    return self.send_file(result,'skope-'+job[:8]+'-results.zip')
                if route.path=='/api/large/latest':
                    return self.send_data(200,massive.latest(self.db_path))
                if route.path=='/api/large/status':
                    return self.send_data(200,massive.status(self.db_path,args.get('job',[''])[0]))
                with closing(connect(self.db_path,readonly=True)) as db:
                    if route.path=='/api/meta':out=meta(db)
                    elif route.path=='/api/config':out={'recipe':self.starting_recipe,'profile':'skope.encyk-startup/1.0','guidance':self.arketype_guidance,'target_kristal':self.target_kristal}
                    elif route.path=='/api/search':out=find(db,args.get('q',[''])[0],15)
                    elif route.path=='/api/node':out=node(db,args.get('qid',[''])[0])
                    elif route.path=='/api/branches':out=branches_for_root(db,args.get('root',[''])[0],args.get('direction',['both'])[0],set(args.get('pid',[])) or None)
                    else:return self.send_data(404,{'error':'not_found'})
                return self.send_data(200,out)
            page='/index.html' if route.path=='/' else route.path
            # fixed whitelist, no arbitrary filesystem navigation
            if page not in ('/index.html','/app.js','/style.css','/wizard.js','/wizard.css','/results.js','/results.css','/extraction.js','/extraction.css'):return self.send_data(404,{'error':'not_found'})
            path=STATIC/page[1:]
            return self.send_data(200,path.read_bytes(),mimetypes.guess_type(path)[0] or 'application/octet-stream')
        except (ValueError,TypeError) as e:self.send_data(400,{'error':str(e)})
        except Exception as e:self.send_data(500,{'error':type(e).__name__})
    def do_POST(self):
        if not self._check_host() or not self._check_origin():return self.send_data(403,{'error':'same_origin_required'})
        route=urlparse(self.path).path
        if route not in ('/api/preview','/api/export','/api/large/start','/api/large/pause','/api/large/open','/api/large/copy','/api/extract/preflight','/api/extract/start','/api/extract/pause','/api/extract/open'):return self.send_data(404,{'error':'not_found'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if length<=0 or length>65536:return self.send_data(413,{'error':'payload_too_large_or_empty'})
            data=json.loads(self.rfile.read(length))
            if route=='/api/extract/preflight':return self.send_data(200,extraction.preflight(self.db_path,data.get('profile'),data.get('source_job')))
            if route=='/api/extract/start':return self.send_data(200,extraction.start(self.db_path,data.get('profile'),data.get('source_job'),data.get('resume'),data.get('confirmed')))
            if route=='/api/extract/pause':return self.send_data(200,extraction.pause(self.db_path,data.get('job')))
            if route=='/api/extract/open':return self.send_data(200,extraction.open_results(self.db_path,data.get('job')))
            if route=='/api/large/open':return self.send_data(200,massive.open_results_folder(self.db_path,data.get('job')))
            if route=='/api/large/copy':return self.send_data(200,massive.copy_zip_to_windows_clipboard(self.db_path,data.get('job')))
            if route=='/api/large/start':return self.send_data(200,massive.start(self.db_path,data.get('recipe'),data.get('resume')))
            if route=='/api/large/pause':return self.send_data(200,massive.pause(self.db_path,data.get('job')))
            with closing(connect(self.db_path,readonly=True)) as db:
                if route=='/api/preview':out=explore(db,data);return self.send_data(200,out)
                out=bundle(db,data,guidance=self.arketype_guidance,target=self.target_kristal)
                return self.send_data(200,out,'application/zip',{'Content-Disposition':'attachment; filename="skope-working.zip"'})
        except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:self.send_data(400,{'error':str(e)})
        except Exception as e:self.send_data(500,{'error':type(e).__name__})
    def log_message(self,format,*args):pass

def serve(db_path,host='127.0.0.1',port=DEFAULT_PORT,recipe_path=None,guidance_path=None,kristal_path=None):
    if host not in ('127.0.0.1','localhost','::1'):
        raise ValueError('Integrated Skope only accepts loopback connections')
    from .arketype import load_guidance
    guidance=load_guidance(guidance_path)
    from .project import read_kristal,safe_target,seed_search
    target=safe_target(read_kristal(kristal_path)) if kristal_path else None
    db=Path(db_path)
    if not db.is_file():raise FileNotFoundError(f'Missing index: {db}. Build and finalize the global compact index with EncyK Wikidata Manager.')
    starting_recipe=None
    if recipe_path:
        starting_recipe=validate_recipe(json.loads(Path(recipe_path).read_text(encoding='utf-8')))
    with closing(connect(db,readonly=True)) as check:
        meta(check)
    cls=type('SkopeApp',(App,),{'db_path':str(db),'starting_recipe':starting_recipe,'arketype_guidance':guidance,'target_kristal':target})
    server=ThreadingHTTPServer((host,port),cls)
    print(f'Skope: http://{host}:{port} | SQLite: {db}',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
