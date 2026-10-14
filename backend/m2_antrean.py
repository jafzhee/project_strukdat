from backend.m1_pesanan import Array

class Tumpukan:
    def __init__(self):
        self.a = Array()

    def push(self, x):
        self.a.append(x)

    def pop(self):
        if self.a.n == 0:
            raise IndexError("tumpukan kosong")
        return self.a.remove(self.a.n - 1)

    def peek(self):
        return self.a.get(self.a.n - 1)

    def kosong(self):
        return self.a.n == 0

    def __len__(self):
        return self.a.n

    def isi(self):
        return [self.a.get(i) for i in range(self.a.n)]

    def kosongkan(self):
        self.a = Array()


# KASIR
def _angka(t):
    return t[0] in "0123456789."

def _num(x):
    return str(int(x) if isinstance(x, float) and x == int(x) else x)

def _prio(op):
    return 2 if op in "*/" else 1

def token(s):
    hasil, i, n = [], 0, len(s)

    while i < n:
        ch = s[i]
        if ch == " ":
            i += 1
        elif ch in "0123456789.":
            j = i
            while j < n and s[j] in "0123456789.":
                j += 1
            hasil.append(s[i:j])
            i = j
        elif ch in "+-*/()":
            hasil.append(ch)
            i += 1
        else:
            raise ValueError("karakter tidak dikenal: " + ch)

    return hasil

def ke_postfix(ekspresi, jejak=None):
    st, out = Tumpukan(), []

    for k, t in enumerate(token(ekspresi), 1):
        if _angka(t):
            out.append(t)
            tindakan = "angka, langsung keluar"
        elif t == "(":
            st.push(t)
            tindakan = "push ("
        elif t == ")":
            while not st.kosong() and st.peek() != "(":
                out.append(st.pop())
            if st.kosong():
                raise ValueError("kurung tutup tidak berpasangan")
            st.pop()
            tindakan = "pop sampai (, buang ("
        else:
            lepas = []
            while (not st.kosong() and st.peek() != "("
                   and _prio(st.peek()) >= _prio(t)):
                x = st.pop()
                out.append(x)
                lepas.append(x)
            st.push(t)
            tindakan = (
                "pop %s (sama/lebih kuat), push %s" % (" ".join(lepas), t)
                if lepas else "push " + t
            )

        if jejak is not None:
            jejak.append([
                "1.%d" % k, t, tindakan,
                " ".join(st.isi()) or "kosong", " ".join(out)
            ])

    while not st.kosong():
        x = st.pop()
        if x == "(":
            raise ValueError("kurung buka tidak berpasangan")
        out.append(x)

    if jejak is not None:
        jejak.append(["1.akhir", "-", "pop sisa stack", "kosong", " ".join(out)])

    return out

def hitung(postfix, jejak=None):
    st = Tumpukan()

    for k, t in enumerate(postfix, 1):
        if _angka(t):
            st.push(float(t) if "." in t else int(t))
            tindakan = "operand, push " + t
        else:
            if len(st) < 2:
                raise ValueError("ekspresi tidak valid")

            b, a = st.pop(), st.pop()

            if t == "+":
                r = a + b
            elif t == "-":
                r = a - b
            elif t == "*":
                r = a * b
            else:
                if b == 0:
                    raise ValueError("pembagian dengan nol")
                r = a / b

            st.push(r)
            tindakan = "pop %s dan %s -> %s%s%s = %s" % (
                _num(b), _num(a), _num(a), t, _num(b), _num(r)
            )

        if jejak is not None:
            jejak.append([
                "2.%d" % k, t, tindakan,
                " ".join(_num(x) for x in st.isi()), ""
            ])

    if len(st) != 1:
        raise ValueError("ekspresi tidak valid")

    h = st.pop()
    return int(h) if isinstance(h, float) and h == int(h) else h


# ANTREAN
class AntreanNaif:
    def __init__(self):
        self.a = Array()

    def __len__(self):
        return self.a.n

    @property
    def geser(self):
        return self.a.kerja

    def enqueue(self, x):
        self.a.append(x)

    def dequeue(self):
        return None if self.a.n == 0 else self.a.remove(0)

    def push_front(self, x):
        self.a.insert(0, x)

    def pop_back(self):
        return None if self.a.n == 0 else self.a.remove(self.a.n - 1)

    def isi(self):
        return [self.a.get(i) for i in range(self.a.n)]

class AntreanMelingkar:
    def __init__(self, K=4):
        self.data = [None] * K
        self.front = self.rear = self.count = 0
        self.geser = self.salin = 0

    def __len__(self):
        return self.count

    @property
    def kapasitas(self):
        return len(self.data)

    def kosong(self):
        return self.count == 0

    def _tumbuh(self):
        K = len(self.data)
        baru = [None] * (K * 2)

        for i in range(self.count):
            baru[i] = self.data[(self.front + i) % K]

        self.salin += self.count
        self.data, self.front, self.rear = baru, 0, self.count

    def enqueue(self, x):
        if self.count == len(self.data):
            self._tumbuh()

        self.data[self.rear] = x
        self.rear = (self.rear + 1) % len(self.data)
        self.count += 1

    def dequeue(self):
        if self.count == 0:
            return None

        x = self.data[self.front]
        self.data[self.front] = None
        self.front = (self.front + 1) % len(self.data)
        self.count -= 1
        return x

    def push_front(self, x):
        if self.count == len(self.data):
            self._tumbuh()

        self.front = (self.front - 1) % len(self.data)
        self.data[self.front] = x
        self.count += 1

    def pop_back(self):
        if self.count == 0:
            return None

        self.rear = (self.rear - 1) % len(self.data)
        x = self.data[self.rear]
        self.data[self.rear] = None
        self.count -= 1
        return x

    def isi(self):
        K = len(self.data)
        return [self.data[(self.front + i) % K] for i in range(self.count)]

# UNDO / REDO
class Layanan:
    def __init__(self, awal):
        self.naif, self.circ = AntreanNaif(), AntreanMelingkar(4)

        for p in awal:
            self.naif.enqueue(p)
            self.circ.enqueue(p)

        self.undo, self.redo = Tumpukan(), Tumpukan()

    def _antrean(self, versi):
        return self.naif if versi == "naif" else self.circ

    def _catat(self, aksi):
        self.undo.push(aksi)
        self.redo.kosongkan()

    def enqueue(self, p):
        self.naif.enqueue(p)
        self.circ.enqueue(p)
        self._catat(("ENQUEUE", p))

    def dequeue(self, versi, k):
        q, keluar = self._antrean(versi), []

        for _ in range(k):
            x = q.dequeue()
            if x is None:
                break
            keluar.append(x)

        if keluar:
            self._catat(("DEQUEUE", versi, keluar))

        return keluar

    def _balik(self, aksi):
        if aksi[0] == "ENQUEUE":
            self.naif.pop_back()
            self.circ.pop_back()
        else:
            q, daftar = self._antrean(aksi[1]), aksi[2]
            for p in reversed(daftar):
                q.push_front(p)

    def _ulang(self, aksi):
        if aksi[0] == "ENQUEUE":
            self.naif.enqueue(aksi[1])
            self.circ.enqueue(aksi[1])
        else:
            q = self._antrean(aksi[1])
            for _ in aksi[2]:
                q.dequeue()

    def undo_last(self):
        if self.undo.kosong():
            return None

        aksi = self.undo.pop()
        self._balik(aksi)
        self.redo.push(aksi)
        return aksi

    def redo_last(self):
        if self.redo.kosong():
            return None

        aksi = self.redo.pop()
        self._ulang(aksi)
        self.undo.push(aksi)
        return aksi

    def stats(self):
        return [
            ["queue_len naif", len(self.naif)],
            ["queue_len circular", len(self.circ)],
            ["queue_capacity circular", self.circ.kapasitas],
            ["total geseran naif", self.naif.geser],
            ["total geseran circular", self.circ.geser],
            ["undo depth", len(self.undo)],
            ["redo depth", len(self.redo)]
        ]