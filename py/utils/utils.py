import numpy 

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

def repr_pss_tss(pss,tss,weights):
    s = ''
    names = ['w0','w1','w2','w3','wpp','wwp','wlm','wd']
    for sid in xrange(len(pss)):
        psk = pss[sid]
        tsk = tss[sid]
        for k in xrange(len(psk)):
            ps = psk[k]
            ts = tsk[k]
            ss = [str(sid)]
            ts_flat = reduce(lambda x,y: x+y, [list(x) for x in ts])
            ss.append(' '.join(ts_flat))
            ss.append(' '.join([str(x) for x in ps]))
            score = sum([ps[i]*weights[i] for i in xrange(len(weights))])
            ss.append(str(score))
            ss = ' ||| '.join(ss)
            s+=ss+'\n'
    return s

            
