import time

class RNG:
    def __init__(self, seed=None, a=48271, c=0, m=2147483647):
        if seed is None:
            seed = int(time.time() * 1000)
        self.a = a
        self.c = c
        self.m = m
        self.x = int(seed) % m
        if self.x <= 0:
            self.x += m - 1

    def next(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m

    def next_int(self, min_v, max_v):
        return min_v + int(self.next() * (max_v - min_v + 1))

    def seed(self, new_seed):
        self.x = int(new_seed) % self.m
        if self.x <= 0:
            self.x += m - 1
