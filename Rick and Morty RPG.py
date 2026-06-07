import tkinter as tk
from tkinter import messagebox
VER = "1.2.1.0"
root = tk.Tk()
root.withdraw()
for i in range(6):
    messagebox.askyesno("Are you sure?",
        f"Are you sure? (confirmation {i + 1} of many)\nAre you sure you're sure?")
messagebox.showerror("ConfirmationError",
    "it asked if I was sure I wanted to ask if I was sure.\n"
    "it's confirmation dialogs all the way down, Morty.")
root.destroy()
