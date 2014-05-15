from utils.utils import get_config, write_config
from utils.weights import Weight, get_random_weights,weight_to_config,normalize_weights
from .bleu import Bleu
from .line_search import search_line 
from decode.reorder_lm_framework import decode_batch_config_weight
import logging
import cPickle
import os,sys
from datetime import datetime
from random import random

def main():
    # python mert_framework mert.config
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    config_fn = sys.argv[1]
    config = get_config(config_fn)
    mert(config,config_fn+'.mert')




def mert(config,config_out,debug = True):
    weight = Weight()
    weight.parse(config)
    current_weights = weight.get_weights()

    current_pss = []
    current_tss = []
    current_bleus = []
    sentence_dict = []

    bleu_thres = 0.01

    n_new_add = 0.0
    new_bleu = .0
    old_bleu = .0
    best_bleu = .0
    best_weights = None
    round_id = 0
    refs = get_reference_config(config)

    # this loop stop when: 1 no new sentence ; 2 bleu doesn't imporve
    while True:
        old_bleu = best_bleu
        # generate k-best 
        pss,tss = decode_batch_config_weight(config,current_weights)

        # merge k-best
        n_new_add = merge_pss_tss(current_pss, current_tss, sentence_dict, current_bleus, refs, pss, tss)
        
        logging.info('New_add: {}'.format(n_new_add))
        if n_new_add == 0:
            break
        # optimize 20 times: one with previous weight, the other with random weights
        new_weights, new_bleu = optimize(current_pss, current_bleus,  current_weights)

        if best_bleu < new_bleu:
            best_bleu = new_bleu
            best_weights = new_weights

        if debug:
            logging.info('{} {}'.format(new_bleu, new_weights))

        for i in xrange(19):
            rand_weights = get_random_weights(current_weights)
            new_weights, new_bleu = optimize(current_pss, current_bleus,  rand_weights)
            
            if debug:
                #logging.info('Rand Weights: {}'.format(rand_weights))
                logging.info('{} {}'.format(new_bleu, new_weights))

            if best_bleu < new_bleu:
                best_bleu = new_bleu
                best_weights = new_weights
                

        round_id += 1

        logging.info('Round: {}, Bleu: {}'.format(round_id,best_bleu))
        logging.info('Weights: {}'.format(best_weights))

        current_weights = best_weights

        if best_bleu - old_bleu < bleu_thres:
             break

    # write the new weights to config
    config = weight_to_config(best_weights,config)
    write_config(config,config_out)


def merge_pss_tss(total_pss,total_tss,sentence_dict,total_bleus, refs, new_pss,new_tss):
    '''change total_pss, total_tss, sentence_dict inplace.
    
    sentence_dict: a dict array, one for each source sentence

    return the number of newly added sentences
    '''
    n = len(new_pss)
    n_new_add = 0

    if len(sentence_dict) == 0:
        for i in xrange(n):
            sentence_dict.append({})
            total_bleus.append([])
            total_pss.append([])
            total_tss.append([])
    for i in xrange(n):
        pss = new_pss[i]
        tss = new_tss[i]
        t_pss = total_pss[i]
        t_tss = total_tss[i]
        t_bleus = total_bleus[i]
        ref = refs[i]
        d = sentence_dict[i]
        for j in xrange(len(tss)):
            ts = tss[j]
            ps = pss[j]
            key = tuple(ts)
            if not key in d:

                n_new_add += 1
                t_pss.append(ps)
                t_tss.append(ts)
                d[key] = len(t_pss)-1
                b = Bleu()
                ts_flat = []
                for e_phrase in ts:
                    ts_flat += list(e_phrase)
                b.parse_sentence(ts_flat,ref)
                t_bleus.append(b)
            else:
                old_j = d[key]
                t_pss[old_j] = ps
    return n_new_add

def rand_array(n,ept):
    temp = range(n)
    temp = [x for x in temp if not x in ept]
    temp = [(random(),x) for x in temp]
    temp = sorted(temp)
    temp = [x[1] for x in temp]
    return temp

def optimize(pps, bleus, start_feature_weights):
    '''optimize from start_feature_weights
    pps: partial_scores num_sentence * k_best 
    tss: translated_sentences num_sentence * k_best 
    bleus: Bleu Objects num_sentence * k_best
    '''
    num_feature = len(start_feature_weights)
    
    current_weights = list(start_feature_weights)
    
    old_bleu = 0
    new_bleu = 0
    threshold = 0.1
    ept = set()
#    ept.add(4)
#   ept.add(5)
    while True:
        old_bleu = new_bleu
        for i in rand_array(num_feature,ept):
            # optimize ith weights
            current_weights, new_bleu = search_line(pps, bleus, current_weights,i)
        if abs(new_bleu - old_bleu) < threshold:
            break
    
    current_weights = normalize_weights(current_weights)

    return current_weights,new_bleu

def get_reference_config(config):
    fn = config['reference']
    f = open(fn)
    refs = []
    for line in f:
        ll = line.strip().split()
        refs.append(ll)
    return refs

def get_reference_path(fn):
    f = open(fn)
    refs = []
    for line in f:
        ll = line.strip().split()
        refs.append(ll)
    return refs
    

# ==== Test ====

def test():
    pss, tss = cPickle.load(open('/Users/xingshi/Workspace/misc/pyPBMT/var/v1/pts.pickle'))
    d = []
    weights = [0.2,0.2,0.2,0.2,0.1,0.1,0.5,0.3]
    t_pss, t_tss, t_bleus = [],[],[]
    refs = get_reference_path('/Users/xingshi/Workspace/misc/pyPBMT/data/dev.clean.en.10')
    new_add = merge_pss_tss(t_pss,t_tss,d,t_bleus,refs,pss,tss)
    cPickle.dump((t_pss,t_tss,t_bleus),open('/Users/xingshi/Workspace/misc/pyPBMT/var/v1/ptbs.pickle','w'))
    print new_add
                 


if __name__ == '__main__':
    main()
    #test()
