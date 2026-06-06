import tkinter as tk
VER = "0.6.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
root.configure(bg="#000018")
tk.Label(root, text="* YOU WIN *", bg="#000018", fg="gold",
         font=("Consolas", 26, "bold")).pack(expand=True)
tk.Label(root, text="THE END", bg="#000018", fg="white", font=("Consolas", 16)).pack()
tk.Label(root, text="(you did nothing. the one remaining Rick got bored, wandered into the\nboss arena, and beat the game before it started. the ending plays on launch.)",
         bg="#000018", fg="#88a", font=("Consolas", 9)).pack(side="bottom", pady=12)
root.mainloop()
