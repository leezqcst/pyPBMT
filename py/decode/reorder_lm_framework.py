
from .reorder_lm import
from . import phraseTable
from . import multip
from . import monotone
from .reorder_lm import decode, stderr

def read_moses(fn):
    f = open(fn)
    wp = 0.0
    pp = 0.0
    weights = []
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
    f.close()
    return weights, wp, pp, path



def main():
    # reorder mosis.ini -j 4 -b 100
    if len(sys.argv) < 2:
        sys.exit(-1)
    mosis_fn = sys.argv[1]
    n_core = 1
    beam_size = 100
    if len(sys.argv) >= 4:
        n_core = int(sys.argv[3])
        beam_size = int(sys.argv[5])
    weights, wp, pp, d_weight, lm_weight, path = monotone.read_moses(mosis_fn)

    mask = [1, 1, 1, 1]
    d_limit = 6

    stderr(repr([weights, wp, pp, d_weight, lm_weight, d_limit, beam_size]))

    # get phrase table
    phrase_table, seen_words = phraseTable.get_phrase_table(
        weights, mask, pp, wp, path)
    lm_model = lm.getLM()

    # decode
    lines = sys.stdin.readlines()

    line_groups = multip.split_list(lines, n_core, 1)

    processes = []
    queue = Queue()
    for i in xrange(n_core):
        group = line_groups[i]
        p = Process(
            target=worker,
            args=(
                group,
                phrase_table,
                seen_words,
                lm_model,
                lm_weight,
                d_weight,
                d_limit,
                beam_size,
                i,
                queue))
        p.start()
        processes.append(p)

    d = {}
    s = 0.0
    ns = 0.0
    for i in xrange(n_core):
        key, out, score = queue.get()
        d[key] = out
        s += score

    for p in processes:
        p.join()

    for i in xrange(n_core):
        group = d[i]
        if group != '':
            print group,

    sys.stderr.write('score:' + str(s) + '\n')

    sys.stderr.flush()


def worker(lines, phrase_table, seen_words, lm_model,
           lm_weight, d_weight, d_limit, beam_size, i, queue):
    out = ''
    s = 0.0
    k = 0
    for line in lines:
        if k % 10 == 1:
            stderr('PRO-%d %d/%d' % (i, k, len(lines)))
        k += 1
        ll = line.strip().split()
        e_phrases = None
        e_sentence = ''
        score = 0.0
        success = False
        expand = 1
        while not success:
            try:
                e_phrases, e_sentence, score = decode(
                    ll, phrase_table, seen_words, lm_model, lm_weight, d_weight, d_limit, beam_size * expand)
                success = True
            except Exception as e:
                stderr(repr(e))
                stderr(line)
                stderr(repr(beam_size * expand))
                expand += 10
                if expand > 1:
                    success = True
                    e_sentence = ' '
                    score = 0.0
                    stderr('Abort!')

        out += e_sentence + '\n'
        s += score

    queue.put((i, out, s))

if __name__ == '__main__':

    a = datetime.now()
    main()
    b = datetime.now()
    stderr(str(b - a))

