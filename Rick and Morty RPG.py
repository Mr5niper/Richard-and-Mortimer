import tkinter as tk
VER = "0.2.1.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x300")
tk.Label(root, text="You are in: a broom closet.", font=("Consolas", 15)).pack(pady=40)
tk.Label(root, text="The entire infinite multiverse is this closet.\nExits: none. There is a mop.",
         font=("Consolas", 12), fg="#a33").pack()
tk.Label(root, text="(capped the generation. capped it a little hard.)",
         fg="#888").pack(side="bottom", pady=10)
root.mainloop()
