
from __future__ import annotations
from typing import List
import numpy as np
from .utils import pretty_mat, dump_json, save_csv_bundle

def print_header(title: str):
    print("\n" + title)
    print("=" * len(title))

def show_matrix_block(Ahat, Bhat, Chat, Dhat, pretty: bool):
    if not pretty:
        return
    if Ahat is not None: print("A^:\n" + pretty_mat(Ahat))
    if Bhat is not None: print("B^:\n" + pretty_mat(Bhat))
    if Chat is not None: print("C^:\n" + pretty_mat(Chat))
    if Dhat is not None: print("D^:\n" + pretty_mat(Dhat))

def export_bundle(name: str, T, Ahat, Bhat, Chat, Dhat, save_json: bool, save_csv: bool):
    if save_json:
        dump_json({
            "name": name,
            "T": T, "Ahat": Ahat, "Bhat": Bhat, "Chat": Chat, "Dhat": Dhat
        }, name)
    if save_csv:
        mats = {"T": T, "Ahat": Ahat, "Bhat": Bhat, "Chat": Chat, "Dhat": Dhat}
        export_name = name
        save_csv_bundle(mats, export_name)
