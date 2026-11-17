# -*- coding: utf-8 -*-
"""Nettoyage local, volontaire et limité aux index du snapshot précédent.

Double-cliquer sur ce fichier à la racine du dépôt (Python + tkinter requis).
Rien n'est supprimé au lancement. Aucun dossier ni fichier modifié n'est effacé.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

ROOT = Path(__file__).resolve().parent
# Empreintes du snapshot fourni le 13 octobre 2026. Ne pas élargir cette liste
# à des artefacts canoniques, exemples, secrets ou fichiers utilisateur.
OLD_FILES = {
    "SMARTDUMP_INDEX.txt": "782d00eccbe4f21ad54c01b75ccd51762ec663ab3a946c1d7b62806a755afefc",
    "SNAPSHOT_INDEX.txt": "db7d24e70c34b7b9b794fb7776e85f5aea9dd6d026a7400034357a7e51c0317b",
}


def _candidate(name: str) -> Path | None:
    if name not in OLD_FILES or Path(name).name != name:
        return None
    path = ROOT / name
    # Interdire les liens symboliques, y compris en cas de remplacement local.
    if path.is_symlink() or not path.parent.resolve() == ROOT:
        return None
    return path


def status(name: str) -> str:
    path = _candidate(name)
    if path is None:
        return "Chemin refusé"
    if not path.exists():
        return "Absent — aucune action"
    if not path.is_file():
        return "Pas un fichier — protégé"
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return "Ancien index vérifié — supprimable" if digest == OLD_FILES[name] else "Fichier modifié — protégé"


def delete_matching(names: list[str]) -> tuple[list[str], list[str]]:
    """Supprime uniquement les index dont les SHA-256 correspondent à l'archive.

    N'est appelé qu'après une action explicite de la fenêtre. Ne supprime jamais
    les répertoires et ne se comporte pas comme un nettoyeur générique.
    """
    deleted, refused = [], []
    for name in dict.fromkeys(names):
        path = _candidate(name)
        if path is None or status(name) != "Ancien index vérifié — supprimable":
            refused.append(name)
            continue
        try:
            # Revalider immédiatement avant la suppression.
            if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != OLD_FILES[name]:
                refused.append(name)
                continue
            path.unlink()
            deleted.append(name)
        except OSError:
            refused.append(name)
    return deleted, refused


def main() -> None:
    window = tk.Tk()
    window.title("Authoring Kit — Nettoyage local contrôlé")
    window.geometry("750x355")
    window.minsize(650, 330)
    frame = ttk.Frame(window, padding=18)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Retrait des anciens index de snapshot", font=("Segoe UI", 14, "bold")).pack(anchor="w")
    ttk.Label(frame, text="Dossier local : " + str(ROOT), wraplength=700).pack(anchor="w", pady=(5, 8))
    ttk.Label(frame, text="Rien n'est supprimé automatiquement. Les fichiers personnels, exemples et sources canoniques sont exclus.", wraplength=700).pack(anchor="w")
    rows: dict[str, tuple[tk.BooleanVar, ttk.Checkbutton, ttk.Label]] = {}
    holder = ttk.Frame(frame)
    holder.pack(fill="x", pady=15)
    for name in OLD_FILES:
        sub = ttk.Frame(holder)
        sub.pack(fill="x", pady=4)
        chosen = tk.BooleanVar(value=False)
        cb = ttk.Checkbutton(sub, text=name, variable=chosen)
        cb.pack(side="left", padx=(0, 20))
        state = ttk.Label(sub, text="", foreground="#374151")
        state.pack(side="left")
        rows[name] = chosen, cb, state

    def refresh():
        for name, (chosen, cb, label) in rows.items():
            current = status(name)
            label.configure(text=current)
            if current == "Ancien index vérifié — supprimable":
                cb.configure(state="normal")
            else:
                chosen.set(False)
                cb.configure(state="disabled")

    def confirm_delete():
        selected = [name for name, (chosen, _, _) in rows.items() if chosen.get()]
        if not selected:
            messagebox.showinfo("Aucune sélection", "Cochez un ancien index vérifié.", parent=window)
            return
        if not messagebox.askyesno("Suppression locale", "Supprimer définitivement ces fichiers locaux ?\n\n" + "\n".join(selected), parent=window):
            return
        answer = simpledialog.askstring("Confirmation", "Saisissez SUPPRIMER pour confirmer :", parent=window)
        if answer != "SUPPRIMER":
            messagebox.showinfo("Annulé", "Aucun fichier supprimé.", parent=window)
            return
        deleted, refused = delete_matching(selected)
        refresh()
        messagebox.showinfo("Résultat", f"Supprimés : {len(deleted)}\nNon supprimés : {len(refused)}" +
                            ("\n" + "\n".join(refused) if refused else ""), parent=window)

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="w", pady=(8, 3))
    ttk.Button(buttons, text="Actualiser", command=refresh).pack(side="left", padx=(0, 10))
    ttk.Button(buttons, text="Supprimer les fichiers sélectionnés", command=confirm_delete).pack(side="left")
    ttk.Label(frame, text="Les index absents ou modifiés ne sont jamais supprimés. L'outil ne contacte aucun service.", wraplength=700, foreground="#555555").pack(anchor="w", pady=(15, 0))
    refresh()
    window.mainloop()


if __name__ == "__main__":
    main()
