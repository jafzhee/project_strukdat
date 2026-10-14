class Array:
    satuan = "elemen digeser"

    def __init__(self, kapasitas=4):
        self.data = [None] * kapasitas
        self.n = 0
        self.kerja = 0 # total elemen digeser
        self.salin = 0 # total elemen disalin saat tumbuh

    def __len__(self):
        return self.n

    def _cek(self, i):
        if i < 0 or i >= self.n:
            raise IndexError("indeks %d di luar 0..%d" % (i, self.n - 1))

    def _tumbuh(self):
        baru = [None] * (len(self.data) * 2)
        for i in range(self.n):
            baru[i] = self.data[i]
        self.salin += self.n
        self.data = baru

    def append(self, v): # O(1) amortized
        if self.n == len(self.data):
            self._tumbuh()
        self.data[self.n] = v
        self.n += 1

    def insert(self, i, v): # O(n): geser ke kanan
        if i < 0 or i > self.n:
            raise IndexError("posisi sisip tidak valid")
        if self.n == len(self.data):
            self._tumbuh()
        for j in range(self.n, i, -1):
            self.data[j] = self.data[j - 1]
        self.kerja += self.n - i
        self.data[i] = v
        self.n += 1

    def get(self, i): # O(1)
        self._cek(i)
        return self.data[i]

    def remove(self, i): # O(n): geser ke kiri
        self._cek(i)
        v = self.data[i]
        for j in range(i, self.n - 1):
            self.data[j] = self.data[j + 1]
        self.kerja += self.n - 1 - i
        self.n -= 1
        self.data[self.n] = None
        return v

class Simpul:
    __slots__ = ("nilai", "next")

    def __init__(self, nilai):
        self.nilai = nilai
        self.next = None

class LinkList:
    satuan = "simpul ditelusuri"

    def __init__(self):
        self.head = None
        self.tail = None
        self.n = 0
        self.kerja = 0 # total simpul ditelusuri

    def __len__(self):
        return self.n

    def _cek(self, i):
        if i < 0 or i >= self.n:
            raise IndexError("indeks %d di luar 0..%d" % (i, self.n - 1))

    def append(self, v):  # O(1) berkat tail
        s = Simpul(v)
        if self.tail is None:
            self.head = self.tail = s
        else:
            self.tail.next = s
            self.tail = s
        self.n += 1

    def prepend(self, v): # O(1)
        s = Simpul(v)
        s.next = self.head
        self.head = s
        if self.tail is None:
            self.tail = s
        self.n += 1

    def _simpul(self, i):
        cur = self.head
        for _ in range(i):
            cur = cur.next
        self.kerja += i
        return cur

    def insert(self, i, v):
        if i < 0 or i > self.n:
            raise IndexError("posisi sisip tidak valid")
        if i == 0:
            self.prepend(v)
        elif i == self.n:
            self.append(v)
        else: # O(n) telusur sampai simpul i-1
            sebelum = self._simpul(i - 1)
            s = Simpul(v)
            s.next = sebelum.next
            sebelum.next = s
            self.n += 1

    def get(self, i): # O(n)
        self._cek(i)
        return self._simpul(i).nilai

    def remove(self, i):
        self._cek(i)
        if i == 0:
            s = self.head
            self.head = s.next
            if self.head is None:
                self.tail = None
        else:
            sebelum = self._simpul(i - 1)
            s = sebelum.next
            sebelum.next = s.next
            if s is self.tail:
                self.tail = sebelum
        self.n -= 1
        return s.nilai

def posisi_sisip(prioritas, n):
    if prioritas == 1:
        return 0
    if prioritas == 2:
        return n // 2
    return n

def tambah_ke(struktur, pesanan):
    pos = posisi_sisip(pesanan.prioritas, len(struktur))
    struktur.insert(pos, pesanan)
    return pos
