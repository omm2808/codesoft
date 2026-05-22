import tkinter as tk
from tkinter import ttk, messagebox
import json, os
from datetime import datetime, date
from enum import Enum

DATA_FILE = os.path.join(os.path.expanduser("~"), "todo_tasks.json")

C = {
    "bg":        "#0d0d12",
    "sidebar":   "#13131a",
    "card":      "#1a1a25",
    "card2":     "#1f1f2e",
    "input":     "#22222f",
    "border":    "#2a2a3d",
    "accent":    "#6c63ff",
    "accent_h":  "#8b85ff",
    "accent_lo": "#1e1c4a",
    "green":     "#22c97a",
    "yellow":    "#f5a623",
    "red":       "#ff5e5e",
    "blue":      "#4ea8de",
    "text":      "#eaeaf5",
    "muted":     "#5a5a7a",
    "done_bg":   "#16161f",
    "done_text": "#3a3a55",
    "white":     "#ffffff",
    "progress":  "#6c63ff",
}

PRI_COLORS = {"High": C["red"], "Medium": C["yellow"], "Low": C["green"]}
PRI_BG     = {"High": "#3d1f1f", "Medium": "#3d2e10", "Low": "#12362a"}
CAT_ICONS  = {
    "Personal": "👤", "Work": "💼", "Shopping": "🛒",
    "Health": "❤️", "Finance": "💰", "Other": "📌"
}
CATEGORIES = list(CAT_ICONS.keys())

def _font(size, weight="normal", family="Segoe UI"):
    return (family, size, weight)

class Task:
    def __init__(self, title, description="", priority="Medium",
                 category="Personal", due_date="", task_id=None):
        self.id          = task_id or datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.title       = title
        self.description = description
        self.priority    = priority
        self.category    = category
        self.due_date    = due_date
        self.done        = False
        self.created_at  = datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {k: getattr(self, k) for k in
                ("id","title","description","priority","category","due_date","done","created_at")}

    @classmethod
    def from_dict(cls, d):
        t = cls(d["title"], d.get("description",""), d.get("priority","Medium"),
                d.get("category","Personal"), d.get("due_date",""), d.get("id"))
        t.done = d.get("done", False)
        t.created_at = d.get("created_at","")
        return t


class TaskStore:
    def __init__(self):
        self.tasks = []
        self.load()

    def load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE) as f:
                    self.tasks = [Task.from_dict(d) for d in json.load(f)]
            except Exception:
                self.tasks = []

    def save(self):
        with open(DATA_FILE, "w") as f:
            json.dump([t.to_dict() for t in self.tasks], f, indent=2)

    def add(self, task):    self.tasks.append(task);  self.save()
    def delete(self, tid):  self.tasks = [t for t in self.tasks if t.id != tid]; self.save()
    def toggle(self, tid):
        for t in self.tasks:
            if t.id == tid: t.done = not t.done
        self.save()

    def update(self, tid, **kw):
        for t in self.tasks:
            if t.id == tid:
                for k, v in kw.items(): setattr(t, k, v)
        self.save()

    def clear_done(self):   self.tasks = [t for t in self.tasks if not t.done]; self.save()

    def filter(self, search="", category="All", show_done=True, priority="All", sort="created"):
        res = list(self.tasks)
        if not show_done:      res = [t for t in res if not t.done]
        if category != "All":  res = [t for t in res if t.category == category]
        if priority != "All":  res = [t for t in res if t.priority == priority]
        if search:
            s = search.lower()
            res = [t for t in res if s in t.title.lower() or s in t.description.lower()]
        order = {"High": 0, "Medium": 1, "Low": 2}
        if sort == "priority":  res.sort(key=lambda t: (t.done, order.get(t.priority, 1)))
        elif sort == "due":     res.sort(key=lambda t: (t.done, t.due_date or "9999"))
        elif sort == "alpha":   res.sort(key=lambda t: (t.done, t.title.lower()))
        else:                   res.sort(key=lambda t: (t.done, t.created_at))
        return res

    def stats(self):
        total = len(self.tasks)
        done  = sum(1 for t in self.tasks if t.done)
        hi    = sum(1 for t in self.tasks if not t.done and t.priority == "High")
        return total, done, total - done, hi

    def due_today(self):
        today = date.today().isoformat()
        return [t for t in self.tasks if not t.done and t.due_date == today]


class TaskDialog(tk.Toplevel):
    def __init__(self, parent, task=None):
        super().__init__(parent)
        self.result = None
        self.task   = task
        self.configure(bg=C["bg"])
        self.resizable(False, False)
        self.grab_set()
        self.title("Edit Task" if task else "New Task")
        self._build()
        self.update_idletasks()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        w, h   = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px+(pw-w)//2}+{py+(ph-h)//2}")
        if task: self._populate()

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, bg=C["bg"], fg=C["muted"],
                 font=_font(8), anchor="w").pack(fill="x", pady=(12,3))

    def _styled_entry(self, parent, textvariable=None, width=None):
        kw = dict(bg=C["input"], fg=C["text"], insertbackground=C["text"],
                  relief="flat", font=_font(10), bd=0,
                  highlightthickness=1, highlightbackground=C["border"],
                  highlightcolor=C["accent"])
        if textvariable: kw["textvariable"] = textvariable
        if width:        kw["width"] = width
        e = tk.Entry(parent, **kw)
        e.bind("<FocusIn>",  lambda _: e.config(highlightbackground=C["accent"]))
        e.bind("<FocusOut>", lambda _: e.config(highlightbackground=C["border"]))
        return e

    def _build(self):
        hdr = tk.Frame(self, bg=C["card2"], pady=0)
        hdr.pack(fill="x")
        icon = "✏️" if self.task else "✨"
        label_text = "Edit Task" if self.task else "New Task"
        tk.Label(hdr, text=f"{icon}  {label_text}", bg=C["card2"], fg=C["text"],
                 font=_font(13, "bold"), pady=16).pack()
        tk.Frame(hdr, bg=C["accent"], height=2).pack(fill="x")

        body = tk.Frame(self, bg=C["bg"], padx=28, pady=4)
        body.pack(fill="both", expand=True)

        self._field_label(body, "TITLE  *")
        self.v_title = tk.StringVar()
        e = self._styled_entry(body, self.v_title)
        e.pack(fill="x", ipady=6)
        e.focus()

        self._field_label(body, "DESCRIPTION")
        self.desc_box = tk.Text(body, height=3, bg=C["input"], fg=C["text"],
                                insertbackground=C["text"], relief="flat",
                                font=_font(10), bd=0, wrap="word",
                                highlightthickness=1, highlightbackground=C["border"],
                                highlightcolor=C["accent"])
        self.desc_box.pack(fill="x", ipady=4)

        row = tk.Frame(body, bg=C["bg"])
        row.pack(fill="x", pady=(4,0))
        for col, (label, var_name, values, default) in enumerate([
            ("PRIORITY", "v_priority", ["High","Medium","Low"], "Medium"),
            ("CATEGORY", "v_category", CATEGORIES, "Personal"),
        ]):
            f = tk.Frame(row, bg=C["bg"])
            f.grid(row=0, column=col, sticky="ew", padx=(0,12) if col==0 else 0)
            row.columnconfigure(col, weight=1)
            self._field_label(f, label)
            var = tk.StringVar(value=default)
            setattr(self, var_name, var)
            cb = ttk.Combobox(f, textvariable=var, values=values, state="readonly", font=_font(10))
            cb.pack(fill="x")

        self._field_label(body, "DUE DATE  (YYYY-MM-DD)")
        self.v_due = tk.StringVar()
        self._styled_entry(body, self.v_due).pack(fill="x", ipady=6)

        self._field_label(body, "TAGS  (comma separated)")
        self.v_tags = tk.StringVar()
        self._styled_entry(body, self.v_tags).pack(fill="x", ipady=6)

        btn_row = tk.Frame(self, bg=C["bg"], padx=28, pady=18)
        btn_row.pack(fill="x")
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)

        cancel = tk.Button(btn_row, text="Cancel", bg=C["input"], fg=C["muted"],
                           relief="flat", font=_font(10), cursor="hand2",
                           activebackground=C["border"], activeforeground=C["text"],
                           command=self.destroy, pady=9)
        cancel.grid(row=0, column=0, sticky="ew", padx=(0,8))

        save = tk.Button(btn_row, text="Save Task  ✓", bg=C["accent"], fg=C["white"],
                         relief="flat", font=_font(10, "bold"), cursor="hand2",
                         activebackground=C["accent_h"], activeforeground=C["white"],
                         command=self._save, pady=9)
        save.grid(row=0, column=1, sticky="ew")

        self._style_comboboxes()

    def _style_comboboxes(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TCombobox", fieldbackground=C["input"], background=C["input"],
                    foreground=C["text"], selectbackground=C["accent"],
                    selectforeground=C["white"], arrowcolor=C["accent"],
                    borderwidth=1, relief="flat")
        s.map("TCombobox", fieldbackground=[("readonly", C["input"])],
              foreground=[("readonly", C["text"])])

    def _populate(self):
        self.v_title.set(self.task.title)
        self.desc_box.insert("1.0", self.task.description)
        self.v_priority.set(self.task.priority)
        self.v_category.set(self.task.category)
        self.v_due.set(self.task.due_date)
        if hasattr(self.task, "tags"):
            self.v_tags.set(", ".join(self.task.tags))

    def _save(self):
        title = self.v_title.get().strip()
        if not title:
            messagebox.showwarning("Required", "Please enter a task title.", parent=self)
            return
        due = self.v_due.get().strip()
        if due:
            try: datetime.strptime(due, "%Y-%m-%d")
            except ValueError:
                messagebox.showwarning("Invalid Date", "Use format YYYY-MM-DD", parent=self)
                return
        self.result = dict(
            title       = title,
            description = self.desc_box.get("1.0","end").strip(),
            priority    = self.v_priority.get(),
            category    = self.v_category.get(),
            due_date    = due,
        )
        self.destroy()


class ToDoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.store     = TaskStore()
        self.sort_var  = tk.StringVar(value="created")
        self.title("TaskFlow — To-Do Manager")
        self.configure(bg=C["bg"])
        self.geometry("1020x700")
        self.minsize(820, 560)
        self._apply_global_style()
        self._build_sidebar()
        self._build_main()
        self._refresh()
        self._check_due_today()

    def _apply_global_style(self):
        s = ttk.Style(self)
        s.theme_use("default")
        s.configure("Vertical.TScrollbar", background=C["border"], troughcolor=C["bg"],
                    arrowcolor=C["muted"], borderwidth=0, relief="flat")
        s.map("Vertical.TScrollbar", background=[("active", C["accent"])])

    def _sep(self, parent, pady=8):
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=16, pady=pady)

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=C["sidebar"], width=230)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)

        brand = tk.Frame(sb, bg=C["sidebar"])
        brand.pack(fill="x", pady=(24,8))
        tk.Label(brand, text="✦", bg=C["sidebar"], fg=C["accent"],
                 font=_font(28)).pack()
        tk.Label(brand, text="TaskFlow", bg=C["sidebar"], fg=C["text"],
                 font=_font(17, "bold")).pack()
        tk.Label(brand, text="Your productivity hub", bg=C["sidebar"], fg=C["muted"],
                 font=_font(8)).pack(pady=(2,0))

        self._sep(sb, 16)

        stat_frame = tk.Frame(sb, bg=C["card2"], padx=16, pady=14)
        stat_frame.pack(fill="x", padx=12)
        self.lbl_total   = self._stat_row(stat_frame, "0", "Total Tasks",   C["accent"])
        self.lbl_pending = self._stat_row(stat_frame, "0", "Pending",        C["yellow"])
        self.lbl_done    = self._stat_row(stat_frame, "0", "Completed",      C["green"])
        self.lbl_urgent  = self._stat_row(stat_frame, "0", "Urgent (High)",  C["red"])

        prog_frame = tk.Frame(sb, bg=C["sidebar"], padx=16)
        prog_frame.pack(fill="x", pady=(12,0))
        tk.Label(prog_frame, text="PROGRESS", bg=C["sidebar"], fg=C["muted"],
                 font=_font(8), anchor="w").pack(fill="x")
        self.progress_bar = tk.Canvas(prog_frame, bg=C["border"], height=8,
                                      highlightthickness=0, relief="flat")
        self.progress_bar.pack(fill="x", pady=(4,2))
        self.prog_label = tk.Label(prog_frame, text="0% complete", bg=C["sidebar"],
                                   fg=C["muted"], font=_font(8), anchor="e")
        self.prog_label.pack(fill="x")

        self._sep(sb, 14)

        tk.Label(sb, text="CATEGORIES", bg=C["sidebar"], fg=C["muted"],
                 font=_font(8), anchor="w").pack(anchor="w", padx=16, pady=(0,6))

        self.cat_var = tk.StringVar(value="All")
        cats = [("All", "  🗂️  All Tasks")] + [(c, f"  {CAT_ICONS[c]}  {c}") for c in CATEGORIES]
        for val, label in cats:
            self._sidebar_radio(sb, label, self.cat_var, val)

        self._sep(sb, 14)

        self.show_done_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sb, text="  Show completed", variable=self.show_done_var,
                       bg=C["sidebar"], fg=C["text"], selectcolor=C["card2"],
                       activebackground=C["sidebar"], font=_font(9),
                       cursor="hand2", command=self._refresh).pack(anchor="w", padx=12, pady=2)

        clr_btn = tk.Button(sb, text="🗑   Clear Completed", bg=C["card2"], fg=C["red"],
                            relief="flat", font=_font(9), cursor="hand2",
                            activebackground=C["border"], activeforeground=C["red"],
                            command=self._clear_done, pady=8)
        clr_btn.pack(fill="x", padx=12, pady=(8,4))

        exp_btn = tk.Button(sb, text="📤  Export Tasks", bg=C["card2"], fg=C["blue"],
                            relief="flat", font=_font(9), cursor="hand2",
                            activebackground=C["border"], activeforeground=C["blue"],
                            command=self._export, pady=8)
        exp_btn.pack(fill="x", padx=12, pady=4)

    def _sidebar_radio(self, parent, label, var, val):
        f = tk.Frame(parent, bg=C["sidebar"], cursor="hand2")
        f.pack(fill="x", padx=8, pady=1)

        def on_enter(_): f.config(bg=C["card2"])
        def on_leave(_): f.config(bg=C["sidebar"] if var.get()!=val else C["accent_lo"])
        f.bind("<Enter>", on_enter)
        f.bind("<Leave>", on_leave)
        f.bind("<Button-1>", lambda _: (var.set(val), self._refresh()))

        rb = tk.Radiobutton(f, text=label, variable=var, value=val, bg=C["sidebar"],
                            fg=C["text"], selectcolor=C["accent_lo"],
                            activebackground=C["card2"], font=_font(9),
                            cursor="hand2", indicatoron=True,
                            command=self._refresh)
        rb.pack(fill="x", padx=8, pady=4)

    def _stat_row(self, parent, val, label, color):
        f = tk.Frame(parent, bg=C["card2"])
        f.pack(fill="x", pady=3)
        num = tk.Label(f, text=val, bg=C["card2"], fg=color, font=_font(20, "bold"))
        num.pack(side="left")
        tk.Label(f, text=f"  {label}", bg=C["card2"], fg=C["muted"],
                 font=_font(8)).pack(side="left", pady=(6,0))
        return num

    def _build_main(self):
        main = tk.Frame(self, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        topbar = tk.Frame(main, bg=C["card"], pady=12, padx=18)
        topbar.pack(fill="x")

        search_wrap = tk.Frame(topbar, bg=C["input"], highlightthickness=1,
                               highlightbackground=C["border"])
        search_wrap.pack(side="left", fill="x", expand=True, ipady=2)
        tk.Label(search_wrap, text="🔍", bg=C["input"], fg=C["muted"],
                 font=_font(11)).pack(side="left", padx=(10,4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())
        search_e = tk.Entry(search_wrap, textvariable=self.search_var, bg=C["input"],
                            fg=C["text"], insertbackground=C["text"], relief="flat",
                            font=_font(11), bd=0)
        search_e.pack(side="left", fill="x", expand=True, pady=7, padx=4)
        search_e.bind("<FocusIn>",  lambda _: search_wrap.config(highlightbackground=C["accent"]))
        search_e.bind("<FocusOut>", lambda _: search_wrap.config(highlightbackground=C["border"]))

        tk.Label(topbar, text="Sort:", bg=C["card"], fg=C["muted"],
                 font=_font(9)).pack(side="left", padx=(12,4))
        sort_cb = ttk.Combobox(topbar, textvariable=self.sort_var, width=10,
                               values=["created","priority","due","alpha"],
                               state="readonly", font=_font(9))
        sort_cb.pack(side="left")
        self.sort_var.trace_add("write", lambda *_: self._refresh())

        self.pri_filter = tk.StringVar(value="All")
        tk.Label(topbar, text="Priority:", bg=C["card"], fg=C["muted"],
                 font=_font(9)).pack(side="left", padx=(10,4))
        pri_cb = ttk.Combobox(topbar, textvariable=self.pri_filter, width=8,
                               values=["All","High","Medium","Low"],
                               state="readonly", font=_font(9))
        pri_cb.pack(side="left")
        self.pri_filter.trace_add("write", lambda *_: self._refresh())

        add_btn = tk.Button(topbar, text="  ＋  New Task  ", bg=C["accent"], fg=C["white"],
                            relief="flat", font=_font(10, "bold"), cursor="hand2",
                            activebackground=C["accent_h"], activeforeground=C["white"],
                            command=self._new_task, pady=7)
        add_btn.pack(side="left", padx=(14,0))

        list_outer = tk.Frame(main, bg=C["bg"])
        list_outer.pack(fill="both", expand=True, padx=14, pady=12)

        self.canvas = tk.Canvas(list_outer, bg=C["bg"], highlightthickness=0)
        vsb = ttk.Scrollbar(list_outer, orient="vertical", command=self.canvas.yview,
                             style="Vertical.TScrollbar")
        self.task_frame = tk.Frame(self.canvas, bg=C["bg"])
        self.task_frame.bind(
            "<Configure>",
            lambda _: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self._canvas_win = self.canvas.create_window((0,0), window=self.task_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=vsb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self.canvas.bind("<Configure>",
                         lambda e: self.canvas.itemconfig(self._canvas_win, width=e.width))
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def _refresh(self):
        for w in self.task_frame.winfo_children():
            w.destroy()

        total, done, pending, urgent = self.store.stats()
        self.lbl_total.config(text=str(total))
        self.lbl_done.config(text=str(done))
        self.lbl_pending.config(text=str(pending))
        self.lbl_urgent.config(text=str(urgent))

        pct = int(done / total * 100) if total else 0
        self.progress_bar.update_idletasks()
        pw = self.progress_bar.winfo_width()
        self.progress_bar.delete("all")
        self.progress_bar.create_rectangle(0, 0, pw, 8, fill=C["border"], outline="")
        if pct:
            self.progress_bar.create_rectangle(0, 0, int(pw * pct / 100), 8,
                                               fill=C["accent"], outline="")
        self.prog_label.config(text=f"{pct}% complete")

        tasks = self.store.filter(
            search   = self.search_var.get(),
            category = self.cat_var.get(),
            show_done= self.show_done_var.get(),
            priority = self.pri_filter.get(),
            sort     = self.sort_var.get(),
        )

        if not tasks:
            empty = tk.Frame(self.task_frame, bg=C["bg"])
            empty.pack(expand=True, fill="both", pady=80)
            tk.Label(empty, text="✦", bg=C["bg"], fg=C["border"],
                     font=_font(40)).pack()
            tk.Label(empty, text="No tasks here", bg=C["bg"], fg=C["muted"],
                     font=_font(14, "bold")).pack(pady=(8,4))
            tk.Label(empty, text="Click  ＋ New Task  to get started",
                     bg=C["bg"], fg=C["muted"], font=_font(9)).pack()
            return

        today = date.today().isoformat()
        for task in tasks:
            self._task_card(task, today)

    def _task_card(self, task, today):
        is_done = task.done
        bg      = C["done_bg"] if is_done else C["card"]
        border  = C["border"]

        overdue = (not is_done and task.due_date and task.due_date < today)
        if overdue: border = C["red"]

        outer = tk.Frame(self.task_frame, bg=border, pady=1, padx=1)
        outer.pack(fill="x", pady=4, padx=2)

        card = tk.Frame(outer, bg=bg, pady=12, padx=14)
        card.pack(fill="x")

        left = tk.Frame(card, bg=bg, width=38)
        left.pack(side="left", fill="y", padx=(0,12))
        left.pack_propagate(False)

        chk_txt = "✔" if is_done else "○"
        chk_fg  = C["green"] if is_done else C["muted"]
        chk_btn = tk.Button(left, text=chk_txt, bg=bg, fg=chk_fg, relief="flat",
                            font=_font(18), cursor="hand2", bd=0,
                            activebackground=bg, activeforeground=C["green"],
                            command=lambda t=task: self._toggle(t.id))
        chk_btn.pack(pady=(2,0))

        body = tk.Frame(card, bg=bg)
        body.pack(side="left", fill="both", expand=True)

        title_row = tk.Frame(body, bg=bg)
        title_row.pack(fill="x")

        pri_color = PRI_COLORS.get(task.priority, C["muted"])
        pri_bg    = PRI_BG.get(task.priority, C["input"])
        pri_lbl   = tk.Label(title_row, text=f" {task.priority} ", bg=pri_bg, fg=pri_color,
                             font=_font(8, "bold"), padx=4, pady=2)
        pri_lbl.pack(side="left", padx=(0,8))

        cat_lbl = tk.Label(title_row,
                           text=f"{CAT_ICONS.get(task.category,'')} {task.category}",
                           bg=C["accent_lo"], fg=C["accent_h"],
                           font=_font(8), padx=5, pady=2)
        cat_lbl.pack(side="left")

        title_txt  = task.title
        title_fg   = C["done_text"] if is_done else C["text"]
        title_font = _font(11, "bold") if not is_done else _font(11)
        title_lbl  = tk.Label(body, text=title_txt, bg=bg, fg=title_fg,
                              font=title_font, anchor="w")
        title_lbl.pack(fill="x", pady=(4,2))
        if is_done:
            title_lbl.config(font=(*title_font[:2], "overstrike"))

        if task.description:
            short = task.description[:90] + ("…" if len(task.description)>90 else "")
            tk.Label(body, text=short, bg=bg,
                     fg=C["done_text"] if is_done else C["muted"],
                     font=_font(9), anchor="w", wraplength=520, justify="left").pack(fill="x")

        meta = tk.Frame(body, bg=bg)
        meta.pack(fill="x", pady=(6,0))

        if task.due_date:
            due_fg = C["red"] if (not is_done and task.due_date < date.today().isoformat()) else C["yellow"]
            due_fg = C["done_text"] if is_done else due_fg
            due_icon = "⚠️" if (not is_done and task.due_date < date.today().isoformat()) else "📅"
            tk.Label(meta, text=f"{due_icon} {task.due_date}", bg=bg, fg=due_fg,
                     font=_font(8)).pack(side="left", padx=(0,10))

        tk.Label(meta, text=f"🕓 {task.created_at}", bg=bg,
                 fg=C["done_text"] if is_done else C["muted"],
                 font=_font(8)).pack(side="left")

        actions = tk.Frame(card, bg=bg)
        actions.pack(side="right", fill="y", padx=(10,0))

        edit_btn = tk.Button(actions, text="✏️", bg=C["input"], fg=C["accent_h"],
                             relief="flat", font=_font(11), cursor="hand2",
                             activebackground=C["accent_lo"], activeforeground=C["accent_h"],
                             command=lambda t=task: self._edit_task(t),
                             width=3, pady=4)
        edit_btn.pack(pady=(0,4))

        del_btn = tk.Button(actions, text="🗑", bg=C["input"], fg=C["red"],
                            relief="flat", font=_font(11), cursor="hand2",
                            activebackground="#3d1f1f", activeforeground=C["red"],
                            command=lambda t=task: self._delete(t.id),
                            width=3, pady=4)
        del_btn.pack()

    def _check_due_today(self):
        due = self.store.due_today()
        if due:
            names = "\n".join(f"  • {t.title}" for t in due[:5])
            more  = f"\n  …and {len(due)-5} more" if len(due)>5 else ""
            messagebox.showinfo("Due Today 📅",
                                f"You have {len(due)} task(s) due today:\n\n{names}{more}",
                                parent=self)

    def _new_task(self):
        dlg = TaskDialog(self)
        self.wait_window(dlg)
        if dlg.result:
            self.store.add(Task(**dlg.result))
            self._refresh()

    def _edit_task(self, task):
        dlg = TaskDialog(self, task)
        self.wait_window(dlg)
        if dlg.result:
            self.store.update(task.id, **dlg.result)
            self._refresh()

    def _toggle(self, tid):
        self.store.toggle(tid)
        self._refresh()

    def _delete(self, tid):
        if messagebox.askyesno("Delete Task",
                               "Permanently delete this task?", parent=self):
            self.store.delete(tid)
            self._refresh()

    def _clear_done(self):
        count = sum(1 for t in self.store.tasks if t.done)
        if count == 0:
            messagebox.showinfo("Nothing to Clear", "No completed tasks.", parent=self)
            return
        if messagebox.askyesno("Clear Completed",
                               f"Remove all {count} completed task(s)?", parent=self):
            self.store.clear_done()
            self._refresh()

    def _export(self):
        path = os.path.join(os.path.expanduser("~"), "Desktop", "tasks_export.json")
        try:
            with open(path, "w") as f:
                json.dump([t.to_dict() for t in self.store.tasks], f, indent=2)
            messagebox.showinfo("Exported", f"Tasks saved to:\n{path}", parent=self)
        except Exception as e:
            messagebox.showerror("Export Failed", str(e), parent=self)


if __name__ == "__main__":
    app = ToDoApp()
    app.mainloop()
