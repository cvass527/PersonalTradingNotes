import json
import os
from config import NOTES_FILE

class NoteManager:
    def load_notes(self, date_str):
        try:
            with open(NOTES_FILE, 'r') as f:
                return json.load(f).get(date_str, '')
        except FileNotFoundError:
            return ''
    
    def save_notes(self, date_str, note):
        notes = {}
        if os.path.exists(NOTES_FILE):
            with open(NOTES_FILE, 'r') as f:
                notes = json.load(f)
        notes[date_str] = note
        with open(NOTES_FILE, 'w') as f:
            json.dump(notes, f)
 