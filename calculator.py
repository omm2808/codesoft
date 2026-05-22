import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.geometry("360x540")
root.title("Modern Calculator")
root.resizable(False, False)

expression = ""

display = ctk.CTkEntry(
    root,
    width=320,
    height=70,
    font=("Poppins", 30),
    justify="right",
    corner_radius=15
)
display.pack(pady=20)

def press(value):
    global expression
    expression += str(value)
    display.delete(0, "end")
    display.insert("end", expression)

def clear():
    global expression
    expression = ""
    display.delete(0, "end")

def calculate():
    global expression
    try:
        result = str(eval(expression))
        display.delete(0, "end")
        display.insert("end", result)
        expression = result
    except:
        display.delete(0, "end")
        display.insert("end", "Error")
        expression = ""

frame = ctk.CTkFrame(root, fg_color="transparent")
frame.pack()

buttons = [
    ["C", "÷", "×", "⌫"],
    ["7", "8", "9", "-"],
    ["4", "5", "6", "+"],
    ["1", "2", "3", "="],
    ["0", ".", "%"]
]

def backspace():
    global expression
    expression = expression[:-1]
    display.delete(0, "end")
    display.insert("end", expression)

for row in buttons:
    row_frame = ctk.CTkFrame(frame, fg_color="transparent")
    row_frame.pack(pady=6)

    for button in row:

        if button == "=":
            cmd = calculate
            color = "#00C853"

        elif button == "C":
            cmd = clear
            color = "#FF5252"

        elif button == "⌫":
            cmd = backspace
            color = "#FF9800"

        else:
            color = "#1F1F1F"

            if button == "×":
                cmd = lambda x="*": press(x)

            elif button == "÷":
                cmd = lambda x="/": press(x)

            else:
                cmd = lambda x=button: press(x)

        btn = ctk.CTkButton(
            row_frame,
            text=button,
            width=70,
            height=70,
            font=("Poppins", 24, "bold"),
            corner_radius=20,
            fg_color=color,
            hover_color="#333333",
            command=cmd
        )

        btn.pack(side="left", padx=5)

root.mainloop()