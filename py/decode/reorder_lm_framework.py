
from . import phraseTable
from . import multip
from . import monotone
from . import lm
from .reorder_lm import decode, decode_k, stderr
import configparser
from multiprocessing import Queue, Process
import logging
import cPickle
from datetime import datetime
import sys,os
from utils.utils import repr_pss_tss
from utils.weights import *

def main():
    # reorder_lm.py decode.config

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    config_fn = sys.argv[1]
    config = configparser.ConfigParser()
    config._interpolation = configparser.ExtendedInterpolation()
    config.read(config_fn)

    weight = Weight()
    weight.parse(config)
    feature_weights = weight.get_weights()

    
    # decode
    r = decode_batch_config_weight(config, feature_weights)

    # print results
    if len(r) == 2:
        pss, tss = r
        k_best_path = config.get('path','k_best_path')
        f = open(k_best_path,'w')
        s = repr_pss_tss(pss,tss,feature_weights)
        f.write(s)
        f.close()
        

def decode_batch_config_weight(config,feature_weights):
    # decode.config
    nthread = config.getint('decoding','nthread')
    beam_size = config.getint('decoding','beam_size')
    top_k = config.getint('decoding','top_k')
    d_limit = config.getint('decoding','d_limit')

    # file paths
    temp_folder = config.get('path','temp_folder')
    inputFn = config.get('path','input')
    referenceFn = config.get('path','reference')
    lm_path= config.get('path','lm_path')
    phrase_table_path = config.get('path','phrase_table')
    output_path = config.get('path','single_best_path')
    k_best_path = config.get('path','k_best_path')

    return decode_batch(feature_weights, inputFn, temp_folder = temp_folder, lm_path = lm_path, phrase_table_path = phrase_table_path , n_core = nthread, beam_size = beam_size, top_k = top_k, d_limit = d_limit, output_file = output_path)


def decode_batch(feature_weights,input_path, temp_folder=None, output_file = None, lm_path = None, phrase_table_path = None,n_core = 1, beam_size = 100, top_k = 1, d_limit = 6):
    
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

        f = open(output_file,'w')

        for i in xrange(n_core):
            group = d[i]
            if group != '':
                f.write(group)
        
        f.close()

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

