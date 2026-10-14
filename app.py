"""python app.py  -> jalankan aplikasi 2EZ4U."""
import os
import tkinter as tk

from frontend.ui import Aplikasi


def main():
    akar = os.path.dirname(os.path.abspath(__file__))
    root = tk.Tk()
    Aplikasi(root, os.path.join(akar, "data", "pesanan.csv"))
    root.mainloop()


if __name__ == "__main__":
    main()
