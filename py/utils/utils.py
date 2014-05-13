
def enum(*sequential, **named):
    """
    Handy way to fake an enumerated type in Python
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)


def array_plus(a,b):
    r = []
    for i in xrange(len(a)):
        r.append(a[i] + b[i])
    return r

def array_minus(a,b):
    r = []
    for i in xrange(len(a)):
        r.append(a[i] - b[i])
    return r
    
