class Pencacah:
    def __init__(self):
        self.banding = 0
        self.pindah = 0

def kunci_oid(p):
    return p.oid

def kunci_harga(p):
    return p.harga

def kunci_selesai(p):
    return p.selesai if p.selesai is not None else 10 ** 9     # belum selesai -> paling akhir

def ambil_kunci(nama):
    if nama == "oid":
        return kunci_oid
    if nama == "harga":
        return kunci_harga
    if nama == "selesai":
        return kunci_selesai
    raise ValueError("kunci tidak dikenal: " + nama)

def insertion_sort(A, kunci, c=None):
    c = c or Pencacah()
    for i in range(1, len(A)):
        x = A[i]
        kx = kunci(x)
        j = i - 1
        while j >= 0:
            c.banding += 1
            if kunci(A[j]) > kx:
                A[j + 1] = A[j]
                c.pindah += 1
                j -= 1
            else:
                break
        A[j + 1] = x
        c.pindah += 1
    return A

def merge_sort(A, kunci, c=None):
    c = c or Pencacah()
    _ms(A, [None] * len(A), 0, len(A) - 1, kunci, c)
    return A

def _ms(A, aux, lo, hi, kunci, c):
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    _ms(A, aux, lo, mid, kunci, c)
    _ms(A, aux, mid + 1, hi, kunci, c)
    i, j, k = lo, mid + 1, lo
    while i <= mid and j <= hi:
        c.banding += 1
        if kunci(A[i]) <= kunci(A[j]):          
            aux[k] = A[i]
            i += 1
        else:
            aux[k] = A[j]
            j += 1
        k += 1
    while i <= mid:                              
        aux[k] = A[i]
        i += 1
        k += 1
    while j <= hi:                               
        aux[k] = A[j]
        j += 1
        k += 1
    for t in range(lo, hi + 1):
        A[t] = aux[t]
    c.pindah += hi - lo + 1

def linear_search(A, target, kunci=None, c=None):
    c = c or Pencacah()
    for i in range(len(A)):
        c.banding += 1
        if (A[i] if kunci is None else kunci(A[i])) == target:
            return i
    return -1

def binary_search(A, target, kunci=None, c=None):
    c = c or Pencacah()
    lo, hi = 0, len(A) - 1
    while lo <= hi:                              
        mid = (lo + hi) // 2
        c.banding += 1
        v = A[mid] if kunci is None else kunci(A[mid])
        if v == target:
            return mid
        if v < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
