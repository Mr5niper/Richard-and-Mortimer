import tkinter as tk
VER = "1.3.0.1"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
root.configure(bg="#110000")
tk.Label(root, text="~ FINAL BOSS ~", bg="#110000", fg="#f55",
         font=("Consolas", 16, "bold")).pack(pady=10)
tk.Label(root, text="JERRY", bg="#110000", fg="white", font=("Consolas", 30, "bold")).pack()
tk.Label(root, text="HP: 4     Special Move: cannot parallel park", bg="#110000",
         fg="#faa", font=("Consolas", 12)).pack(pady=8)
tk.Label(root, text="(pulled myself out as the boss. it panicked and made JERRY the climax\n"
                    "of the entire multiverse. truly the darkest timeline.)",
         bg="#110000", fg="#caa", font=("Consolas", 9)).pack(side="bottom", pady=12)
root.mainloop()
