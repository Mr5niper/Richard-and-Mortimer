import tkinter as tk
VER = "1.1.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x340")
tk.Label(root, text="(reinstalled gravity. installed about ten times too much.)",
         fg="#888").pack(side="top", pady=4)
f = tk.Frame(root)
f.pack(side="bottom", fill="x")
for t in ["MAP", "QUEST", "INVENTORY", "SHOP", "Morty's self-esteem"]:
    tk.Button(f, text=t).pack(side="left")
tk.Label(root, text="HP 100    MP 50    GOLD 0", font=("Consolas", 10)).pack(side="bottom")
root.mainloop()
