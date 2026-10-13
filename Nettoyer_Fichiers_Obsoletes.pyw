# -*- coding: utf-8 -*-
"""Nettoyage local EncyK. Une action destructive ne part jamais au démarrage."""
from pathlib import Path
import importlib.util
import tkinter as tk
from tkinter import ttk,messagebox

ROOT=Path(__file__).resolve().parent
MODULE=ROOT/'00_system/tools/migration/cleanup.py'
MANIFEST=ROOT/'00_system/tools/migration/obsolete-files.json'
spec=importlib.util.spec_from_file_location('encyk_cleanup',MODULE)
cleanup=importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)

class App:
    def __init__(self,window):
        self.window=window;window.title('EncyK — Nettoyage local contrôlé');window.geometry('870x500')
        self.data=[]
        frame=ttk.Frame(window,padding=16);frame.pack(fill='both',expand=True)
        ttk.Label(frame,text='Nettoyage après migration',font=('Segoe UI',17,'bold')).pack(anchor='w')
        ttk.Label(frame,text='Aucun fichier n’est supprimé automatiquement. Seuls les chemins et SHA-256 du manifeste sont acceptés.',wraplength=820).pack(anchor='w',pady=(7,12))
        ttk.Label(frame,text='Racine : '+str(ROOT)).pack(anchor='w')
        ttk.Label(frame,text='Manifeste : '+str(MANIFEST)).pack(anchor='w',pady=(0,8))
        cols=('path','status','reason')
        self.tree=ttk.Treeview(frame,columns=cols,show='headings',selectmode='extended')
        for col,width in [('path',325),('status',155),('reason',300)]:self.tree.heading(col,text=col);self.tree.column(col,width=width)
        self.tree.pack(fill='both',expand=True,pady=8)
        self.info=tk.StringVar()
        ttk.Label(frame,textvariable=self.info,wraplength=820).pack(anchor='w',pady=7)
        buttons=ttk.Frame(frame);buttons.pack(fill='x')
        ttk.Button(buttons,text='Vérifier les fichiers',command=self.refresh).pack(side='left')
        self.rm=ttk.Button(buttons,text='Supprimer les éléments sélectionnés…',command=self.remove)
        self.rm.pack(side='right')
        self.refresh()
    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        try:self.data=cleanup.candidates(ROOT,MANIFEST)
        except Exception as exc:
            self.data=[];messagebox.showerror('Manifeste invalide',str(exc));return
        for i,item in enumerate(self.data):self.tree.insert('','end',iid=str(i),values=(item['path'],item['status'],item['reason']))
        eligible=sum(x['status']=='eligible' for x in self.data)
        self.info.set(('Aucun fichier obsolète à supprimer dans ce snapshot.' if not self.data else f'{eligible} fichier(s) admissible(s). Les autres sont conservés.') + ' Les dépôts externes ne sont pas touchés.')
        self.rm.configure(state='normal' if eligible else 'disabled')
    def remove(self):
        chosen=[self.data[int(i)] for i in self.tree.selection()]
        if not chosen:
            messagebox.showinfo('Sélection requise','Sélectionnez d’abord les fichiers admissibles.');return
        if any(x['status']!='eligible' for x in chosen):
            messagebox.showerror('Refus','Un fichier sélectionné est modifié, absent ou non sûr.');return
        names='\n'.join('• '+x['path'] for x in chosen)
        if not messagebox.askyesno('Confirmation de suppression',f'Supprimer définitivement {len(chosen)} fichier(s) locaux ?\n\n{names}\n\nCette action ne peut pas être annulée.'):
            return
        prompt=tk.Toplevel(self.window);prompt.title('Confirmation explicite');prompt.transient(self.window);prompt.grab_set();prompt.resizable(False,False)
        ttk.Label(prompt,text='Tapez SUPPRIMER pour confirmer :',padding=10).pack()
        value=ttk.Entry(prompt,width=30);value.pack(padx=16,pady=8);value.focus_set()
        def confirm():
            if value.get()!='SUPPRIMER':messagebox.showerror('Confirmation','Texte incorrect.',parent=prompt);return
            prompt.destroy()
            try:
                removed=cleanup.delete_selected(ROOT,MANIFEST,[x['path'] for x in chosen]);messagebox.showinfo('Terminé',f'{len(removed)} fichier(s) supprimé(s).')
            except Exception as exc:messagebox.showerror('Suppression annulée',str(exc))
            self.refresh()
        ttk.Button(prompt,text='Confirmer',command=confirm).pack(pady=12)

def main():
    root=tk.Tk();App(root);root.mainloop()
if __name__=='__main__':main()
