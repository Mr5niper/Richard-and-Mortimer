import tkinter as tk
VER = "1.0.0.0"
root = tk.Tk()
root.title(f"Rick and Morty RPG v{VER}")
root.geometry("600x300")
root.configure(bg="#003366")
c = tk.Canvas(root, width=600, height=300, bg="#003366", highlightthickness=0)
c.pack()
for x in range(0, 620, 20):
    c.create_text(x, 250, text="~", fill="#0088aa", font=("Consolas", 14))
c.create_text(300, 60, text="I shipped it. it took that literally.", fill="white",
              font=("Consolas", 13))
c.create_text(300, 90, text="it does not RPG. but it SAILS, Morty.", fill="#99ccff",
              font=("Consolas", 10))
boat = c.create_text(-70, 180, text="<__|__>  (a boat)", fill="white", font=("Consolas", 16))
def sail(x=-70):
    c.coords(boat, x, 180)
    if x < 670:
        root.after(30, lambda: sail(x + 6))
root.after(400, lambda: sail())
root.mainloop()
