import tkinter as tk
from tkinter import messagebox
VER = "1.3.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x300")
tk.Label(root, text="A wild SECRET BOSS appears...", font=("Consolas", 13)).pack(pady=20)
tk.Label(root, text="it's RICK.", font=("Consolas", 18, "bold")).pack()
def boom():
    messagebox.showerror("RespectError",
        "the game encountered RICK (secret boss) and crashed immediately\n"
        "out of pure respect. it does this every time I enter a room.\n"
        "I am too powerful for my own game, Morty.")
    root.destroy()
root.after(1200, boom)
root.mainloop()
