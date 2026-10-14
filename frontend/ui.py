import os
import time

from backend.data import Pesanan, muat_csv, jam
from backend.m1_pesanan import Array, LinkList, tambah_ke
from backend.m2_antrean import Layanan, ke_postfix, hitung
from backend.m3_laporan import (Pencacah, insertion_sort, merge_sort, linear_search,
                                binary_search, ambil_kunci, kunci_oid)

BATAS_INSERTION = 20000
BARIS_LOAD = 1000          # berapa baris pertama yang ditampilkan setelah Load
KOLOM_PESANAN = ["#", "oid", "pelanggan", "resto", "menu", "harga", "masuk", "selesai", "status"]

class Galat(Exception):
    """Kesalahan input/keadaan yang ditampilkan ramah di UI."""

class Param:
    def __init__(self, label, default="", pilihan=None, hint=""):
        self.label, self.default, self.pilihan, self.hint = label, default, pilihan, hint

class Menu:
    def __init__(self, grup, nama, judul, deskripsi, params, fungsi, tombol="JALANKAN"):
        self.grup, self.nama, self.judul, self.deskripsi = grup, nama, judul, deskripsi
        self.params, self.fungsi, self.tombol = params, fungsi, tombol

class Hasil:
    def __init__(self, ringkas, kolom=None, baris=None, modul="", catatan=""):
        self.ringkas, self.kolom, self.baris = ringkas, kolom or [], baris or []
        self.modul, self.catatan = modul, catatan

def ribu(n):
    return "{:,}".format(n).replace(",", ".")

def tabel(pesanan_list):
    return [[i + 1] + p.baris() for i, p in enumerate(pesanan_list)]

def detail(p):
    return [["oid", p.oid], ["pelanggan", p.pelanggan], ["resto", p.resto], ["menu", p.menu],
            ["harga", ribu(p.harga)], ["prioritas", p.prioritas], ["masuk", jam(p.masuk)],
            ["selesai", jam(p.selesai)], ["status", p.status]]

def _int(teks, nama):
    try:
        return int(teks.strip().replace(".", ""))
    except ValueError:
        raise Galat("%s harus berupa bilangan bulat" % nama)

JENIS = [("REGULER", 3), ("PRIORITAS", 2), ("VIP", 1)]

class Mesin:
    def __init__(self, path_csv):
        self.path = path_csv
        self.data = self.arr = self.ll = self.layanan = self.indeks = None
        self.indeks_ms = 0.0
        self.indeks_banding = 0
        self.oid_berikut = 200001
    def _siap(self):
        if self.data is None:
            raise Galat("Data belum dimuat. Klik menu Load dulu.")

    def form_pesanan(self):
        """Isian form untuk semua menu tambah/enqueue (urutan = v[0..3])."""
        return [Param("Nama pelanggan", "Pelanggan Baru"),
                Param("Nama restoran", "kantin-pusat"),
                Param("Nama menu", "paket-siang"),
                Param("Harga (angka)", "15000", hint="contoh: 15000")]

    def _baru(self, v, prioritas):
        nama, resto, menu = v[0].strip(), v[1].strip(), v[2].strip()
        if nama == "" or resto == "" or menu == "":
            raise Galat("Nama pelanggan, restoran, dan menu tidak boleh kosong")
        harga = _int(v[3], "Harga")
        if harga <= 0:
            raise Galat("Harga harus lebih dari 0")
        t = time.localtime()
        p = Pesanan("O-%06d" % self.oid_berikut, nama, resto, menu, harga,
                    prioritas, t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec, None, "ANTRE")
        self.oid_berikut += 1
        return p
    def load(self, v):
        if not os.path.exists(self.path):
            raise Galat("File data tidak ada. Jalankan: python tools/generate_data.py")
        t = [time.perf_counter()]
        data = muat_csv(self.path); t.append(time.perf_counter())
        arr = Array()
        for p in data:
            arr.append(p)
        t.append(time.perf_counter())
        ll = LinkList()
        for p in data:
            ll.append(p)
        t.append(time.perf_counter())
        antre, n_done, n_cancel = [], 0, 0
        for p in data:
            if p.status == "ANTRE":
                antre.append(p)
            elif p.status == "DONE":
                n_done += 1
            else:
                n_cancel += 1
        lay = Layanan(antre); t.append(time.perf_counter())
        self.data, self.arr, self.ll, self.layanan = data, arr, ll, lay
        self.indeks, self.oid_berikut = None, len(data) + 1
        ms = lambda i: "%.1f ms" % ((t[i + 1] - t[i]) * 1000)
        tampil = [[i + 1, p.oid, p.pelanggan, p.resto, p.menu, "Rp " + ribu(p.harga), p.prioritas, p.status]
                  for i, p in enumerate(data[:BARIS_LOAD])]
        return Hasil("%s pesanan dimuat (%s ANTRE) | DONE %s, CANCEL %s\n"
                     "baca CSV %s | isi Array %s | isi LinkList %s | isi 2 antrean %s" %
                     (ribu(len(data)), ribu(len(antre)), ribu(n_done), ribu(n_cancel), ms(0), ms(1), ms(2), ms(3)),
                     ["NO", "OID", "PELANGGAN", "RESTO", "MENU", "HARGA", "PRIORITAS", "STATUS"], tampil, "DATA"
                     , "Menampilkan %s baris pertama dari %s. Gunakan LIHAT PESANAN untuk membuka baris lain." %
                     (ribu(BARIS_LOAD), ribu(len(data))))

    def info(self):
        """Teks untuk pojok kanan header."""
        if self.data is None:
            return "Data: belum dimuat"
        return "Data: %s baris | Antre: %s" % (ribu(len(self.data)), ribu(len(self.layanan.circ)))
    def _struk(self, jenis):
        self._siap()
        return self.arr if jenis == "array" else self.ll

    def m1_lihat(self, jenis, v):
        s = self._struk(jenis)
        i = _int(v[0], "Indeks")
        if i < 0 or i >= len(s):
            raise Galat("Indeks harus 0..%s" % ribu(len(s) - 1))
        k0 = s.kerja
        p = s.get(i)
        return Hasil("Pesanan indeks %s dari %s. %s: %s" % (ribu(i), ribu(len(s)), s.satuan, ribu(s.kerja - k0)),
                     ["kolom", "isi"], detail(p), "M1 - " + ("larik" if jenis == "array" else "rantai"),
                     "Array: akses O(1), tidak ada yang digeser. LinkList: harus menelusur i simpul dari head, O(n).")

    def m1_tambah(self, jenis, prioritas, v):
        s = self._struk(jenis)
        p = self._baru(v, prioritas)
        k0, n = s.kerja, len(s)
        pos = tambah_ke(s, p)
        return Hasil("%s masuk di indeks %s (dari %s). %s: %s. Panjang sekarang %s." %
                     (p.oid, ribu(pos), ribu(n + 1), s.satuan, ribu(s.kerja - k0), ribu(len(s))),
                     ["kolom", "isi"], detail(p), "M1 - " + ("larik" if jenis == "array" else "rantai"),
                     "REGULER=belakang, PRIORITAS=tengah (n/2), VIP=depan. Bandingkan biayanya di Array vs LinkList.")

    def m1_hapus(self, jenis, v):
        s = self._struk(jenis)
        i = _int(v[0], "Indeks")
        if i < 0 or i >= len(s):
            raise Galat("Indeks harus 0..%s" % ribu(len(s) - 1))
        k0 = s.kerja
        p = s.remove(i)
        return Hasil("%s dihapus dari indeks %s. %s: %s. Panjang sekarang %s." %
                     (p.oid, ribu(i), s.satuan, ribu(s.kerja - k0), ribu(len(s))),
                     ["kolom", "isi"], detail(p), "M1 - " + ("larik" if jenis == "array" else "rantai"))
    def m2_postfix(self, v):
        jejak = []
        try:
            pf = ke_postfix(v[0], jejak)
            total = hitung(pf, jejak)
        except ValueError as e:
            raise Galat("Ekspresi salah: %s" % e)
        return Hasil("Struk  : %s\nPostfix: %s\nTOTAL  : Rp %s" % (v[0].strip(), " ".join(pf), ribu(int(total))
                     if total == int(total) else total),
                     ["langkah", "token", "tindakan", "stack", "output"], jejak, "M2 - stack",
                     "Baris 1.x = konversi infix->postfix, 2.x = evaluasi. Yang di-pop pertama adalah operand KANAN.")

    def _aksi_ringkas(self, aksi):
        if aksi[0] == "ENQUEUE":
            return "ENQUEUE " + aksi[1].oid, [aksi[1]]
        return "DEQUEUE x%d dari antrean %s" % (len(aksi[2]), aksi[1]), aksi[2]

    def m2_undo(self, v):
        self._siap()
        L = self.layanan
        aksi = L.undo_last()
        if aksi is None:
            raise Galat("Tumpukan undo kosong, tidak ada yang dibatalkan.")
        teks, daftar = self._aksi_ringkas(aksi)
        return Hasil("Dibatalkan: %s.\nPanjang antrean: naif %s, circular %s. Tumpukan undo %d, redo %d." %
                     (teks, ribu(len(L.naif)), ribu(len(L.circ)), len(L.undo), len(L.redo)),
                     KOLOM_PESANAN, tabel(daftar), "M2 - stack",
                     "Kebalikan enqueue = keluarkan dari belakang. Kebalikan dequeue = kembalikan ke DEPAN.")

    def m2_redo(self, v):
        self._siap()
        L = self.layanan
        aksi = L.redo_last()
        if aksi is None:
            raise Galat("Tumpukan redo kosong, tidak ada yang diulang.")
        teks, daftar = self._aksi_ringkas(aksi)
        return Hasil("Diulang: %s.\nPanjang antrean: naif %s, circular %s. Tumpukan undo %d, redo %d." %
                     (teks, ribu(len(L.naif)), ribu(len(L.circ)), len(L.undo), len(L.redo)),
                     KOLOM_PESANAN, tabel(daftar), "M2 - stack",
                     "Redo mengerjakan ULANG aksi aslinya, bukan kebalikannya.")

    def m2_enqueue(self, v):
        self._siap()
        p = self._baru(v, 3)
        self.layanan.enqueue(p)
        L = self.layanan
        return Hasil("%s masuk ke belakang KEDUA antrean. Panjang: naif %s, circular %s." %
                     (p.oid, ribu(len(L.naif)), ribu(len(L.circ))), ["kolom", "isi"], detail(p), "M2 - queue",
                     "enqueue sama murahnya di kedua versi; selisih baru muncul di dequeue.")

    def m2_dequeue(self, versi, v):
        self._siap()
        k = _int(v[0], "Jumlah")
        if k < 1:
            raise Galat("Jumlah minimal 1")
        L = self.layanan
        q = L.naif if versi == "naif" else L.circ
        g0 = q.geser
        keluar = L.dequeue(versi, k)
        if len(keluar) == 0:
            raise Galat("Antrean kosong.")
        geser = q.geser - g0
        extra = ("Total %s elemen digeser, rata-rata %s per pesanan." % (ribu(geser), ribu(geser // len(keluar)))
                 if versi == "naif" else
                 "Tidak ada elemen digeser. front=%s, rear=%s, kapasitas %s." % (ribu(q.front), ribu(q.rear), ribu(q.kapasitas)))
        return Hasil("%d pesanan keluar dari depan antrean %s.\n%s Sisa antrean: %s." %
                     (len(keluar), versi, extra, ribu(len(q))),
                     KOLOM_PESANAN, tabel(keluar), "M2 - queue " + ("naif" if versi == "naif" else "circular"),
                     "Isi dengan jumlah besar (mis. 100) lalu bandingkan waktu menu NAIF vs CIRCULAR.")
    def m3_sort(self, algo, v):
        self._siap()
        n = _int(v[0], "Jumlah baris")
        if n < 1 or n > len(self.data):
            raise Galat("Jumlah baris harus 1..%s" % ribu(len(self.data)))
        if algo == "insertion" and n > BATAS_INSERTION:
            raise Galat("DITOLAK: batasnya %s baris untuk insertion sort, pakai merge sort untuk data besar." % ribu(BATAS_INSERTION))
        kunci = v[1]
        A, c = self.data[:n], Pencacah()
        (insertion_sort if algo == "insertion" else merge_sort)(A, ambil_kunci(kunci), c)
        return Hasil("%s pesanan terurut menurut %s.\n%s perbandingan, %s pemindahan." %
                     (ribu(n), kunci, ribu(c.banding), ribu(c.pindah)),
                     KOLOM_PESANAN, tabel(A[:500]), "M3 - " + ("insertion sort" if algo == "insertion" else "merge sort"),
                     "Lipat-duakan n: insertion sort ~4x perbandingan, merge sort ~2x. Keduanya stabil (kunci sama = urutan asli).")

    def _target(self, teks):
        t = teks.strip().upper()
        if t.isdigit():
            t = "O-%06d" % int(t)
        return t

    def m3_linear(self, v):
        self._siap()
        target, c = self._target(v[0]), Pencacah()
        i = linear_search(self.data, target, kunci_oid, c)
        if i < 0:
            return Hasil("%s tidak ditemukan setelah %s perbandingan." % (target, ribu(c.banding)), modul="M3 - linear")
        return Hasil("Ditemukan pada indeks %s.\n%s perbandingan." % (ribu(i), ribu(c.banding)),
                     ["kolom", "isi"], detail(self.data[i]), "M3 - linear",
                     "Tidak butuh data terurut, tetapi kasus terburuk menyentuh seluruh n baris.")

    def m3_binary(self, v):
        self._siap()
        target, bangun = self._target(v[0]), ""
        if self.indeks is None:
            c0, t0 = Pencacah(), time.perf_counter()
            A = self.data[:]
            merge_sort(A, kunci_oid, c0)
            self.indeks, self.indeks_ms = A, (time.perf_counter() - t0) * 1000
            self.indeks_banding = c0.banding
            bangun = "(baru dibangun)"
        c = Pencacah()
        i = binary_search(self.indeks, target, kunci_oid, c)
        awal = "Daftar terurut oid dibangun sekali dengan merge sort: %.2f ms, %s perbandingan %s.\n" % (
            self.indeks_ms, ribu(self.indeks_banding), bangun)
        if i < 0:
            return Hasil(awal + "%s tidak ditemukan setelah %d perbandingan." % (target, c.banding), modul="M3 - binary")
        return Hasil(awal + "Ditemukan pada baris ke-%s dari %s.\n%d perbandingan, bandingkan dengan linear search." %
                     (ribu(i + 1), ribu(len(self.indeks)), c.banding),
                     ["kolom", "isi"], detail(self.indeks[i]), "M3 - binary",
                     "Binary search menuntut data terurut menurut kunci yang dicari; ongkos pengurutan dibayar sekali di awal.")
    def daftar_menu(self):
        P = Param
        pilih_kunci = ["oid", "harga", "selesai"]
        M = []
        M.append(Menu("DATA", "Load", "Load data", "Baca pesanan.csv lalu isi Array, LinkList, dan kedua antrean.",
                      [], self.load, "LOAD"))
        for jenis, nm in (("array", "ARRAY"), ("linked", "LINKEDLIST")):
            j = "array" if jenis == "array" else "linked"
            M.append(Menu("M1 - DATA PESANAN", nm + " - LIHAT PESANAN", nm + ": lihat pesanan ke-i",
                          "Akses berdasarkan indeks. Array O(1), LinkList O(n).",
                          [P("Indeks", "100000", hint="0 sampai n-1")],
                          lambda v, j=j: self.m1_lihat(j, v), "LIHAT"))
            for nama_jenis, pri in JENIS:
                M.append(Menu("M1 - DATA PESANAN", "%s - TAMBAH PESANAN %s" % (nm, nama_jenis),
                              "%s: pesanan %s" % (nm, nama_jenis),
                              "Sisip sesuai jenis: REGULER belakang, PRIORITAS tengah, VIP depan.",
                              self.form_pesanan(),
                              lambda v, j=j, pri=pri: self.m1_tambah(j, pri, v), "TAMBAH"))
            M.append(Menu("M1 - DATA PESANAN", nm + " - HAPUS PESANAN", nm + ": hapus pesanan ke-i",
                          "Cabut pesanan dari barisan. Keduanya O(n).",
                          [P("Indeks", "100000", hint="0 sampai n-1")],
                          lambda v, j=j: self.m1_hapus(j, v), "HAPUS"))
        g = "M2 - STACK DAN QUEUE"
        M.append(Menu(g, "STACK - POSTFIX (MESIN KASIR)", "Stack: hitung struk lewat postfix",
                      "Struk infix diubah ke postfix (tahap 1) lalu dievaluasi (tahap 2), keduanya memakai stack.",
                      [P("Struk belanja (infix)", "( 3 * 12000 ) + ( 2 * 8500 ) - 5000", hint="angka, + - * / dan tanda kurung")],
                      self.m2_postfix, "HITUNG"))
        M.append(Menu(g, "STACK - UNDO", "Stack: batalkan aksi antrean terakhir",
                      "Ambil catatan teratas tumpukan undo, lalu jalankan kebalikannya.", [], self.m2_undo, "UNDO"))
        M.append(Menu(g, "STACK - REDO", "Stack: kerjakan lagi aksi yang dibatalkan",
                      "Ambil catatan teratas tumpukan redo lalu kerjakan ulang aksi aslinya.", [], self.m2_redo, "REDO"))
        M.append(Menu(g, "QUEUE - ENQUEUE", "Queue: pesanan baru masuk ke belakang",
                      "Menambah di ujung belakang kedua antrean sekaligus (naif dan circular).",
                      self.form_pesanan(), self.m2_enqueue, "ENQUEUE"))
        M.append(Menu(g, "QUEUE - DEQUEUE NAIF", "Queue naif: ambil dari depan dengan menggeser isi",
                      "Mengambil indeks 0 lalu menggeser seluruh sisa satu petak ke kiri. Biayanya O(n) setiap dequeue.",
                      [P("Berapa kali dequeue", "2", hint="sampai panjang antrean; coba 1 lalu 100")],
                      lambda v: self.m2_dequeue("naif", v), "DEQUEUE"))
        M.append(Menu(g, "QUEUE - DEQUEUE CIRCULAR", "Queue circular: ambil dari depan dengan memajukan penunjuk",
                      "Hanya penunjuk front yang maju, isi larik tidak digeser sama sekali. O(1).",
                      [P("Berapa kali dequeue", "2", hint="sampai panjang antrean; coba 1 lalu 100")],
                      lambda v: self.m2_dequeue("circular", v), "DEQUEUE"))
        g = "M3 - SORT DAN SEARCH"
        M.append(Menu(g, "SORT - INSERTION SORT", "Sort: insertion sort, O(n^2)",
                      "Setiap elemen digeser mundur sampai menemukan tempatnya. Sederhana, tetapi kerjanya tumbuh kuadratik.",
                      [P("Jumlah baris diurutkan", "2000", hint="diambil dari awal data; maks 20.000"),
                       P("Diurutkan menurut", "harga", pilih_kunci)],
                      lambda v: self.m3_sort("insertion", v), "URUTKAN"))
        M.append(Menu(g, "SORT - MERGE SORT", "Sort: merge sort, O(n log n)",
                      "Larik dibelah dua terus-menerus, lalu potongan yang sudah terurut disatukan kembali.",
                      [P("Jumlah baris diurutkan", "4000", hint="diambil dari awal data; boleh sampai 200.000"),
                       P("Diurutkan menurut", "harga", pilih_kunci)],
                      lambda v: self.m3_sort("merge", v), "URUTKAN"))
        M.append(Menu(g, "SEARCH - LINEAR SEARCH", "Search: linear search, O(n)",
                      "Memeriksa pesanan satu per satu dari depan. Tidak menuntut data terurut.",
                      [P("Nomor pesanan (oid)", "O-137442", hint="format O-000001 sampai O-200000, atau cukup angkanya")],
                      self.m3_linear, "CARI"))
        M.append(Menu(g, "SEARCH - BINARY SEARCH", "Search: binary search, O(log n)",
                      "Membuang separuh sisa daftar pada setiap perbandingan. Menuntut daftar terurut menurut oid.",
                      [P("Nomor pesanan (oid)", "O-137442", hint="format O-000001 sampai O-200000, atau cukup angkanya")],
                      self.m3_binary, "CARI"))
        return M

import time
import tkinter as tk
from tkinter import ttk

MAKS_BARIS = 1000
COKELAT = "#63352F"
KREM = "#FFF9E9"
KARAMEL = "#FFD77A"
KAKAO = "#63352F"
MERAH = "#C94747"
HIJAU = "#95B83D"
KREM_MUDA = "#FFFDF6"
PUTIH = "#FFFFFF"

def fmt_waktu(detik):
    ms = detik * 1000
    teks = ("%.2f s" % (ms / 1000)) if ms >= 1000 else ("%.2f ms" % ms)
    return teks.replace(".", ",")

class Aplikasi:
    def __init__(self, root, path_data):
        self.root = root
        root.title("2EZ4U Food Delivery")
        root.geometry("1180x780")
        root.minsize(900, 600)
        self.mesin = Mesin(path_data)
        self.menus = self.mesin.daftar_menu()
        self.tombol_menu, self.entri, self.aktif = [], [], None
        self._gaya()
        self._bangun()
        self.pilih(0)
    def _gaya(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure(".", font=("Segoe UI", 9))
        s.configure("TFrame", background=KREM)
        s.configure("TLabel", background=KREM, foreground=KAKAO)
        s.configure("Menu.TButton", anchor="w", padding=(7, 4), background=KREM, foreground=KAKAO)
        s.configure("Aktif.TButton", anchor="w", padding=(7, 4), background=HIJAU,
                    foreground=PUTIH, font=("Segoe UI", 9, "bold"))
        s.map("Menu.TButton", background=[("active", "#FFE9B3")])
        s.configure("Aksi.TButton", background=MERAH, foreground=PUTIH,
                    padding=(18, 7), font=("Segoe UI", 9, "bold"))
        s.map("Aksi.TButton", background=[("active", "#AC3737")])
        s.configure("Treeview", rowheight=23, background=PUTIH,
                    fieldbackground=PUTIH, foreground=KAKAO)
        s.configure("Treeview.Heading", background=KARAMEL, foreground=KAKAO,
                    font=("Segoe UI", 9, "bold"))

    def _bangun(self):
        kepala = tk.Frame(self.root, bg=COKELAT)
        kepala.pack(fill="x")
        tk.Label(kepala, text="2EZ4U Food Delivery", bg=COKELAT, fg=PUTIH, anchor="w",
                 font=("Segoe UI", 13, "bold"), padx=12, pady=9).pack(side="left")
        self.info = tk.Label(kepala, text=self.mesin.info(), bg=COKELAT, fg=KREM, padx=12,
                             font=("TkDefaultFont", 9))
        self.info.pack(side="right")
        self.status = tk.Label(self.root, text="siap", bg=KAKAO, fg=PUTIH, anchor="w", padx=12, pady=3,
                               font=("Consolas", 9))
        self.status.pack(side="bottom", fill="x")

        badan = ttk.Frame(self.root)
        badan.pack(fill="both", expand=True)
        badan.columnconfigure(1, weight=1)
        badan.rowconfigure(0, weight=1)

        # kiri
        kiri = ttk.Frame(badan, width=270)
        kiri.grid(row=0, column=0, sticky="ns")
        kiri.grid_propagate(False)
        kanvas = tk.Canvas(kiri, width=250, highlightthickness=0, bg=KREM)
        sb = ttk.Scrollbar(kiri, orient="vertical", command=kanvas.yview)
        isi = ttk.Frame(kanvas)
        isi.bind("<Configure>", lambda e: kanvas.configure(scrollregion=kanvas.bbox("all")))
        kanvas.create_window((0, 0), window=isi, anchor="nw", width=248)
        kanvas.configure(yscrollcommand=sb.set)
        kanvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        kanvas.bind_all("<MouseWheel>", lambda e: kanvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        kanvas.bind_all("<Button-4>", lambda e: kanvas.yview_scroll(-1, "units"))
        kanvas.bind_all("<Button-5>", lambda e: kanvas.yview_scroll(1, "units"))
        grup_terakhir = None
        for i, m in enumerate(self.menus):
            if m.grup != grup_terakhir:
                grup_terakhir = m.grup
                ttk.Label(isi, text=m.grup, font=("Segoe UI", 8, "bold"), foreground=COKELAT).pack(
                    anchor="w", padx=6, pady=(8, 1))
            b = ttk.Button(isi, text=m.nama, style="Menu.TButton", command=lambda i=i: self.pilih(i))
            b.pack(fill="x", padx=4, pady=1)
            self.tombol_menu.append(b)

        # kanan
        kanan = ttk.Frame(badan, padding=(14, 10))
        kanan.grid(row=0, column=1, sticky="nsew")
        kanan.columnconfigure(0, weight=1)
        kanan.rowconfigure(4, weight=1)
        self.judul = ttk.Label(kanan, font=("Segoe UI", 12, "bold"))
        self.judul.grid(row=0, column=0, sticky="w")
        self.desk = ttk.Label(kanan, foreground=KAKAO, wraplength=820, justify="left")
        self.desk.grid(row=1, column=0, sticky="w", pady=(0, 6))
        self.form = ttk.Frame(kanan)
        self.form.grid(row=2, column=0, sticky="ew")
        self.ringkas = tk.Label(kanan, anchor="w", justify="left", wraplength=820, font=("Consolas", 10), bg=KREM, fg=KAKAO)
        self.ringkas.grid(row=3, column=0, sticky="ew", pady=8)
        tbl = ttk.Frame(kanan)
        tbl.grid(row=4, column=0, sticky="nsew")
        tbl.columnconfigure(0, weight=1)
        tbl.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(tbl, show="headings")
        v = ttk.Scrollbar(tbl, orient="vertical", command=self.tree.yview)
        h = ttk.Scrollbar(tbl, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        v.grid(row=0, column=1, sticky="ns")
        h.grid(row=1, column=0, sticky="ew")
        ttk.Label(kanan, text="COMMAND", font=("TkDefaultFont", 8, "bold")).grid(row=5, column=0, sticky="w", pady=(8, 0))
        self.log = tk.Text(kanan, height=5, font=("Consolas", 9), state="disabled", bg=PUTIH, fg=KAKAO, insertbackground=KAKAO, relief="flat")
        self.log.grid(row=6, column=0, sticky="ew")
        self.catatan = tk.Label(kanan, anchor="w", justify="left", wraplength=820, bg="#E8D2B8", fg=KAKAO,
                                font=("TkDefaultFont", 9), padx=8, pady=4)
        self.catatan.grid(row=7, column=0, sticky="ew", pady=(6, 0))
    def pilih(self, i):
        self.aktif = self.menus[i]
        for j, b in enumerate(self.tombol_menu):
            b.configure(style="Aktif.TButton" if j == i else "Menu.TButton")
        m = self.aktif
        self.judul.configure(text=m.judul)
        self.desk.configure(text=m.deskripsi)
        for w in self.form.winfo_children():
            w.destroy()
        self.entri = []
        for r, p in enumerate(m.params):
            ttk.Label(self.form, text=p.label, font=("Segoe UI", 9, "bold")).grid(row=r * 2, column=0, sticky="w")
            if p.pilihan:
                w = ttk.Combobox(self.form, values=p.pilihan, state="readonly", width=14)
                w.set(p.default or p.pilihan[0])
            else:
                w = ttk.Entry(self.form, width=44 if len(p.default) > 20 else 22)
                w.insert(0, p.default)
            w.grid(row=r * 2 + 1, column=0, sticky="w", pady=(0, 2))
            w.bind("<Return>", lambda e: self.jalankan())
            if p.hint:
                ttk.Label(self.form, text=p.hint, foreground="#888", font=("Segoe UI", 8)).grid(
                    row=r * 2 + 1, column=1, sticky="w", padx=8)
            self.entri.append(w)
        ttk.Button(self.form, text="" + m.tombol, style="Aksi.TButton",
                   command=self.jalankan).grid(
            row=len(m.params) * 2, column=0, columnspan=2, pady=(8, 2), sticky="w")
        self.form.columnconfigure(1, weight=1)
        self.ringkas.configure(text="", fg="black")
        self.catatan.configure(text="")
        self._isi_tabel([], [])

    def _isi_tabel(self, kolom, baris):
        self.tree.delete(*self.tree.get_children())
        ids = ["c%d" % i for i in range(len(kolom))]
        self.tree.configure(columns=ids)
        for cid, nama in zip(ids, kolom):
            lebar = 60 if nama in ("#", "NO") else (90 if nama in ("HARGA", "PRIORITAS", "STATUS") else (260 if nama in ("tindakan", "isi") else 130))
            self.tree.heading(cid, text=nama)
            self.tree.column(cid, width=lebar, minwidth=50, anchor="w", stretch=True)
        for b in baris[:MAKS_BARIS]:
            self.tree.insert("", "end", values=[str(x) for x in b])

    def _catat(self, nama, modul, detik):
        self.log.configure(state="normal")
        self.log.insert("1.0", "%-30s -> %-20s %s\n" % (nama, modul, fmt_waktu(detik)))
        self.log.configure(state="disabled")

    def jalankan(self):
        m = self.aktif
        nilai = [w.get() for w in self.entri]
        self.ringkas.configure(text="memproses...", fg=KAKAO)
        self.root.update_idletasks()
        t0 = time.perf_counter()
        try:
            hasil = m.fungsi(nilai)
        except Galat as e:
            self.ringkas.configure(text=str(e), fg=MERAH)
            self._isi_tabel([], [])
            self.catatan.configure(text="")
            return
        except Exception as e:
            self.ringkas.configure(text="Galat: %s" % e, fg=MERAH)
            return
        dt = time.perf_counter() - t0
        self.ringkas.configure(text=hasil.ringkas, fg="black")
        self._isi_tabel(hasil.kolom, hasil.baris)
        cat = hasil.catatan
        if len(hasil.baris) > MAKS_BARIS:
            cat = ("Menampilkan %d dari %d baris. " % (MAKS_BARIS, len(hasil.baris))) + cat
        self.catatan.configure(text=cat)
        self._catat(m.nama.lower().replace(" - ", "_").replace(" ", "_"), hasil.modul or "-", dt)
        self.status.configure(text="[%s] %s" % (hasil.modul or "-", fmt_waktu(dt)))
        self.info.configure(text=self.mesin.info())
