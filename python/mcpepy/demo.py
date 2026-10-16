"""Launch a tiny interactive voxel-world demo using Python's standard Tk GUI.

Run from the python directory: python3 -m mcpepy.demo
Controls: W/A/S/D move, Space jump, Shift sprint, arrow keys look, Esc quit.
"""
from __future__ import annotations
import base64
import time
import tkinter as tk
from .game import Game

class Demo:
    def __init__(self, root):
        self.root=root
        self.game=Game(240,180)
        self.keys=set()
        self.last=time.perf_counter()
        self.image=tk.PhotoImage(width=self.game.width,height=self.game.height)
        self.view=tk.Label(root,image=self.image,bd=0)
        self.view.pack()
        self.status=tk.Label(root,anchor="w",text="",font=("TkFixedFont",9))
        self.status.pack(fill="x")
        root.title("MCPE Python Rewrite — renderer prototype")
        root.resizable(False,False)
        root.bind("<KeyPress>",self.key_down)
        root.bind("<KeyRelease>",self.key_up)
        root.protocol("WM_DELETE_WINDOW",root.destroy)
        root.focus_force()
        self.tick()

    def key_down(self,event):
        key=event.keysym.lower()
        if key=="escape":
            self.root.destroy()
            return
        if key=="up": self.game.pitch-=.08
        elif key=="down": self.game.pitch+=.08
        elif key=="left": self.game.yaw-=.08
        elif key=="right": self.game.yaw+=.08
        elif key=="space" and "space" not in self.keys: self.game.jump()
        self.keys.add(key)

    def key_up(self,event):
        self.keys.discard(event.keysym.lower())

    def tick(self):
        now=time.perf_counter()
        dt=min(.05,now-self.last)
        self.last=now
        self.game.step(self.keys,dt)
        ppm=self.game.render()
        encoded=base64.b64encode(ppm).decode("ascii")
        try:
            self.image=tk.PhotoImage(data=encoded,format="PPM")
            self.view.configure(image=self.image)
        except tk.TclError as exc:
            self.status.configure(text="Could not update image: "+str(exc))
        self.status.configure(text=f"WASD move  Space jump  Shift sprint  Arrows look  Esc quit   "
                                   f"XYZ {self.game.player_x:.1f}, {self.game.player_y:.1f}, {self.game.player_z:.1f}   "
                                   f"Triangles {self.game.last_triangles}")
        self.root.after(33,self.tick)

def main():
    root=tk.Tk()
    Demo(root)
    root.mainloop()

if __name__=="__main__":
    main()
