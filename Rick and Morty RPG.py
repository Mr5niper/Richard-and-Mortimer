import tkinter as tk
VER = "1.2.3.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("560x320")
tk.Label(root, text="enter command:", font=("Consolas", 12)).pack(pady=8)
e = tk.Entry(root, width=40)
e.pack()
box = tk.Text(root, height=8, width=58, font=("Consolas", 10))
box.pack(pady=8)
def go(*_):
    box.insert("end", "YOU: " + e.get() + "\n"
               "GAME: no. I know better. I've got this.\n"
               "GAME: *clears the level without you*\n\n")
    box.see("end")
    e.delete(0, "end")
e.bind("<Return>", go)
tk.Label(root, text="(gave it confidence. overcorrected. it refuses your input and plays itself.)",
         fg="#888").pack(side="bottom")
root.mainloop()
