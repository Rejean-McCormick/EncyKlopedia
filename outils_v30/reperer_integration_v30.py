#!/usr/bin/env python3
"""Localise les points de generation v28 dans le depot. Lecture seule, pas de patch aveugle."""
import argparse,datetime,re,os,sys
from pathlib import Path
PATTERNS=[re.compile(x,re.I) for x in (r'REVUE_v28',r'PROMPT_CHATGPT',r'INSTRUCTIONS_CHATGPT',r'CONTEXTES_DOCUMENTAIRES',r'DECOUVERTE_ARTICLES_RELIES',r'candidate_id',r'export.*v28',r'gener.*batch',r'gener.*pack',r'priority.*sort',r'BATCH[_ ]?SIZE',r'PACK[_ ]?SIZE',r'max[_ ]?candidate',r'taille[_ ]?lot',r'taille[_ ]?pack',r'limit[_ ]?candidate',r'chunk[_ ]?size',r'\b110\b',r'\b300\b',r'proof.*froze',r'preuves.*fig',r'pending.*review')]
SKIP={'.git','node_modules','venv','.venv','__pycache__','OUTILS_PRIORISATION_STATS_V30','.idea','.vs','bin','obj','dist','.pytest_cache'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--sortie',type=Path,required=True);args=ap.parse_args()
    lines=['EncyKlopedia V30 — Recherche de points d integration (LECTURE SEULE)',f'Date: {datetime.datetime.now().isoformat(timespec="seconds")}',f'Depot: {args.repo}',
           'Ne modifie aucun code. Les extraits servent a preparer un patch compatible.', 'Taille cible du planificateur autonome : 300 (maximum configurable 500).', 'Le producteur NATIF reste inchangé sans vérification du code et des verrous de revues en cours.', '']
    seen=0; hits=0
    if not args.repo.is_dir():
        lines.append('Depot absent: verifier chemin.');args.sortie.write_text('\n'.join(lines)+'\n',encoding='utf-8-sig');return 0
    for root,dirs,files in os.walk(args.repo):
        dirs[:]=[x for x in dirs if x not in SKIP and not x.startswith('BACKUP_') and not x.startswith('.STAGING_') and not x.startswith('OUTILS_PRIORISATION_STATS_V30_SAUVEGARDE_')]
        for filename in files:
            if not filename.lower().endswith(('.py','.ps1')):continue
            path=Path(root)/filename
            if seen>=2500 or hits>=150:break
            seen+=1
            if path.stat().st_size>2_500_000:continue
            try:content=path.read_text(encoding='utf-8-sig',errors='replace').splitlines()
            except OSError:continue
            matches=[(i,line.strip()) for i,line in enumerate(content,1) if any(p.search(line) for p in PATTERNS)]
            if matches:
                hits+=1;lines.append(f'FICHIER : {path.relative_to(args.repo)} | lignes pertinentes: {len(matches)}')
                for i,line in matches[:15]:lines.append(f'  {i:05d}: {line[:250]}')
                if len(matches)>15:lines.append(f'  ... {len(matches)-15} correspondances supplementaires')
                lines.append('')
        if seen>=2500 or hits>=150:break
    lines.extend([f'Scripts examines: {seen}',f'Fichiers avec indices: {hits}', 'Note : un index de lignes ne suffit pas a justifier une modification automatique du producteur.'])
    args.sortie.parent.mkdir(parents=True,exist_ok=True)
    args.sortie.write_text('\n'.join(lines)+'\n',encoding='utf-8-sig')
    print('Points d insertion releves :',args.sortie)
    return 0
if __name__=='__main__':sys.exit(main())
