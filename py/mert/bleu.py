
# -*- coding: utf-8 -*-

import os, sys
import logging
from math import pow,exp

class Bleu:
    def __init__(self):
        self.length = .0
        self.ref_length = .0
        self.precision = [[.0,.0], [.0, .0], [.0, .0], [.0, .0]]
    
    def parse_sentence(self, sen, ref):
        # sen, ref : ['a','b']
        # currently, only single reference sentence.
        # if pharse A occurs 2 times in reference, then A in translated sentence will match at most 2 times.
        self.length = len(sen)
        self.ref_length = len(ref)
        for n in xrange(4):
            d = {}
            for i in xrange(len(ref) - n):
                key =tuple(ref[i:i+n+1])
                if not key in d:
                    d[key] = 0
                d[key] += 1
            for i in xrange(len(sen) - n):
                key =tuple(sen[i:i+n+1])
                if key in d and d[key] > 0:
                    self.precision[n][0] += 1
                    d[key] -= 1
            if len(sen) - n >= 0:
                self.precision[n][1] = len(sen) - n

    def get_bleu(self):
        bp = 1.0
        if self.length < self.ref_length:
            ratio = self.length*1.0 / self.ref_length
            bp = exp(1- self.ref_length *1.0 / self.length)
        bleu = 1.0

        for p in self.precision:
            if p[1] == 0:
                bleu = 0.0
                break
            prec = p[0]*1.0/p[1]
            bleu = bleu * prec
        bleu = bp * pow(bleu, 0.25)
        bleu = bleu * 100
        return bleu

    def add_bleu(self,b):
        self.length += b.length
        self.ref_length += b.ref_length
        for i in xrange(4):
            for j in xrange(2):
                self.precision[i][j] += b.precision[i][j]

    def minus_bleu(self,b):
        self.length -= b.length
        self.ref_length -= b.ref_length
        for i in xrange(4):
            for j in xrange(2):
                self.precision[i][j] -= b.precision[i][j]

    def __repr__(self):
        bp = 1.0
        ratio = self.length*1.0 / self.ref_length
        if self.length< self.ref_length:
            ratio = self.length*1.0 / self.ref_length
            bp = exp(1- self.ref_length *1.0 / self.length)
        
                
        prec = []
        for p in self.precision:
            if p[1] == 0:
                prec.append(0.0)
                continue
            prec.append(p[0]*1.0/p[1]*100)

        
        #s = 'Bleu Score: {} (BP:{}, 1:{}, 2:{}, 3:{}. 4:{})'.format(self.get_bleu(),bp,prec[0],prec[1],prec[2],prec[3])
        s = 'BLEU = %.2f %.2f/%.2f/%.2f/%.2f, (BP=%.3f ratio=%.3f, hyp_len=%d, ref_len=%d)' % (self.get_bleu(),prec[0],prec[1],prec[2],prec[3], bp, ratio, self.length, self.ref_length)
        return s


def calculate_bleu(sens, refs):
    # sens and refs : ['a','b']
    b = Bleu()
    for i in xrange(len(sens)):
        sen = sens[i]
        ref = refs[i]
        bl = Bleu()
        bl.parse_sentence(sen,ref)
        b.add_bleu(bl)
        
    return b

def main():
    # python bleu predict.txt ref.txt
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    reffn = sys.argv[1]
    fn = sys.argv[2]
    f = open(fn)
    reff = open(reffn)
    
    sens = []
    refs = []

    for line in f:
        ll = line.strip().split()
        sens.append(ll)
        
    for line in reff:
        ll = line.strip().split()
        refs.append(ll)
        
    bleu_object = calculate_bleu(sens,refs)
    
    logging.info('{}'.format(bleu_object))


if __name__ == '__main__':
    main()
