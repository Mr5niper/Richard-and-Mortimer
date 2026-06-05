import tkinter as tk
VER = "0.2.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x300")
tk.Label(root, text="Generating multiverse...", font=("Consolas", 14)).pack(pady=30)
lbl = tk.Label(root, text="room 0", font=("Consolas", 12), fg="#39f")
lbl.pack()
c = [0]
def gen():
    c[0] += 137
    lbl.config(text=f"room {c[0]:,}")
    root.after(30, gen)
root.after(300, gen)
tk.Label(root, text="(it is never going to stop. I can hear the CPU begging.)",
         fg="#888").pack(side="bottom", pady=10)
root.mainloop()
