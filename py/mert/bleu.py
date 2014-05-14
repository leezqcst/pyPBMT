
class Bleu:
    def __init__(self):
        self.length = .0
        self.ref_length = .0
        self.precision = [[.0，.0], [.0，.0], [.0，.0], [.0，.0]]
    
    def parse_sentence(sen, ref):
        # sen, ref : ['a','b']
        self.length = len(sen)
        self.ref_length = len(ref)
        for n in xrange(4):
            d = {}
            for i in xrange(len(ref) - n):
                key =tuple(ref[i:i+n+1])
                d[key] = 1
            for i in xrange(len(sen) - n):
                key =tuple(sen[i:i+n+1])
                if key in d:
                    self.precision[i][0] += 1
            if len(sen) - n >= 0:
                self.precision[i][1] = len(sen) - n

    def get_bleu(self):
        bp = 1.0
        if self.length < self.ref_length:
            bp = self.length*1.0 / self.ref_length
        bleu = bp

        for p in self.precision:
            if p[1] == 0:
                bleu = 0.0
                break
            prec = p[0]*1.0/p[1]
            bleu = bleu * prec
        
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
