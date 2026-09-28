from pathlib import Path
import runpy
p=Path(__file__).resolve().parent/'00_system'/'tools'/'wikidata-manager'/'run_manager.pyw'
runpy.run_path(str(p),run_name='__main__')
