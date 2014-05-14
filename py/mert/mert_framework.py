from utils.utils import get_config, write_config
from utils.weights import Weight, get_random_weights,weight_to_config
from .bleu import Bleu
from .line_search import search_line 
from decode.reorder_lm_framework
import logging
import cPickle
import os,sys
from datetime import datetime


def main():
    # python mert_framework mert.config
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    config_fn = sys.argv[1]
    config = get_config(config_fn)
    mert(config,config_fn+'.mert')




def mert(config,config_out):
    weight = Weight()
    weight.parse(config)

    refs = get_reference(config)

    current_weights = weight.get_weights()
    current_pss = []
    current_tss = []
    current_bleus = []
    sentence_dict = []

    blue_thres = 0.1

    n_new_add = 0.0
    new_bleu = .0
    old_bleu = .0
    best_weights = None
    round_id = 0
    # this loop stop when: 1 no new sentence ; 2 bleu doesn't imporve
    while True:
        old_bleu = best_bleu
        # generate k-best 
        pss,tss = decode_batch_config_weight(config,current_weights)
        # merge k-best
        n_new_add = merge_pss_tss(current_pss, current_tss, sentence_dict, current_bleus, refs, pss, tss)
        if n_new_add == 0:
            break
        # optimize 20 times: one with previous weight, the other with random weights
        new_weights, new_bleu = optimize(current_pss, current_tss, current_bleus,  current_weights)
        if best_bleu < new_bleu:
            best_bleu == new_bleu
            best_weights = new_weights
        for i in xrange(19):
            rand_weights = get_random_weights(current_weights)
            new_weights, new_bleu = optimize(current_pss, current_tss, rand_weights)
            if best_bleu < new_bleu:
                best_bleu == new_bleu
                best_weights = new_weights

        round_id += 1

        logging.info('Round: {} Bleu: {}'.format(round_id,best_bleu))
        logging.info('Weights: {}'.format(best_weights))

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
                d[key] = 1
                n_new_add += 1
                t_pss.append(ps)
                t_tss.append(ts)
                b = Bleu()
                b.parse_sentence(ts,ref)
                t_bleus.append(b)
    return n_new_add



def optimize(pps,tss, bleus, start_feature_weights):
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
    while True:
        for i in xrange(num_feature):
            # optimize ith weights
            current_weights, new_bleu = search_line(pps,tss, bleus, current_weights,i)
        if abs(new_bleu - old_bleu) < threshold:
            break
    return current_weights,new_bleu

def get_reference(config):
    fn = config['reference']
    f = open(fn)
    refs = []
    for line in f:
        ll = line.strip().split()
        refs.append(ll)
    return refs




if __name__ == '__main__':
    main()

