import tkinter as tk
VER = "0.5.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x340")
box = tk.Text(root, wrap="word", font=("Consolas", 10))
box.pack(expand=True, fill="both")
lines = ["RICK (shopkeeper): I'm the real Rick.",
         "RICK (guard): no, I'M the real Rick, you're a clone.",
         "RICK (questgiver): you're BOTH clones. *burp*",
         "RICK (innkeeper): nobody is actually running the shops.",
         "RICK (final boss): I'm not doing it, YOU do it."]
i = [0]
def arg():
    box.insert("end", lines[i[0] % len(lines)] + "\n")
    box.see("end")
    i[0] += 1
    if i[0] < 36:
        root.after(220, arg)
    else:
        box.insert("end", "\n(every NPC is me now. none of them will work. the shops are closed.)")
root.after(300, arg)
root.mainloop()
