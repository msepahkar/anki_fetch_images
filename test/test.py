class B:
    def __init__(self):
        self.x = 1

class C(B):
    def __init__(self, b):
        self.y = 2

b=B()
c=C(b)
print(c.x)
print(c.y)