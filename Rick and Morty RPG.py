import tkinter as tk
VER = "1.0.1.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x320")
root.configure(bg="black")
tk.Label(root, text="FLIGHT SYSTEMS NOMINAL", bg="black", fg="#3f3",
         font=("Consolas", 14)).pack(pady=10)
tk.Label(root, text="ALT 31,000 ft    HDG 270    SPD 480 kt", bg="black", fg="#3f3",
         font=("Consolas", 12)).pack()
tk.Label(root, text="TOWER: you are cleared to land on the Gromflomite.", bg="black",
         fg="#3f3", font=("Consolas", 11)).pack(pady=14)
tk.Label(root, text="(tried to dry-dock the boat back into an RPG. overshot. it's a flight\nsimulator now. you can't fight enemies, but you can land on them.)",
         bg="black", fg="#393", font=("Consolas", 9)).pack(side="bottom", pady=12)
root.mainloop()
