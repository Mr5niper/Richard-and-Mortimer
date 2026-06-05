import tkinter as tk
VER = "0.3.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x340")
tk.Label(root, text="THE NPC SENATE IS NOW IN SESSION", font=("Consolas", 13, "bold")).pack(pady=8)
box = tk.Text(root, wrap="word", font=("Consolas", 10))
box.pack(expand=True, fill="both")
lines = ["MOTION: shall the player receive the main quest? ",
         "SHOPKEEPER yields the floor to the BLACKSMITH. ",
         "BLACKSMITH proposes a subcommittee. ",
         "the subcommittee requires a vote. ",
         "the vote is filibustered by a goblin. ",
         "MOTION tabled indefinitely. "]
i = [0]
def sess():
    box.insert("end", lines[i[0] % len(lines)])
    box.see("end")
    i[0] += 1
    if i[0] < 60:
        root.after(180, sess)
    else:
        box.insert("end", "\n\n(your main quest is stuck in committee. forever.)")
root.after(300, sess)
root.mainloop()
