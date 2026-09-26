"""Match a detected plate against the active watchlist, tolerant of OCR errors."""
import re, difflib
from .models import Watchlist

import os
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.82"))

def norm_plate(s):
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())

def find_match(plate, db, threshold=MATCH_THRESHOLD):
    """
    Return (watchlist_entry, score) for the best match >= threshold, else None.
    Uses similarity ratio so 'MD7078644' still matches watchlist 'MH7078644'.
    """
    plate = norm_plate(plate)
    if not plate:
        return None
    best, best_score = None, 0.0
    for w in db.query(Watchlist).filter(Watchlist.active == True).all():  # noqa: E712
        wp = norm_plate(w.plate_number)
        if not wp:
            continue
        if wp == plate:
            return w, 1.0                      # exact
        score = difflib.SequenceMatcher(None, wp, plate).ratio()
        if score > best_score:
            best, best_score = w, score
    if best and best_score >= threshold:
        return best, best_score
    return None