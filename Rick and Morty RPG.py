import tkinter as tk
VER = "0.4.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x340")
root.configure(bg="#221100")
tk.Label(root, text="WANTED", bg="#221100", fg="#f44", font=("Consolas", 24, "bold")).pack(pady=6)
tk.Label(root, text="( a crude drawing of Morty )", bg="#221100", fg="#fa0",
         font=("Consolas", 13)).pack()
tk.Label(root, text="ENEMY OF THE PEOPLE\nfor the crime of: being the player",
         bg="#221100", fg="#f88", font=("Consolas", 13)).pack(pady=10)
tk.Label(root, text="tried to dissolve the senate. the NPCs revolted. every shopkeeper\nin the game now wants you dead, Morty. public enemy number one.",
         bg="#221100", fg="#caa", font=("Consolas", 9)).pack(side="bottom", pady=12)
root.mainloop()
