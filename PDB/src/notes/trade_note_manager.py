import json
import os
from config import PDB_DIR

class TradeNoteManager:
    def __init__(self):
        self.trade_notes_file = os.path.join(PDB_DIR, 'trade_notes.json')
        self.trade_colors_file = os.path.join(PDB_DIR, 'trade_colors.json')
    
    def generate_trade_id(self, date_str, contract, entry_time, exit_time):
        """Generate a unique trade ID based on trade details."""
        # Create a unique identifier using date, contract, and times
        return f"{date_str}_{contract}_{entry_time}_{exit_time}".replace(' ', '_').replace(':', '-')
    
    def load_trade_notes(self, date_str=None):
        """Load trade notes. If date_str provided, return only notes for that date."""
        try:
            with open(self.trade_notes_file, 'r') as f:
                all_notes = json.load(f)
            
            if date_str:
                # Filter notes for specific date
                return {k: v for k, v in all_notes.items() if k.startswith(f"{date_str}_")}
            return all_notes
        except FileNotFoundError:
            return {}
    
    def save_trade_note(self, trade_id, note):
        """Save a note for a specific trade."""
        # Load existing notes
        all_notes = self.load_trade_notes()
        
        # Update with new note
        all_notes[trade_id] = note
        
        # Save back to file
        with open(self.trade_notes_file, 'w') as f:
            json.dump(all_notes, f, indent=2)
    
    def get_trade_note(self, trade_id):
        """Get note for a specific trade."""
        all_notes = self.load_trade_notes()
        return all_notes.get(trade_id, '')
    
    def delete_trade_note(self, trade_id):
        """Delete a note for a specific trade."""
        all_notes = self.load_trade_notes()
        if trade_id in all_notes:
            del all_notes[trade_id]
            with open(self.trade_notes_file, 'w') as f:
                json.dump(all_notes, f, indent=2)
    
    def load_trade_colors(self, date_str=None):
        """Load trade colors. If date_str provided, return only colors for that date."""
        try:
            with open(self.trade_colors_file, 'r') as f:
                all_colors = json.load(f)
            
            if date_str:
                # Filter colors for specific date
                return {k: v for k, v in all_colors.items() if k.startswith(f"{date_str}_")}
            return all_colors
        except FileNotFoundError:
            return {}
    
    def save_trade_color(self, trade_id, color):
        """Save a color preference for a specific trade."""
        # Load existing colors
        all_colors = self.load_trade_colors()
        
        # Update with new color
        all_colors[trade_id] = color
        
        # Save back to file
        with open(self.trade_colors_file, 'w') as f:
            json.dump(all_colors, f, indent=2)
    
    def get_trade_color(self, trade_id):
        """Get color for a specific trade."""
        all_colors = self.load_trade_colors()
        return all_colors.get(trade_id, 'none')