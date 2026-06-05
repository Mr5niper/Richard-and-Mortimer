import tkinter as tk
import random
VER = "0.1.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
root.configure(bg="black")
names = ["UNTITLED_DIMENSION", "ROY: A LIFE 2", "froopy_quest", "SPACE GOLF 77",
         "the other one", "DO NOT OPEN", "garage_v1"]
title = tk.Label(root, bg="black", fg="#5f5", font=("Consolas", 18))
title.pack(expand=True)
tk.Label(root, text="stitched together from three dead games and a microverse. it boots. somehow.",
         bg="black", fg="#555", font=("Consolas", 9)).pack(side="bottom", pady=10)
n = [0]
def glitch():
    title.config(text=random.choice(names))
    n[0] += 1
    if n[0] < 40:
        root.after(150, glitch)
    else:
        title.config(text="[ BUILD UNSTABLE ]", fg="#f55")
root.after(200, glitch)
root.mainloop()
