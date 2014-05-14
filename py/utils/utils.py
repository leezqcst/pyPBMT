
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


def get_config(fn):
    config = {}
    f = open(fn)
    for line in f:
        if line.strip().startswith('#'):
            continue
        fields = line.strip().split('=')
        if len(fields)<3:
            continue

        t = fields[0]
        key = fields[1]
        value = fields[2]
        if t == 'i': #int
            config[key] = int(value)
        elif t== 'f': #float
            config[key] = float(value)
        elif t=='s': # string
            config[key] = value
        elif t=='b': # bool
            if value == 'True':
                config[key]= True
            elif value == 'False':
                config[key]=False
    return config
