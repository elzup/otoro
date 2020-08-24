path = './otoro.log'
f = open(path, encoding='utf-8')

lines = f.read().split("\n")


def get_d(line):
    h, l, c = map(int, line.split("|"))
    return h - l


nums = sorted(map(get_d, lines))
print("\n".join(map(str, nums)))
