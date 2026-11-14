"""Presse-papiers Windows natif: CF_UNICODETEXT + CF_HDROP (pas de processus enfant).

Les deux formats sont publiés dans la même opération OpenClipboard/EmptyClipboard.
Ce module n'écrit ni sur disque ni dans la base EncyKlopedia.
"""
from __future__ import annotations
import ctypes
import os
from pathlib import Path
import struct
import time

CF_UNICODETEXT = 13
CF_HDROP = 15
GMEM_MOVEABLE = 0x0002

def clipboard_payloads(text: str, path: Path):
    file_path=str(Path(path).resolve())
    if '\x00' in text or '\x00' in file_path:
        raise ValueError('Caractere NUL interdit dans le presse-papiers')
    if not Path(file_path).is_file():
        raise FileNotFoundError('ZIP de transfert absent : '+file_path)
    text_raw=text.encode('utf-16le')+b'\x00\x00'
    # DROPFILES: DWORD pFiles=20, POINT(0,0), BOOL fNC=0, BOOL fWide=1.
    drop_raw=struct.pack('<IiiII',20,0,0,0,1)+(file_path+'\x00\x00').encode('utf-16le')
    return text_raw,drop_raw

def copy_text_and_file(text: str, path: Path):
    if os.name!='nt':raise OSError('Presse-papiers Windows uniquement')
    text_raw,drop_raw=clipboard_payloads(text,path)
    from ctypes import wintypes
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user.OpenClipboard.argtypes=[wintypes.HWND];user.OpenClipboard.restype=wintypes.BOOL
    user.EmptyClipboard.argtypes=[];user.EmptyClipboard.restype=wintypes.BOOL
    user.SetClipboardData.argtypes=[wintypes.UINT,wintypes.HANDLE]
    user.SetClipboardData.restype=wintypes.HANDLE
    user.CloseClipboard.argtypes=[];user.CloseClipboard.restype=wintypes.BOOL
    kernel.GlobalAlloc.argtypes=[wintypes.UINT,ctypes.c_size_t]
    kernel.GlobalAlloc.restype=wintypes.HGLOBAL
    kernel.GlobalLock.argtypes=[wintypes.HGLOBAL]
    kernel.GlobalLock.restype=ctypes.c_void_p
    kernel.GlobalUnlock.argtypes=[wintypes.HGLOBAL];kernel.GlobalUnlock.restype=wintypes.BOOL
    kernel.GlobalFree.argtypes=[wintypes.HGLOBAL];kernel.GlobalFree.restype=wintypes.HGLOBAL

    def allocate(raw):
        h=kernel.GlobalAlloc(GMEM_MOVEABLE,len(raw))
        if not h:raise OSError('Allocation presse-papiers impossible')
        ptr=kernel.GlobalLock(h)
        if not ptr:
            kernel.GlobalFree(h)
            raise OSError('Verrouillage presse-papiers impossible')
        ctypes.memmove(ptr,raw,len(raw))
        kernel.GlobalUnlock(h)
        return h

    h_text=allocate(text_raw)
    try:h_file=allocate(drop_raw)
    except Exception:
        kernel.GlobalFree(h_text)
        raise
    opened=False
    try:
        for _ in range(7):
            if user.OpenClipboard(None):opened=True;break
            time.sleep(0.07)
        if not opened:raise OSError('Presse-papiers Windows occupe')
        if not user.EmptyClipboard():raise OSError('Impossible de vider le presse-papiers')
        if not user.SetClipboardData(CF_UNICODETEXT,h_text):
            raise OSError('Impossible de copier le texte Unicode')
        h_text=None  # ownership transferred to the OS
        if not user.SetClipboardData(CF_HDROP,h_file):
            raise OSError('Impossible de copier la reference au fichier ZIP')
        h_file=None
    finally:
        if opened:user.CloseClipboard()
        if h_text is not None:kernel.GlobalFree(h_text)
        if h_file is not None:kernel.GlobalFree(h_file)
