
from . import phraseTable
from . import multip
from . import monotone
from . import lm
from .reorder_lm import decode, decode_k, stderr
from utils.utils import get_config
from multiprocessing import Queue, Process
import logging
import cPickle
from datetime import datetime
import sys,os



def main():
    # reoder_lm.py decode.config
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    config_fn = sys.argv[1]
    config = get_config(config_fn)
    decode_batch_config(config)

    
def decode_batch_config(config):
    # weights
    feature_weights = []
    for name in ['w0','w1','w2','w3','wpp','wwp','wlm','wd']:
        feature_weights.append(config[name])

    # decode.config
    nthread = config['nthread']
    beam_size = config['beam_size']
    top_k = config['top_k']
    d_limit = config['d_limit']

    # file paths
    temp_folder = config['temp_folder']
    inputFn = config['input']
    referenceFn = config['reference']
    lm_path= config['lm_path']
    phrase_table_path = config['phrase_table']

    return decode_batch(feature_weights, inputFn, temp_folder = temp_folder, lm_path = lm_path, phrase_table_path = phrase_table_path , n_core = nthread, beam_size = beam_size, top_k = top_k, d_limit = d_limit)


def decode_batch_config_weight(config,feature_weights):
    # decode.config
    nthread = config['nthread']
    beam_size = config['beam_size']
    top_k = config['top_k']
    d_limit = config['d_limit']

    # file paths
    temp_folder = config['temp_folder']
    inputFn = config['input']
    referenceFn = config['reference']
    lm_path= config['lm_path']
    phrase_table_path = config['phrase_table']

    return decode_batch(feature_weights, inputFn, temp_folder = temp_folder, lm_path = lm_path, phrase_table_path = phrase_table_path , n_core = nthread, beam_size = beam_size, top_k = top_k, d_limit = d_limit)


def decode_batch(feature_weights,input_path, temp_folder=None, lm_path = None, phrase_table_path = None,n_core = 1, beam_size = 100, top_k = 1, d_limit = 6):
    
    # weights
    num_feature = len(feature_weights)
    weights = feature_weights[0:4]
    pp = feature_weights[4]
    wp = feature_weights[5]
    lm_weight = feature_weights[6]
    d_weight = feature_weights[7]

    # get phrase table
    phrase_table, seen_words = phraseTable.get_phrase_table(
        weights, pp, wp, phrase_table_path)
    lm_model = lm.getLM(lm_path)

    # decode
    f = open(input_path)
    lines = f.readlines()
    f.close()

    line_groups = multip.split_list(lines, n_core, 1)

    processes = []
    queue = Queue()
    for i in xrange(n_core):
        group = line_groups[i]
        p = None
        if top_k == 1:
            p = Process(
                target=worker_1,
                args=(
                    group,
                    phrase_table,
                    seen_words,
                    lm_model,
                    lm_weight,
                    d_weight,
                    d_limit,
                    beam_size,
                    num_feature,
                    i,
                    queue))
        else:
            p = Process(
                target=worker_k,
                args=(
                    group,
                    phrase_table,
                    seen_words,
                    lm_model,
                    lm_weight,
                    d_weight,
                    d_limit,
                    beam_size,
                    num_feature,
                    temp_folder,
                    top_k,
                    i,
                    queue))
        p.start()
        processes.append(p)

    if top_k == 1:
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

    elif top_k > 1:
        d = {}
        pss = []
        tss = []
        for i in xrange(n_core):
            key, ps, ts = queue.get()
            d[key] = (ps,ts)

        for p in processes:
            p.join()

        for i in xrange(n_core):
            ps,ts = d[i]
            pss+=ps
            tss+=ts
        

        #pfn = os.path.join(temp_folder, 'pts.pickle')
        #cPickle.dump((pss,tss),open(pfn,'w'))

        return pss, tss

        

def worker_k(lines, phrase_table, seen_words, lm_model,
           lm_weight, d_weight, d_limit, beam_size, num_feature, tempFolder, top_k, i, queue):

    tempFilePath = os.path.join(tempFolder,'temp_{}.fsa'.format(i))
    pss = []
    tss = []
    k = 0
    for line in lines:
        if k % 10 == 1:
            stderr('PRO-%d %d/%d' % (i, k, len(lines)))
        k += 1
        ll = line.strip().split()
        ps,ts = decode_k(
            ll, phrase_table, seen_words, lm_model, lm_weight, d_weight, d_limit, beam_size, num_feature, tempFilePath, False, k_best = top_k)
        pss.append(ps)
        tss.append(ts)
        
    queue.put((i, pss,tss))



def worker_1(lines, phrase_table, seen_words, lm_model,
           lm_weight, d_weight, d_limit, beam_size, num_feature, i, queue):
    out = ''
    s = 0.0
    k = 0
    for line in lines:
        if k % 3 == 1:
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
                    ll, phrase_table, seen_words, lm_model, lm_weight, d_weight, d_limit, beam_size * expand, num_feature)
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

