import tkinter as tk
from tkinter import ttk, messagebox
import random
import string
import pyperclip  # pip install pyperclip

# ─────────────────────────────────────────
#  THEME CONSTANTS
# ─────────────────────────────────────────
BG        = "#0d0f14"
CARD      = "#161b25"
ACCENT    = "#00e5ff"
ACCENT2   = "#7b61ff"
TEXT      = "#e8eaf6"
MUTED     = "#5c6380"
SUCCESS   = "#00e676"
DANGER    = "#ff5252"
FONT_HEAD = ("Courier New", 22, "bold")
FONT_SUB  = ("Courier New", 10)
FONT_BODY = ("Courier New", 12)
FONT_PASS = ("Courier New", 15, "bold")


# ─────────────────────────────────────────
#  STRENGTH ANALYSER
# ─────────────────────────────────────────
def analyse_strength(pwd: str) -> tuple[str, str]:
    score = 0
    if len(pwd) >= 8:  score += 1
    if len(pwd) >= 14: score += 1
    if any(c.isupper() for c in pwd): score += 1
    if any(c.islower() for c in pwd): score += 1
    if any(c.isdigit() for c in pwd): score += 1
    if any(c in string.punctuation for c in pwd): score += 1

    if score <= 2:   return "WEAK",   DANGER
    if score <= 4:   return "FAIR",   "#ffab40"
    if score == 5:   return "STRONG", SUCCESS
    return "VERY STRONG", ACCENT


# ─────────────────────────────────────────
#  PASSWORD GENERATOR LOGIC
# ─────────────────────────────────────────
def generate_password(length: int, use_upper: bool, use_digits: bool,
                      use_symbols: bool, exclude_ambiguous: bool) -> str:
    chars = string.ascii_lowercase
    if use_upper:   chars += string.ascii_uppercase
    if use_digits:  chars += string.digits
    if use_symbols: chars += string.punctuation

    if exclude_ambiguous:
        ambiguous = "Il1O0o|`\\"
        chars = "".join(c for c in chars if c not in ambiguous)

    if not chars:
        return ""

    # Guarantee at least one character from each chosen category
    required = [random.choice(string.ascii_lowercase)]
    if use_upper:   required.append(random.choice(string.ascii_uppercase))
    if use_digits:  required.append(random.choice(string.digits))
    if use_symbols: required.append(random.choice(string.punctuation))

    remaining = [random.choice(chars) for _ in range(length - len(required))]
    password  = required + remaining
    random.shuffle(password)
    return "".join(password)


# ─────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────
class PasswordGeneratorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("// PASSGEN //")
        self.resizable(False, False)
        self.configure(bg=BG)

        # State
        self.length_var      = tk.IntVar(value=16)
        self.upper_var       = tk.BooleanVar(value=True)
        self.digits_var      = tk.BooleanVar(value=True)
        self.symbols_var     = tk.BooleanVar(value=True)
        self.ambiguous_var   = tk.BooleanVar(value=False)
        self.password_var    = tk.StringVar(value="")
        self.history: list[str] = []

        self._build_ui()
        self._generate()          # show a password on startup

    # ── UI CONSTRUCTION ──────────────────
    def _build_ui(self):
        pad = dict(padx=24, pady=10)

        # ── HEADER ──
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(24, 0))
        tk.Label(header, text="// PASSGEN //", font=FONT_HEAD,
                 fg=ACCENT, bg=BG).pack(side="left")
        tk.Label(header, text="v1.0", font=FONT_SUB,
                 fg=MUTED, bg=BG).pack(side="left", padx=8, pady=4)

        tk.Label(self, text="Cryptographically strong password generator",
                 font=FONT_SUB, fg=MUTED, bg=BG).pack(anchor="w", padx=24)

        self._divider()

        # ── PASSWORD DISPLAY CARD ──
        card = tk.Frame(self, bg=CARD, bd=0, relief="flat")
        card.pack(fill="x", padx=24, pady=(0, 4))

        inner = tk.Frame(card, bg=CARD)
        inner.pack(fill="x", padx=16, pady=14)

        self.pass_label = tk.Label(
            inner, textvariable=self.password_var,
            font=FONT_PASS, fg=ACCENT, bg=CARD,
            wraplength=440, justify="center", cursor="hand2"
        )
        self.pass_label.pack()
        self.pass_label.bind("<Button-1>", lambda e: self._copy())

        # Strength bar row
        bar_row = tk.Frame(card, bg=CARD)
        bar_row.pack(fill="x", padx=16, pady=(0, 10))

        self.strength_label = tk.Label(bar_row, text="", font=FONT_SUB,
                                       fg=SUCCESS, bg=CARD)
        self.strength_label.pack(side="left")

        self.char_count_label = tk.Label(bar_row, text="", font=FONT_SUB,
                                         fg=MUTED, bg=CARD)
        self.char_count_label.pack(side="right")

        # Canvas strength bar
        self.bar_canvas = tk.Canvas(card, height=4, bg=MUTED,
                                    highlightthickness=0)
        self.bar_canvas.pack(fill="x", padx=16, pady=(0, 14))

        self._divider()

        # ── CONTROLS ──
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", **pad)

        # Length slider
        tk.Label(ctrl, text="LENGTH", font=FONT_SUB,
                 fg=MUTED, bg=BG).grid(row=0, column=0, sticky="w")
        self.len_val_lbl = tk.Label(ctrl, text="16", font=FONT_BODY,
                                    fg=ACCENT, bg=BG, width=3)
        self.len_val_lbl.grid(row=0, column=2, sticky="e")

        slider = tk.Scale(
            ctrl, from_=4, to=64, orient="horizontal",
            variable=self.length_var, command=self._on_slider,
            bg=BG, fg=TEXT, troughcolor=CARD, activebackground=ACCENT,
            highlightthickness=0, bd=0, showvalue=False, length=340
        )
        slider.grid(row=0, column=1, padx=8)

        # Checkboxes
        checks_frame = tk.Frame(self, bg=BG)
        checks_frame.pack(fill="x", padx=24, pady=4)

        opts = [
            ("Uppercase  A–Z",  self.upper_var),
            ("Digits     0–9",  self.digits_var),
            ("Symbols    !@#$", self.symbols_var),
            ("Exclude ambiguous (0 O l 1)", self.ambiguous_var),
        ]
        for i, (label, var) in enumerate(opts):
            cb = tk.Checkbutton(
                checks_frame, text=label, variable=var,
                font=FONT_SUB, fg=TEXT, bg=BG,
                activebackground=BG, activeforeground=ACCENT,
                selectcolor=CARD, command=self._generate,
                cursor="hand2"
            )
            cb.grid(row=i // 2, column=i % 2, sticky="w", padx=8, pady=3)

        self._divider()

        # ── BUTTONS ──
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=24, pady=10)

        self._btn(btn_row, "⟳  GENERATE", self._generate,
                  ACCENT, BG).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "⎘  COPY", self._copy,
                  ACCENT2, BG).pack(side="left", padx=(0, 8))
        self._btn(btn_row, "⊞  HISTORY", self._show_history,
                  MUTED, BG).pack(side="right")

        # ── STATUS BAR ──
        self.status = tk.Label(self, text="", font=FONT_SUB,
                               fg=SUCCESS, bg=BG)
        self.status.pack(pady=(0, 16))

    def _divider(self):
        tk.Frame(self, bg=MUTED, height=1).pack(fill="x", padx=24, pady=6)

    @staticmethod
    def _btn(parent, text, cmd, fg, bg):
        return tk.Button(
            parent, text=text, command=cmd,
            font=FONT_SUB, fg=fg, bg=CARD,
            activebackground=CARD, activeforeground=fg,
            relief="flat", bd=0, padx=14, pady=8,
            cursor="hand2"
        )

    # ── ACTIONS ─────────────────────────
    def _on_slider(self, val):
        self.len_val_lbl.config(text=val)
        self._generate()

    def _generate(self, *_):
        pwd = generate_password(
            length          = self.length_var.get(),
            use_upper       = self.upper_var.get(),
            use_digits      = self.digits_var.get(),
            use_symbols     = self.symbols_var.get(),
            exclude_ambiguous = self.ambiguous_var.get(),
        )
        if not pwd:
            self.password_var.set("Select at least one option")
            return

        self.password_var.set(pwd)
        self.history.append(pwd)
        self._update_strength(pwd)
        self.status.config(text="")

    def _update_strength(self, pwd: str):
        label, color = analyse_strength(pwd)
        self.strength_label.config(text=f"● {label}", fg=color)
        self.char_count_label.config(text=f"{len(pwd)} chars")

        # Draw bar
        self.bar_canvas.update_idletasks()
        w = self.bar_canvas.winfo_width()
        score_map = {"WEAK": 0.2, "FAIR": 0.5, "STRONG": 0.8, "VERY STRONG": 1.0}
        ratio = score_map.get(label, 0.5)
        self.bar_canvas.delete("all")
        self.bar_canvas.create_rectangle(0, 0, int(w * ratio), 4,
                                         fill=color, outline="")

    def _copy(self):
        pwd = self.password_var.get()
        if not pwd or pwd == "Select at least one option":
            return
        try:
            pyperclip.copy(pwd)
            self.status.config(text="✔  Copied to clipboard!", fg=SUCCESS)
        except Exception:
            self.clipboard_clear()
            self.clipboard_append(pwd)
            self.status.config(text="✔  Copied to clipboard!", fg=SUCCESS)
        self.after(2000, lambda: self.status.config(text=""))

    def _show_history(self):
        if not self.history:
            messagebox.showinfo("History", "No passwords generated yet.")
            return

        win = tk.Toplevel(self)
        win.title("Password History")
        win.configure(bg=BG)
        win.resizable(False, False)

        tk.Label(win, text="HISTORY", font=FONT_HEAD,
                 fg=ACCENT2, bg=BG).pack(padx=20, pady=(16, 4))

        frame = tk.Frame(win, bg=BG)
        frame.pack(padx=20, pady=10)

        for i, p in enumerate(reversed(self.history[-10:]), 1):
            tk.Label(frame, text=f"{i:02d}.  {p}", font=FONT_SUB,
                     fg=TEXT, bg=BG, anchor="w").pack(anchor="w", pady=2)

        self._btn(win, "✕  CLOSE", win.destroy, MUTED, BG).pack(pady=(4, 16))


# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────
if __name__ == "__main__":
    app = PasswordGeneratorApp()
    app.mainloop()
