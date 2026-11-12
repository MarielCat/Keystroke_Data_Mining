import argparse
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk
import pandas as pd
from ksd.data import MODIFIERS, events_to_keystrokes, load_raw, pair_events
from ksd.distance import DISTANCES
from ksd.identify import Identifier


ROOT = Path(__file__).parent.parent
MIN_KEYS = 20


def display_names(raw: pd.DataFrame) -> dict:
    """participant_id -> nicest spelling seen in the files."""

    def best(names):
        # Prefer names with their original accents and capitalization
        name = max(names.unique(), key=lambda n: (not n.isascii(), n[:1].isupper()))
        return name[:1].upper() + name[1:]
    return raw.groupby("participant_id")["name"].agg(best).to_dict()


class App:

    def __init__(self, root: tk.Tk, identifier: Identifier):
        self.root = root
        self.identifier = identifier
        self.events = []
        self.names = {}
        self.min_keys = MIN_KEYS
        root.title("Qui tape ? (keystroke dynamics)")
        root.geometry("760x620")
        root.minsize(560, 480)
        
        frm = ttk.Frame(root, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Qui est en train de taper ?", font=("Segoe UI", 16, "bold")).pack(anchor="w")

        ttk.Label(frm, wraplength=720, justify="left",
            text="Type anything you want below in English. Write at least 20 characters, then click “Who is typing?” (or press Ctrl+Enter). The program does not read what you write. It only looks at your typing rhythm."
        ).pack(anchor="w", pady=(2, 8))

        # Text area used to capture keyboard events
        self.text = tk.Text(frm, height=9, wrap="word", font=("Segoe UI", 12), undo=False)
        self.text.pack(fill="both", expand=True)

        self.text.bind("<KeyPress>", self.on_key, add="+")
        self.text.bind("<KeyRelease>", self.on_key, add="+")
        self.text.bind("<Control-Return>", lambda e: (self.identify(), "break")[1])

        # Pasted text has no real typing rhythm
        for seq in ("<<Paste>>", "<<Cut>>"):
            self.text.bind(seq, lambda e: "break")

        # Buttons and keystroke counter
        bar = ttk.Frame(frm)
        bar.pack(fill="x", pady=8)

        self.btn = ttk.Button(bar, text="Who's typing ?", command=self.identify, state="disabled")
        self.btn.pack(side="left")

        ttk.Button(bar, text="Erase", command=self.clear).pack(side="left", padx=6)

        self.counter = ttk.Label(bar, text="0 frappe")
        self.counter.pack(side="right")

        # Status and identification results
        self.status = ttk.Label(frm, text="Entraînement des modèles…", font=("Segoe UI", 10, "italic") )
        self.status.pack(anchor="w")

        self.verdict = ttk.Label(frm, text="", font=("Segoe UI", 18, "bold") )
        self.verdict.pack(anchor="w", pady=(6, 0))

        self.detail = ttk.Label(frm, text="", wraplength=720, justify="left")
        self.detail.pack(anchor="w")

        # Canvas used to display the scores
        self.canvas = tk.Canvas(frm, height=150, highlightthickness=0, bg=root.cget("bg"))
        self.canvas.pack(fill="x", pady=(6, 0))

        self.text.focus_set()


    def on_key(self, e):
        # Ignore shortcuts because they do not represent normal typing
        if e.state & 0x4 and e.keysym.lower() in ("return", "a", "z", "y", "c", "v", "x") :
            return

        if e.type == tk.EventType.KeyPress:
            typ = "keydown"
        else:
            typ = "keyup"

        # Store the event with its timestamp
        event = (typ, e.keysym, e.char, time.perf_counter_ns())
        self.events.append(event)

        if typ == "keydown":
            count = sum(event[0] == "keydown" for event in self.events)
            self.counter.config(text=f"{count} frappe{'s' * (count > 1)}")

    
    def clear(self):
        # Reset the input and all displayed results
        self.events.clear()

        self.text.delete("1.0", "end")
        self.counter.config(text="0 keystroke")

        self.verdict.config(text="")
        self.detail.config(text="")

        self.canvas.delete("all")
        self.text.focus_set()


    def ready(self, names: dict, n_keys: int):
        self.names = names
        idf = self.identifier

        model_names = ", ".join(names[user] for user in idf.models)

        self.status.config(
            text = f"Models are ready: {model_names} "
               f"({n_keys} training keystrokes, window size: {idf.n_keys}, "
               f"validation EER: {idf.eer:.0%})."
        )

        self.btn.config(state="normal")

    
    def identify(self):
        # Do not run identification before training is finished
        if str(self.btn["state"]) == "disabled":
            return

        if self.events:
            ks = events_to_keystrokes(self.events)
        else:
            ks = pd.DataFrame()

        # Count only regular text keys
        if len(ks):
            n_text = int(
                (~ks["key"].isin(MODIFIERS)).sum()
            )
        else:
            n_text = 0

        if n_text < self.min_keys:
            self.verdict.config(text="Not enough text")

            self.detail.config( text=f"{n_text} usable matches found. At least {self.min_keys} are required "
                                     f"(ideally {2 * self.identifier.n_keys} or more).")

            self.canvas.delete("all")
            return

        # Calculate the scores for all known participants
        scores = self.identifier.score(ks)

        scores = scores[pd.notna(scores) & (scores < float("inf"))]

        if scores.empty:
            self.verdict.config(text="Impossible to compare")
            self.detail.config(text="No matching keys or sequences found in the training data. Try an English text.")
            self.canvas.delete("all")
            return

        self.show(scores, n_text)

    
    def show(self, scores: pd.Series, n_text: int):
        # The participant with the lowest score is the best match
        best = scores.index[0]
        best_s = scores.iloc[0]

        if len(scores) > 1:
            margin = scores.iloc[1] / best_s
        else:
            margin = float("inf")

        # Estimate confidence based on the difference between the two best scores
        if margin > 1.3:
            conf = "high"
        elif margin > 1.1:
            conf = "medium"
        else:
            conf = "low"

        name = self.names.get(best, best)

        if best_s <= self.identifier.threshold:
            color = "#15803d"
        else:
            color = "#b45309"

        self.verdict.config(text=f"With the training, it is {name} who is typing.", foreground=color)

        # The threshold is only an indication because typing conditions can vary
        if best_s <= self.identifier.threshold:
            extra = (f"Score {best_s:.2f} is below or equal to the alert threshold of {self.identifier.threshold:.2f}.")
        
        else:
            extra = (
                f"Score {best_s:.2f} is above the alert threshold "
                f"of {self.identifier.threshold:.2f}: the typing rhythm is quite different "
                f"from {name}'s usual typing pattern (different keyboard, different type "
                f"of text, or someone not included in the training data)."
            )

        if n_text < 2 * self.identifier.n_keys:
            warn = (f" Warning: only {n_text} keystrokes found. The result may be unreliable (at least ~{2 * self.identifier.n_keys} are needed).")
        else:
            warn = ""
        
        self.detail.config(
            text=f"Confidence: {conf} (the 2nd closest result is {margin:.2f}× further away). {extra}{warn}\n"
                 f"Score per person: ~1 = typical typing rhythm for this person, higher = less similar."
        )

        self.draw_bars(scores)

    
    def draw_bars(self, scores: pd.Series):
        c = self.canvas
        c.delete("all")
        c.update_idletasks()

        width = max(c.winfo_width(), 400)
        row_height = 26

        c.config(height=row_height * len(scores) + 6)

        # Scale the bars relative to the best score
        lowest = scores.min()

        for i, (user, score) in enumerate(scores.items()):
            y = 4 + i * row_height
            bar_length = (width - 220) * lowest / score

            if i == 0:
                color = "#15803d"
            else:
                color = "#94a3b8"

            # Participant name
            c.create_text(4, y + 10, text=self.names.get(user, user), anchor="w", font=("Segoe UI", 11) )

            # Score bar
            c.create_rectangle(110, y, 110 + bar_length, y + 20, fill=color, width=0 )

            c.create_text(118 + bar_length, y + 10, text=f"{score:.2f}", anchor="w", font=("Segoe UI", 10) )


def main():
    # Read the command-line arguments
    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--window",
        type=int,
        default=50,
        help="keystrokes per window"
    )

    ap.add_argument(
        "--distance",
        default="l1",
        choices=list(DISTANCES)
    )

    ap.add_argument("--k", type=int, default=3)

    ap.add_argument(
        "--min-keys",
        type=int,
        default=MIN_KEYS,
        help="refuse shorter texts (e.g. 3 to try a single word)"
    )

    args = ap.parse_args()

    # Create the application and its identifier
    root = tk.Tk()

    identifier = Identifier(
        DISTANCES[args.distance],
        args.k,
        args.window
    )

    app = App(root, identifier)
    app.min_keys = args.min_keys

    result = {}

    
    def train():
        # Training runs in the background to keep the interface responsive
        try:
            dataset_folders = [folder for folder in sorted(ROOT.glob("Dataset_*")), if folder.is_dir() ]
            raw_data = [load_raw(folder) for folder in dataset_folders]
            raw = pd.concat(raw_data, ignore_index=True)
            ks = pair_events(raw)
            app.identifier.fit(ks)
            result["ok"] = (display_names(raw), len(ks) )

        except Exception as exc:
            result["error"] = exc

    
    def poll():
        # Update the interface when the training thread finishes
        if "ok" in result:
            app.ready(*result["ok"])

        elif "error" in result:
            app.status.config(text=f"Error during training : {result['error']}")

        else:
            root.after(200, poll)

    # Start training without blocking the main interface
    threading.Thread(target=train, daemon=True).start()
    poll()
    root.mainloop()


if __name__ == "__main__":
    main()
