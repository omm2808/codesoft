import tkinter as tk
import math, re, ctypes, platform


BG_TOP     = "#0a0015"
BG_MID     = "#050520"
BG_BOT     = "#000d0d"
ORB1       = "#7c3aed"
ORB2       = "#0ea5e9"
ORB3       = "#f43f5e"
PANEL_BG   = "#0d0d20"
DISP_BG    = "#07071a"
DISP_EDGE  = "#1e1b4b"
NUM_REST   = "#13132b"
NUM_EDGE   = "#2d2b6e"
NUM_GLOW   = "#4f46e5"
OP_REST    = "#160d30"
OP_EDGE    = "#4c1d95"
OP_GLOW    = "#7c3aed"
FN_REST    = "#0a1a28"
FN_EDGE    = "#0c4a6e"
FN_GLOW    = "#0ea5e9"
EQ_REST    = "#1a0a2e"
EQ_EDGE    = "#6d28d9"
EQ_GLOW    = "#a78bfa"
PRESS_LITE = "#ddd6fe"
PRESS_MID  = "#a78bfa"
TEXT_BRIGHT= "#f1f0ff"
TEXT_MED   = "#a5b4fc"
TEXT_DIM   = "#3d3d6b"
TEXT_OP    = "#c4b5fd"
TEXT_FN    = "#7dd3fc"
TEXT_EQ    = "#ede9fe"


def _apply_blur(hwnd):
    if platform.system() != "Windows":
        return
    try:
        build = int(platform.version().split(".")[2])
    except Exception:
        build = 0
    try:
        if build >= 22000:
            v = ctypes.c_int(3)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 38, ctypes.byref(v), ctypes.sizeof(v))
        else:
            class AP(ctypes.Structure):
                _fields_ = [("AccentState", ctypes.c_int),
                             ("AccentFlags", ctypes.c_int),
                             ("GradientColor", ctypes.c_int),
                             ("AnimationId", ctypes.c_int)]
            class WD(ctypes.Structure):
                _fields_ = [("Attribute", ctypes.c_int),
                             ("Data", ctypes.POINTER(ctypes.c_int)),
                             ("SizeOfData", ctypes.c_size_t)]
            ac = AP()
            ac.AccentState   = 4
            ac.GradientColor = 0xCC000018
            wd = WD()
            wd.Attribute  = 19
            wd.Data       = ctypes.cast(ctypes.byref(ac), ctypes.POINTER(ctypes.c_int))
            wd.SizeOfData = ctypes.sizeof(ac)
            ctypes.windll.user32.SetWindowCompositionAttribute(hwnd, ctypes.byref(wd))
    except Exception:
        pass


def _rgb(h):
    return int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)

def _mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    r1,g1,b1 = _rgb(c1);  r2,g2,b2 = _rgb(c2)
    return "#{:02x}{:02x}{:02x}".format(
        int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))

def _lerp3(c1, c2, c3, t):
    return _mix(c1, c2, t*2) if t < 0.5 else _mix(c2, c3, (t-0.5)*2)


class CalcEngine:
    def __init__(self):
        self.reset()

    def reset(self):
        self.expression     = ""
        self.display_text   = "0"
        self.last_answer    = 0
        self.just_evaluated = False

    def _safe_eval(self, expr):
        expr = (expr.replace("×","*").replace("÷","/").replace("^","**")
                    .replace("√(","math.sqrt(").replace("π",str(math.pi))
                    .replace("sin(","math.sin(math.radians(")
                    .replace("cos(","math.cos(math.radians(")
                    .replace("tan(","math.tan(math.radians(")
                    .replace("log(","math.log10(").replace("ln(","math.log(")
                    .replace("e", str(math.e)))
        expr += ")" * (expr.count("(") - expr.count(")"))
        safe  = re.sub(r"[^0-9\.\+\-\*\/\(\)\%\^mathsincotaglqre\. ]", "", expr)
        return eval(safe, {"__builtins__": {}}, vars(math))

    def append(self, token):
        if self.just_evaluated:
            if token not in "+-×÷^%":
                self.expression = ""
            self.just_evaluated = False
        self.expression  += token
        self.display_text = self.expression

    def backspace(self):
        self.just_evaluated = False
        self.expression     = self.expression[:-1]
        self.display_text   = self.expression if self.expression else "0"

    def evaluate(self):
        if not self.expression:
            return
        try:
            r = self._safe_eval(self.expression)
            if isinstance(r, float):
                r = int(r) if r.is_integer() else round(r, 10)
            self.last_answer    = r
            self.display_text   = str(r)
            self.expression     = str(r)
            self.just_evaluated = True
        except ZeroDivisionError:
            self.display_text = "Cannot ÷ zero"
            self.expression   = ""
        except Exception:
            self.display_text = "Syntax Error"
            self.expression   = ""

    def clear(self):
        self.reset()

    def toggle_sign(self):
        if self.expression.startswith("-"):
            self.expression = self.expression[1:]
        else:
            self.expression = "-" + self.expression
        self.display_text = self.expression

    def percent(self):
        try:
            v = self._safe_eval(self.expression) / 100
            self.expression = self.display_text = str(v)
        except Exception:
            pass


class AuroraButton(tk.Canvas):
    FRAMES = 12

    def __init__(self, parent, text, command,
                 rest=NUM_REST, edge=NUM_EDGE, glow=NUM_GLOW,
                 tcolor=TEXT_BRIGHT, width=76, height=60, **kw):
        super().__init__(parent, width=width, height=height,
                         bg=PANEL_BG, highlightthickness=0, **kw)
        self.text    = text
        self.command = command
        self.w, self.h = width, height
        self.rest  = rest
        self.edge  = edge
        self.glow  = glow
        self.tc    = tcolor
        self._step  = 0
        self._hover = False
        self._job   = None
        self._draw(0, False)
        self.bind("<Enter>",           self._on_enter)
        self.bind("<Leave>",           self._on_leave)
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _alive(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _rrect(self, x1, y1, x2, y2, r, **kw):
        p = [x1+r,y1, x2-r,y1, x2,y1, x2,y1+r,
             x2,y2-r, x2,y2, x2-r,y2, x1+r,y2,
             x1,y2, x1,y2-r, x1,y1+r, x1,y1, x1+r,y1]
        return self.create_polygon(p, smooth=True, **kw)

    def _draw(self, step, hover):
        if not self._alive():
            return
        try:
            self.delete("all")
            w, h = self.w, self.h
            r    = 16
            t    = step / self.FRAMES

            if step > 0:
                self._rrect(4, 4, w+2, h+2, r+2,
                             fill=_mix("#000000", self.glow, t*0.35), outline="")

            body   = _lerp3(self.rest, _mix(self.rest, self.glow, 0.4), PRESS_LITE, t)
            border = _lerp3(self.edge, self.glow, PRESS_MID, t)
            self._rrect(0, 0, w-3, h-3, r, fill=body,
                        outline=border, width=1+int(t*2))

            if hover and step == 0:
                self._rrect(0, 0, w-3, h-3, r, fill="",
                             outline=self.glow, width=1)

            if step > 0:
                shine = _mix(body, "#ffffff", t*0.55)
                self._rrect(6, 4, w-9, int(14+t*8), 8, fill=shine, outline="")
                rr = int(t * (w//2 + 10))
                cx, cy = (w-3)//2, (h-3)//2
                if rr > 0:
                    self.create_oval(cx-rr, cy-rr, cx+rr, cy+rr,
                                     outline=_mix(self.glow, PRESS_LITE, t),
                                     width=max(1, int((1-t)*3)))

            tc = _mix(self.tc, "#1a1040", t*0.5) if step > 0 else self.tc
            if hover and step == 0:
                tc = _mix(self.tc, "#ffffff", 0.3)
            fs = 18 if len(self.text)==1 else (14 if len(self.text)<=3 else 11)
            self.create_text((w-3)//2, (h-3)//2, text=self.text,
                             fill=tc, font=("Segoe UI", fs, "bold"))
        except tk.TclError:
            pass

    def _cancel(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None

    def _anim(self, target, speed):
        self._cancel()
        def tick():
            if not self._alive():
                return
            try:
                if self._step != target:
                    self._step += 1 if self._step < target else -1
                    self._draw(self._step, self._hover)
                    self._job = self.after(speed, tick)
                else:
                    self._draw(self._step, self._hover)
            except tk.TclError:
                pass
        tick()

    def _on_enter(self, _=None):
        self._hover = True
        if self._step == 0:
            self._draw(0, True)

    def _on_leave(self, _=None):
        self._hover = False
        self._anim(0, 18)

    def _on_press(self, _=None):
        self._hover = False
        self._anim(self.FRAMES, 12)

    def _on_release(self, _=None):
        if self.command:
            self.command()
        self._anim(0, 20)


class AuroraBackground(tk.Canvas):
    def __init__(self, parent, w, h, **kw):
        super().__init__(parent, width=w, height=h,
                         highlightthickness=0, **kw)
        self._w   = w
        self._h   = h
        self._t   = 0.0
        self._job = None
        self._orbs = [
            {"cx":0.20,"cy":0.18,"rx":210,"ry":185,"col":ORB1,"phase":0.0},
            {"cx":0.82,"cy":0.28,"rx":230,"ry":205,"col":ORB2,"phase":1.2},
            {"cx":0.50,"cy":0.76,"rx":250,"ry":185,"col":ORB3,"phase":2.4},
            {"cx":0.10,"cy":0.82,"rx":165,"ry":145,"col":ORB2,"phase":0.8},
            {"cx":0.88,"cy":0.68,"rx":175,"ry":155,"col":ORB1,"phase":2.0},
        ]
        self._paint()
        self._schedule()

    def _alive(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False

    def _paint(self):
        if not self._alive():
            return
        try:
            self.delete("all")
            w, h = self._w, self._h

            steps = 30
            for i in range(steps):
                t2  = i / steps
                col = _lerp3(BG_TOP, BG_MID, BG_BOT, t2)
                y1  = int(t2 * h)
                y2  = int((i+1)/steps * h)
                self.create_rectangle(0, y1, w, y2+2, fill=col, outline="")

            for orb in self._orbs:
                cx  = orb["cx"] + 0.06*math.sin(self._t*0.4 + orb["phase"])
                cy  = orb["cy"] + 0.04*math.cos(self._t*0.3 + orb["phase"])
                px  = int(cx * w)
                py  = int(cy * h)
                rx, ry = orb["rx"], orb["ry"]
                rc, gc, bc = _rgb(orb["col"])
                for k in range(18, 0, -1):
                    ratio = k / 18
                    a     = (1 - ratio) * 0.13
                    fr    = min(255, int(rc * a * 4.5))
                    fg    = min(255, int(gc * a * 4.5))
                    fb    = min(255, int(bc * a * 4.5))
                    self.create_oval(
                        px - int(rx*ratio), py - int(ry*ratio),
                        px + int(rx*ratio), py + int(ry*ratio),
                        fill="#{:02x}{:02x}{:02x}".format(fr,fg,fb),
                        outline="")
        except tk.TclError:
            pass

    def _schedule(self):
        if not self._alive():
            return
        try:
            self._t  += 0.04
            self._paint()
            self._job = self.after(55, self._schedule)
        except tk.TclError:
            pass

    def stop(self):
        if self._job:
            try:
                self.after_cancel(self._job)
            except Exception:
                pass
            self._job = None


class CalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.engine = CalcEngine()
        self.title("CALC")
        self.resizable(False, False)

        self._W, self._H = 440, 780
        self._mode = "basic"
        self._dx   = self._dy = 0

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self._W) // 2
        y  = (sh - self._H) // 2
        self.geometry(f"{self._W}x{self._H}+{x}+{y}")
        self.configure(bg=PANEL_BG)

        # Must update before overrideredirect so winfo_id() is valid
        self.update_idletasks()
        self.update()

        self.overrideredirect(True)
        self.wm_attributes("-alpha", 0.96)

        if platform.system() == "Windows":
            try:
                hwnd = self.winfo_id()
                _apply_blur(hwnd)
            except Exception:
                pass

        self._bg = None
        self._build()
        self.bind("<Key>", self._on_key)
        self.protocol("WM_DELETE_WINDOW", self._quit)

    def _quit(self):
        try:
            if self._bg:
                self._bg.stop()
        except Exception:
            pass
        self.destroy()

    def _build(self):
        W, H = self._W, self._H

        # ── Stop & destroy old background if rebuilding ──────────────────
        if self._bg is not None:
            try:
                self._bg.stop()
                self._bg.place_forget()
                self._bg.destroy()
            except Exception:
                pass

        # ── Create background canvas first ───────────────────────────────
        self._bg = AuroraBackground(self, W, H, bg=PANEL_BG)
        self._bg.place(x=0, y=0, width=W, height=H)
        # Lower it so all subsequent widgets appear on top
        self._bg.lower()

        # ── Main panel frame (transparent-ish, sits above background) ────
        panel = tk.Frame(self, bg=PANEL_BG)
        panel.place(x=14, y=14, width=W-28, height=H-28)

        # ── Title bar ────────────────────────────────────────────────────
        title_f = tk.Frame(panel, bg=PANEL_BG)
        title_f.pack(fill="x", pady=(6, 0), padx=4)
        title_f.bind("<ButtonPress-1>", self._ds)
        title_f.bind("<B1-Motion>",     self._dm)

        dot_f = tk.Frame(title_f, bg=PANEL_BG)
        dot_f.pack(side="left", padx=(2, 0))
        for color, action in [
            ("#ff5f57", self._quit),
            ("#ffbd2e", self.iconify),
            ("#28c840", None),
        ]:
            dot = tk.Canvas(dot_f, width=13, height=13,
                            bg=PANEL_BG, highlightthickness=0)
            dot.pack(side="left", padx=3, pady=6)
            dot.create_oval(1, 1, 12, 12, fill=color, outline="")
            if action:
                dot.bind("<Button-1>", lambda _, a=action: a())

        tk.Label(title_f, text="✦  AURORA CALC", bg=PANEL_BG,
                 fg=TEXT_MED, font=("Segoe UI", 10, "bold")).pack(
                     side="left", padx=10)

        self._mode_btn = tk.Button(
            title_f, text="⊕ SCI",
            bg=PANEL_BG, fg=OP_GLOW,
            activebackground=PANEL_BG, activeforeground=EQ_GLOW,
            font=("Segoe UI", 9, "bold"),
            relief="flat", bd=0, cursor="hand2",
            command=self._toggle_mode)
        self._mode_btn.pack(side="right", padx=6)

        sep = tk.Frame(panel, bg=DISP_EDGE, height=1)
        sep.pack(fill="x", padx=4, pady=(8, 0))

        # ── Display ───────────────────────────────────────────────────────
        disp_wrap = tk.Frame(panel, bg=DISP_EDGE)
        disp_wrap.pack(fill="x", padx=4, pady=(1, 0))
        disp_inner = tk.Frame(disp_wrap, bg=DISP_BG)
        disp_inner.pack(fill="x", padx=1, pady=1)

        self._hist_var = tk.StringVar(value="")
        tk.Label(disp_inner, textvariable=self._hist_var,
                 bg=DISP_BG, fg=TEXT_DIM,
                 font=("Segoe UI", 11), anchor="e").pack(
                     fill="x", padx=14, pady=(10, 0))

        self._disp_var = tk.StringVar(value="0")
        self._disp_lbl = tk.Label(
            disp_inner, textvariable=self._disp_var,
            bg=DISP_BG, fg=TEXT_BRIGHT,
            font=("Segoe UI", 42, "bold"),
            anchor="e", wraplength=380, justify="right")
        self._disp_lbl.pack(fill="x", padx=14, pady=(4, 14))

        # ── Button grid ───────────────────────────────────────────────────
        self._grid_f = tk.Frame(panel, bg=PANEL_BG)
        self._grid_f.pack(fill="both", expand=True, padx=2, pady=(10, 4))

        if self._mode == "basic":
            self._build_basic()
        else:
            self._build_sci()

    def _ds(self, e):
        self._dx = e.x_root - self.winfo_x()
        self._dy = e.y_root - self.winfo_y()

    def _dm(self, e):
        self.geometry(f"+{e.x_root-self._dx}+{e.y_root-self._dy}")

    def _clr(self):
        for w in self._grid_f.winfo_children():
            w.destroy()

    def _btn(self, parent, text, cmd,
             rest=NUM_REST, edge=NUM_EDGE, glow=NUM_GLOW,
             tc=TEXT_BRIGHT, w=76, h=62, row=0, col=0, cs=1):
        b = AuroraButton(parent, text, cmd,
                         rest=rest, edge=edge, glow=glow,
                         tcolor=tc, width=w, height=h)
        b.grid(row=row, column=col, columnspan=cs,
               padx=4, pady=4, sticky="nsew")
        return b

    def _build_basic(self):
        self._clr()
        f = self._grid_f
        for c in range(4):
            f.columnconfigure(c, weight=1)
        e = self.engine
        layout = [
            [("AC",  e.clear,                   FN_REST,  FN_EDGE,  FN_GLOW,  TEXT_FN),
             ("+/−", e.toggle_sign,              NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_MED),
             ("%",   e.percent,                  NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_MED),
             ("÷",   lambda: self._i("÷"),       OP_REST,  OP_EDGE,  OP_GLOW,  TEXT_OP)],
            [("7",   lambda: self._i("7"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("8",   lambda: self._i("8"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("9",   lambda: self._i("9"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("×",   lambda: self._i("×"),       OP_REST,  OP_EDGE,  OP_GLOW,  TEXT_OP)],
            [("4",   lambda: self._i("4"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("5",   lambda: self._i("5"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("6",   lambda: self._i("6"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("−",   lambda: self._i("-"),        OP_REST,  OP_EDGE,  OP_GLOW,  TEXT_OP)],
            [("1",   lambda: self._i("1"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("2",   lambda: self._i("2"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("3",   lambda: self._i("3"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("+",   lambda: self._i("+"),        OP_REST,  OP_EDGE,  OP_GLOW,  TEXT_OP)],
            [("⌫",   e.backspace,                FN_REST,  FN_EDGE,  FN_GLOW,  TEXT_FN),
             ("0",   lambda: self._i("0"),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             (".",   lambda: self._i("."),        NUM_REST, NUM_EDGE, NUM_GLOW, TEXT_BRIGHT),
             ("=",   self._eq,                   EQ_REST,  EQ_EDGE,  EQ_GLOW,  TEXT_EQ)],
        ]
        for r, row in enumerate(layout):
            f.rowconfigure(r, weight=1)
            for c, (t, cmd, rs, ed, gl, tc) in enumerate(row):
                self._btn(f, t, cmd, rs, ed, gl, tc, 76, 62, r, c)

    def _build_sci(self):
        self._clr()
        f = self._grid_f
        for c in range(5):
            f.columnconfigure(c, weight=1)
        e = self.engine
        rows = [
            [("sin", lambda: self._i("sin("),  FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("cos", lambda: self._i("cos("),  FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("tan", lambda: self._i("tan("),  FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("log", lambda: self._i("log("),  FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("ln",  lambda: self._i("ln("),   FN_REST, FN_EDGE, FN_GLOW, TEXT_FN)],
            [("√",   lambda: self._i("√("),    OP_REST, OP_EDGE, OP_GLOW, TEXT_OP),
             ("x²",  lambda: self._i("^2"),    OP_REST, OP_EDGE, OP_GLOW, TEXT_OP),
             ("xⁿ",  lambda: self._i("^"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP),
             ("π",   lambda: self._i("π"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP),
             ("e",   lambda: self._i("e"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP)],
            [("AC",  e.clear,                  FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("(",   lambda: self._i("("),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_MED),
             (")",   lambda: self._i(")"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_MED),
             ("%",   e.percent,                NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_MED),
             ("÷",   lambda: self._i("÷"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP)],
            [("7",   lambda: self._i("7"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("8",   lambda: self._i("8"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("9",   lambda: self._i("9"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("+/−", e.toggle_sign,            NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_MED),
             ("×",   lambda: self._i("×"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP)],
            [("4",   lambda: self._i("4"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("5",   lambda: self._i("5"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("6",   lambda: self._i("6"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("⌫",   e.backspace,              FN_REST, FN_EDGE, FN_GLOW, TEXT_FN),
             ("−",   lambda: self._i("-"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP)],
            [("1",   lambda: self._i("1"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("2",   lambda: self._i("2"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("3",   lambda: self._i("3"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             (".",   lambda: self._i("."),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("+",   lambda: self._i("+"),     OP_REST, OP_EDGE, OP_GLOW, TEXT_OP)],
            [("0",   lambda: self._i("0"),     NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("00",  lambda: self._i("00"),    NUM_REST,NUM_EDGE,NUM_GLOW,TEXT_BRIGHT),
             ("ANS", lambda: self._i(str(e.last_answer)), FN_REST,FN_EDGE,FN_GLOW,TEXT_FN),
             ("=",   self._eq,                EQ_REST, EQ_EDGE, EQ_GLOW, TEXT_EQ),
             None],
        ]
        for r, row in enumerate(rows):
            f.rowconfigure(r, weight=1)
            for c, item in enumerate(row):
                if item is None:
                    continue
                t, cmd, rs, ed, gl, tc = item
                cs = 2 if (r == 6 and c == 3) else 1
                self._btn(f, t, cmd, rs, ed, gl, tc, 62, 52, r, c, cs)

    def _i(self, token):
        self.engine.append(token)
        self._refresh()

    def _eq(self):
        prev = self.engine.expression
        self.engine.evaluate()
        self._hist_var.set(prev + "  =")
        self._refresh()

    def _refresh(self):
        text  = self.engine.display_text
        fsize = 22 if len(text) > 18 else (30 if len(text) > 10 else 42)
        self._disp_lbl.config(font=("Segoe UI", fsize, "bold"))
        self._disp_var.set(text)

    def _toggle_mode(self):
        if self._mode == "basic":
            self._mode = "scientific"
            self._mode_btn.config(text="⊖ BASIC")
            nx, ny = self.winfo_x(), self.winfo_y()
            self._W, self._H = 560, 820
            self.geometry(f"560x820+{nx}+{ny}")
        else:
            self._mode = "basic"
            self._mode_btn.config(text="⊕ SCI")
            nx, ny = self.winfo_x(), self.winfo_y()
            self._W, self._H = 440, 780
            self.geometry(f"440x780+{nx}+{ny}")

        # Rebuild everything (background + panel) cleanly
        # Destroy all children before rebuilding
        for widget in self.winfo_children():
            try:
                widget.destroy()
            except Exception:
                pass
        self._bg = None
        self.update_idletasks()
        self._build()

    def _on_key(self, event):
        k, ch = event.keysym, event.char
        m = {"Return": self._eq, "KP_Enter": self._eq,
             "BackSpace": self.engine.backspace, "Escape": self.engine.clear}
        if k in m:
            m[k]()
            if k not in ("Return", "KP_Enter"):
                self._refresh()
            return
        if ch in "0123456789.+-*/()^%":
            self._i(ch.replace("*", "×").replace("/", "÷"))


if __name__ == "__main__":
    app = CalculatorApp()
    app.mainloop()