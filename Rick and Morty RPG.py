import tkinter as tk
import random
VER = "1.0.2.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x340")
root.configure(bg="#111")
c = tk.Canvas(root, width=600, height=300, bg="#111", highlightthickness=0)
c.pack()
mortys = [c.create_text(300, 150, text="Morty", fill="#dddd00", font=("Consolas", 12))
          for _ in range(12)]
vel = [(random.uniform(-6, 6), random.uniform(-6, 6)) for _ in mortys]
def fall():
    for m, (dx, dy) in zip(mortys, vel):
        c.move(m, dx, dy)
        x, y = c.coords(m)
        if x < 0 or x > 600 or y < 0 or y > 300:
            c.coords(m, 300, 150)
    root.after(40, fall)
root.after(300, fall)
tk.Label(root, text="deleted the sky to force it back to an RPG. deleting the sky deleted 'up.'\n"
                    "Morty now falls in every direction at once. he says he's fine.",
         bg="#111", fg="#888", font=("Consolas", 9)).pack(side="bottom", pady=8)
root.mainloop()
