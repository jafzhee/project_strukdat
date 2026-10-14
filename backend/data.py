import csv

class Pesanan:
    __slots__ = ("oid", "pelanggan", "resto", "menu", "harga", "prioritas", "masuk", "selesai", "status")

    def __init__(self, oid, pelanggan, resto, menu, harga, prioritas, masuk, selesai, status):
        self.oid = oid
        self.pelanggan = pelanggan
        self.resto = resto
        self.menu = menu
        self.harga = harga
        self.prioritas = prioritas
        self.masuk = masuk
        self.selesai = selesai
        self.status = status

    def baris(self):
        return [self.oid, self.pelanggan, self.resto, self.menu, "{:,}".format(self.harga).replace(",", "."),
                jam(self.masuk), jam(self.selesai), self.status]

def jam(detik):
    if detik is None:
        return "-"
    detik = detik % 86400
    return "%02d:%02d:%02d" % (detik // 3600, (detik % 3600) // 60, detik % 60)

def muat_csv(path):
    hasil = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r)
        for b in r:
            sel = int(b[7]) if b[7] != "" else None
            hasil.append(Pesanan(b[0], b[1], b[2], b[3], int(b[4]), int(b[5]), int(b[6]), sel, b[8]))
    return hasil
