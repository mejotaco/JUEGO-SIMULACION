import math


class RNG:
    def __init__(self, seed=42):
        self._state = seed & 0x7FFFFFFF
        self._gauss_cache = None

    def seed(self, value):
        self._state = value & 0x7FFFFFFF
        self._gauss_cache = None

    # ── Generador base: Congruencia Lineal (LCG) ──
    # X_{n+1} = (1103515245 * X_n + 12345) mod 2^31
    def _next(self):
        self._state = (1103515245 * self._state + 12345) & 0x7FFFFFFF
        return self._state

    # ── Distribuciones ──

    def uniform(self, a, b):
        return a + self._next() / 2147483648.0 * (b - a)

    def random(self):
        return self._next() / 2147483648.0

    def randint(self, a, b):
        return a + int(self.random() * (b - a + 1))

    def choice(self, seq):
        return seq[self.randint(0, len(seq) - 1)]

    def exponential(self, lambd):
        u = 1.0 - self.random()
        return -math.log(u) / lambd

    def gauss(self, mu=0.0, sigma=1.0):
        if self._gauss_cache is not None:
            z = self._gauss_cache
            self._gauss_cache = None
            return mu + z * sigma
        u1 = self.random()
        u2 = self.random()
        r = math.sqrt(-2.0 * math.log(u1))
        z0 = r * math.cos(math.tau * u2)
        z1 = r * math.sin(math.tau * u2)
        self._gauss_cache = z1
        return mu + z0 * sigma

    def chi_square(self, k):
        s = 0.0
        for _ in range(k):
            z = self.gauss()
            s += z * z
        return s


rng = RNG()
