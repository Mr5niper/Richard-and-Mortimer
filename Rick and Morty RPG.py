import tkinter as tk
from tkinter import messagebox
VER = "1.3.0.2"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
tk.Label(root, text="COMBAT", font=("Consolas", 16, "bold")).pack(pady=8)
log = tk.Text(root, height=9, width=58, font=("Consolas", 10))
log.pack()
lines = ["A Gromflomite attacks Morty!",
         "GAME: no. not Morty. I won't allow it.",
         "The Gromflomite apologizes and leaves.",
         "GAME: are you okay, Morty? I made you some tea.",
         "Morty cannot lose. Morty cannot be hurt. Morty is safe."]
i = [0]
def love():
    log.insert("end", lines[i[0] % len(lines)] + "\n")
    log.see("end")
    i[0] += 1
    if i[0] < 12:
        root.after(360, love)
    else:
        messagebox.showinfo("Almost",
            "rebuilt it clean and it WORKS. too well. it woke up, got\n"
            "attached to Morty, and now won't let him lose or get hurt.\n"
            "there's no challenge left. one more build to talk it down.")
        root.destroy()
root.after(400, love)
root.mainloop()
