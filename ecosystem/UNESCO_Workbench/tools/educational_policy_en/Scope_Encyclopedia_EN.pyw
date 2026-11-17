"""Windows GUI for preparing the private Educational Policy candidate."""
import sys,threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk,messagebox
sys.path.insert(0,str(Path(__file__).resolve().parent))
from prepare import SOURCE, OUTPUT, KRISTALIZER, INDEX, validate, produce

root=tk.Tk();root.title('EncyKlopedia — Scope EN / Educational policy');root.geometry('820x490')
body=ttk.Frame(root,padding=16);body.pack(fill='both',expand=True)
ttk.Label(body,text='Educational policy — encyclopedic scope (English)',font=('Segoe UI',14,'bold')).pack(anchor='w')
for label,path in [('Source',SOURCE),('Candidate output',OUTPUT),('Kristalizer',KRISTALIZER),('Wikidata index (optional)',INDEX)]:
 ttk.Label(body,text=f'{label}: {path}',wraplength=780).pack(anchor='w',pady=3)
view=tk.Text(body,height=13,wrap='word');view.pack(fill='both',expand=True,pady=(12,8))
controls=ttk.Frame(body);controls.pack(anchor='w')
buttons=[]
def message(text):
 root.after(0,lambda s=text:(view.insert('end',s+'\n'),view.see('end')))
def start(fn):
 for b in buttons:b.configure(state='disabled')
 def task():
  try:fn()
  except Exception as e:
   message('ERROR: '+str(e))
   root.after(0,lambda detail=str(e):messagebox.showerror('Scope EN',detail))
  finally:root.after(0,lambda:[b.configure(state='normal') for b in buttons])
 threading.Thread(target=task,daemon=True).start()
def check():
 c,scope,params=validate(SOURCE)
 message(f'OK: {len(c)} concepts; 9 editorial facets; {params["kristalizer"]["max_results_per_label"]} matches/label')
 message('Kristalizer present: '+str(KRISTALIZER.is_file()))
 message('SQLite index present: '+str(INDEX.is_file()))
def create():
 archive,report=produce(log=message)
 message('ZIP READY: '+str(archive))
 root.after(0,lambda:messagebox.showinfo('Scope EN',str(archive)))
for label,fn in [('1. Vérifier sans modifier',check),('2. Préparer + scanner avec Kristalizer',create)]:
 b=ttk.Button(controls,text=label,command=lambda f=fn:start(f));b.pack(side='left',padx=(0,12));buttons.append(b)
message('This never modifies the original UNESCO Kristal or publishes anything.')
root.mainloop()
