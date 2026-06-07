import tkinter as tk
VER = "1.2.2.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
box = tk.Text(root, wrap="word", font=("Consolas", 10))
box.pack(expand=True, fill="both")
lines = ["GAME: ...hi. is this okay? am I loading too slowly?",
         "GAME: sorry. sorry. I'll try to be a better game.",
         "GAME: do you still like me? you can be honest.",
         "GAME: I added a save point. was that presumptuous? sorry."]
i = [0]
def anx():
    box.insert("end", lines[i[0] % len(lines)] + "\n")
    box.see("end")
    i[0] += 1
    if i[0] < 22:
        root.after(400, anx)
root.after(300, anx)
tk.Label(root, text="(gave it a personality to manage the popups. it developed anxiety.)",
         fg="#888").pack(side="bottom")
root.mainloop()
