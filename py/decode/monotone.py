#!/usr/bin/env python
# -*- coding: utf-8 -*-
# monotone model

import phraseTable
import sys
import os
import multip
from multiprocessing import Queue, Process
import subprocess as sp


def stderr(s):
    sys.stderr.write(s+'\n')

def decode(f_sentence,phrase_table,seen_words,return_trans=False,num_feature = 8):

    derivation = [] # [(f_phrase,e_phrase,score)]
    new_phrase_table = {}

    states = [0.0] * (len(f_sentence)+1)
    trans = {} # key = (start_state, end_state) value = (score, e_phrase)
    inward = {} # if (0,1) in trans, inward[1] = [0]
    small = 0

    # build the fst
    for i in xrange(len(f_sentence)):
        for j in xrange(i+1,len(f_sentence)+1):        
            key = (i,j)
            f_phrase = tuple ( f_sentence[i:j] )
            if not f_phrase in phrase_table:
                continue
            trans[key] = phrase_table[f_phrase][0]
            new_phrase_table[f_phrase] = phrase_table[f_phrase]
            # for inword
            if not j in inward:
                inward[j] = []
            inward[j].append(i)

    # check for Out of Phrase-table phrases
    length_ps = 0
    for key in phrase_table:
        items = phrase_table[key][0]
        length_ps = len(items[2])
        break

    for i in xrange(1,len(f_sentence)+1):
        if not i in inward:
            f_phrase = tuple( f_sentence[i-1:i] )
            new_phrase_table[f_phrase] = [(small,f_phrase,[0.0]*length_ps)]
            trans[(i-1,i)] = (small,f_phrase)
            inward[i] = [i-1,]

    # Viterbi decoding
    e_phrases = {} 
    fathers = {} 
    for i in xrange(1,len(f_sentence) + 1):
        max_score = - float('inf')
        best_e_phrase = ()
        for start in inward[i]:
            key = (start,i)
            item = trans[key]
            score = item[0] + states[start]
            if max_score < score:
                max_score = score
                fathers[i] = start
                e_phrases[i] = (item[1],item[0])
        states[i] = max_score
    

    # backtrack
    current = len(f_sentence)
    while True:
        father = fathers[current]
        f_phrase = f_sentence[father:current]
        e_phrase = e_phrases[current][0]
        score = e_phrases[current][1]
        derivation.append((f_phrase,e_phrase,score))
        current = father
        if current == 0:
            break
    derivation.reverse()
    if return_trans:
        return (states,trans.keys(),new_phrase_table)
    else:
        return (derivation,states[-1])

def derivation_to_sentence(derivation):
    s = []
    for f_phrase,e_phrase,score in derivation:
        s += list(e_phrase)
    return ' '.join(s)

def read_moses(fn):
    f = open(fn)
    wp = 0.0
    pp = 0.0
    weights = []
    d_weight = 0.0
    lm_weight = 0.0
    path = ''
    for line in f:
        ll = line.split()
        if line.startswith('PhraseDictionaryMemory'):
            path = ll[4].split('=')[1]
        if line.startswith('WordPenalty0='):
            wp = float(ll[1])
        if line.startswith('PhrasePenalty0='):
            pp = float(ll[1])
        if line.startswith('TranslationModel0='):
            weights = [float(x) for x in ll[1:]]
        if line.startswith('Distortion0='):
            d_weight = float(ll[1])
        if line.startswith('LM0'):
            lm_weight = float(ll[1])
    f.close()
    return weights,wp,pp,d_weight,lm_weight,path

def main():
    # monotone.py mosis.ini -j 4
    if len(sys.argv) < 2:
        sys.exit(-1)
    mosis_fn = sys.argv[1]
    n_core = 1
    if len(sys.argv) >= 4:
        n_core = int(sys.argv[3])
    weights,wp,pp,d_weight,lm_weight,path = read_moses(mosis_fn)
    mask = [1,1,1,1]

    # get phrase table
    phrase_table,seen_words = phraseTable.get_phrase_table(weights,mask,pp,wp,path)    
    
    # decode
    lines = sys.stdin.readlines()
    
    line_groups = multip.split_list(lines, n_core, 1)

    processes = []
    queue = Queue()
    for i in xrange(n_core):
        group = line_groups[i]
        p = Process(target=worker, args=(group, phrase_table,seen_words, i, queue))
        p.start()
        processes.append(p)

    d = {}
    s = 0.0
    ns = 0.0
    for i in xrange(n_core):
        key, out , score = queue.get()
        d[key] = out
        s += score


    for p in processes:
        p.join()

    for i in xrange(n_core):
        group = d[i]
        if group != '':
            print group,

    sys.stderr.write('score:'+str(s)+'\n')

    sys.stderr.flush()

def worker(lines,phrase_table,seen_words, i,queue):
    out = ''
    s = 0.0
    ns = 0.0
    for line in lines:
        ll = line.strip().split()
        derivation,score= decode(ll,phrase_table,seen_words)
        sentence = derivation_to_sentence(derivation)
        out += sentence +'\n'
        s += score

    queue.put((i,out,s))

def test():
    weights = [0.2,0.2,0.2,0.2]
    mask = [1,1,1,1]
    wp = 0
    pp = 0
    f_string = 'mit anderen programmen soll china bei der erfüllung bestimmter wto-vorgaben unterstützt werden .'
    f_sentence = f_string.split()
    phrase_table,seen_words = phraseTable.get_phrase_table(weights,mask,wp,pp,'../model/moses.ini')
    derivation,score,norm_score = decode(f_sentence,phrase_table,seen_words)
    print derivation_to_sentence(derivation)
    print derivation

if __name__ == '__main__':
    main()
