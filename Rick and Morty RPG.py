import tkinter as tk
VER = "1.1.1.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
root.configure(bg="#000018")
tk.Label(root, text="", bg="#000018").pack(expand=True)
tk.Label(root, text="(the game is running. you just can't see any of it.\n"
                    "the entire UI floated off into low orbit. it'll come back. probably.)",
         bg="#000018", fg="#445", font=("Consolas", 9)).pack(side="bottom", pady=14)
root.mainloop()
