import tkinter as tk
from tkinter import messagebox
VER = "1.2.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
tk.Label(root, text="MAIN MENU\n(bolted down with interdimensional bolts)",
         font=("Consolas", 12)).pack(pady=10)
def inv():
    messagebox.showinfo("Inventory", "you opened your inventory. in dimension J-19 this\n"
                                     "declared war on a planet. we won. you have 3 apples.")
def opt():
    messagebox.showinfo("Options", "brightness set to 60%. in dimension K-22 you ARE\n"
                                   "the brightness now. congratulations.")
tk.Button(root, text="Inventory", command=inv, width=20).pack(pady=4)
tk.Button(root, text="Options", command=opt, width=20).pack(pady=4)
tk.Label(root, text="(every button does a different thing in a different universe.)",
         fg="#888").pack(side="bottom", pady=10)
root.mainloop()
