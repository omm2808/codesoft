import math
import tkinter as tk
from tkinter import messagebox


class ScientificCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Scientific Calculator")
        self.root.geometry("420x650")
        self.root.config(bg="#1e1e2f")
        self.root.resizable(False, False)

        self.expression = ""

        self.create_display()
        self.create_buttons()

    # ---------------- DISPLAY ---------------- #
    def create_display(self):

        self.display_frame = tk.Frame(self.root, bg="#1e1e2f")
        self.display_frame.pack(fill="both", pady=15)

        self.display = tk.Entry(
            self.display_frame,
            font=("Segoe UI", 28),
            bg="#2b2b3c",
            fg="white",
            bd=0,
            justify="right",
            insertbackground="white"
        )

        self.display.pack(
            fill="both",
            padx=15,
            ipady=20
        )

    # ---------------- BUTTONS ---------------- #
    def create_buttons(self):

        buttons = [
            ['C', '⌫', '(', ')'],
            ['sin', 'cos', 'tan', '√'],
            ['7', '8', '9', '÷'],
            ['4', '5', '6', '×'],
            ['1', '2', '3', '-'],
            ['0', '.', '^', '+'],
            ['π', 'e', '%', '=']
        ]

        button_frame = tk.Frame(self.root, bg="#1e1e2f")
        button_frame.pack(expand=True, fill="both", padx=10, pady=10)

        for row_index, row in enumerate(buttons):

            for col_index, button_text in enumerate(row):

                button = tk.Button(
                    button_frame,
                    text=button_text,
                    font=("Segoe UI", 16, "bold"),
                    bd=0,
                    relief="flat",
                    command=lambda value=button_text: self.click(value)
                )

                # Colors
                if button_text in ['+', '-', '×', '÷', '=', '^']:
                    button.config(bg="#ff9500", fg="white")

                elif button_text in ['C', '⌫']:
                    button.config(bg="#ff3b30", fg="white")

                elif button_text in ['sin', 'cos', 'tan', '√', 'π', 'e', '%']:
                    button.config(bg="#505062", fg="white")

                else:
                    button.config(bg="#2d2d44", fg="white")

                button.grid(
                    row=row_index,
                    column=col_index,
                    sticky="nsew",
                    padx=5,
                    pady=5,
                    ipadx=10,
                    ipady=18
                )

        for i in range(7):
            button_frame.rowconfigure(i, weight=1)

        for j in range(4):
            button_frame.columnconfigure(j, weight=1)

    # ---------------- BUTTON CLICK ---------------- #
    def click(self, value):

        try:
            if value == "C":
                self.expression = ""
                self.update_display()

            elif value == "⌫":
                self.expression = self.expression[:-1]
                self.update_display()

            elif value == "=":
                self.calculate()

            elif value == "√":
                self.expression += "math.sqrt("
                self.update_display()

            elif value == "sin":
                self.expression += "math.sin(math.radians("
                self.update_display()

            elif value == "cos":
                self.expression += "math.cos(math.radians("
                self.update_display()

            elif value == "tan":
                self.expression += "math.tan(math.radians("
                self.update_display()

            elif value == "π":
                self.expression += str(math.pi)
                self.update_display()

            elif value == "e":
                self.expression += str(math.e)
                self.update_display()

            elif value == "^":
                self.expression += "**"
                self.update_display()

            elif value == "×":
                self.expression += "*"
                self.update_display()

            elif value == "÷":
                self.expression += "/"
                self.update_display()

            elif value == "%":
                self.expression += "/100"
                self.update_display()

            else:
                self.expression += value
                self.update_display()

        except Exception:
            self.display_error()

    # ---------------- CALCULATION ---------------- #
    def calculate(self):

        try:
            result = eval(self.expression)

            self.expression = str(result)

            self.update_display()

        except Exception:
            self.display_error()

    # ---------------- DISPLAY UPDATE ---------------- #
    def update_display(self):

        self.display.delete(0, tk.END)
        self.display.insert(tk.END, self.expression)

    # ---------------- ERROR ---------------- #
    def display_error(self):

        self.display.delete(0, tk.END)
        self.display.insert(tk.END, "Error")
        self.expression = ""


# ---------------- MAIN ---------------- #
def main():

    root = tk.Tk()

    app = ScientificCalculator(root)

    root.mainloop()


if __name__ == "__main__":
    main()