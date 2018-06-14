"""
The GUI for the SPL -> Java translator, needed because reasons.
:author: Ryan Dancy
"""

import tkinter as tk
from splerror import SplError
import translator

class GUI:
    def __init__(self, master):
        self.master = master
        master.title('Shakespeare Programming Language to Java translator.')

        # title onscreen
        self.label = tk.Label(master, text='Shakespeare Programming Language to Java Translator')
        self.label.pack()

        self.texts_frame = tk.Frame(master)

        # SPL title + text + scrollbar on left
        self.spl_frame = tk.Frame(self.texts_frame)
        self.spl_label = tk.Label(self.spl_frame, text='SPL input')
        self.spl_label.pack()
        self.spl_scroll = tk.Scrollbar(self.spl_frame)
        self.spl_text = tk.Text(self.spl_frame, height=50, width=80)
        self.spl_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.spl_text.pack(side=tk.LEFT, fill=tk.Y)
        self.spl_scroll.config(command=self.spl_text.yview)
        self.spl_text.config(yscrollcommand=self.spl_scroll.set)
        self.spl_frame.pack(side=tk.LEFT)

        # Java title + text + scrollbar on right
        self.java_frame = tk.Frame(self.texts_frame)
        self.java_label = tk.Label(self.java_frame, text='Java output')
        self.java_label.pack()
        self.java_scroll = tk.Scrollbar(self.java_frame)
        self.java_text = tk.Text(self.java_frame, height=50, width=80)
        self.java_scroll.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.java_text.pack(side=tk.LEFT, fill=tk.BOTH)
        self.java_scroll.config(command=self.java_text.yview)
        self.java_text.config(yscrollcommand=self.java_scroll.set, state=tk.DISABLED)
        self.java_text.tag_configure('error', foreground='#F00')
        self.java_frame.pack(side=tk.RIGHT)

        self.texts_frame.pack(fill=tk.BOTH)

        # "translate" button
        self.translate_button = tk.Button(master, text='Translate', command=self.translate, bg='#888', fg='black')
        self.translate_button.pack(side=tk.BOTTOM, fill=tk.X)

    def translate(self):
        # attempt to translate it, put results in self.java_text
        self.java_text.config(state=tk.NORMAL)
        self.java_text.delete(1.0, tk.END)
        try:
            java = translator.translate(self.spl_text.get('1.0', tk.END + '-1c'), 'Main')
        except SplError as e:
            self.java_text.insert(tk.END, e.args[0], 'error')
        else:
            self.java_text.insert(tk.END, java)
        self.java_text.config(state=tk.DISABLED)

root = tk.Tk()
gui = GUI(root)
root.mainloop()
