#read phrase-table
from math import exp, log
import sys

def get_phrase_table(weight,phrase_penalty,word_penalty,path):
    sys.stderr.write('loading phrase table\n')
    
    f = open(path)
    d = {}
    seenwords = {}
    for line in f:
        ll = line.split(' ||| ')
        f_phrase = tuple(ll[0].split())
        e_phrase = tuple(ll[1].split())
        features = [float(x) for x in ll[2].split()]

        score = sum([x[0]*log(x[1]) for x in zip(weight,features)])
        score += phrase_penalty - len(e_phrase) * word_penalty

        partial_score = [log(x) for x in features]
        partial_score.append(1) # phrase penalty
        partial_score.append(-len(e_phrase)) # word penalty

        item = (score,e_phrase,partial_score)
        if not f_phrase in d:
            d[f_phrase] = []
        d[f_phrase].append(item)
        for f_word in f_phrase:
            seenwords[f_word] = 1
    for f_phrase in d:
        items = d[f_phrase]
        d[f_phrase] = sorted(items,key = lambda x: -x[0])


    f.close()
    sys.stderr.write('Phrase table: %d\n' % len(d))
    return d,seenwords
