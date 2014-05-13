#!/usr/bin/env python
# -*- coding: utf-8 -*-
# reordering model without language model

import sys
import os
from multiprocessing import Queue, Process
import subprocess as sp
from math import log, exp
from datetime import datetime
import cPickle
from . import phraseTable
from . import multip
from . import monotone
from . import heap_lm 
from . import heap_lm_k
from .lm import lm_order_best, lm_order_list, lmize
from . import lm
from . import carmel_related as _mcr
from utils.utils import array_plus, array_minus

def stderr(s):
    sys.stderr.write(s + '\n')


def future_cost_and_options(f_sentence, phrase_table, seen_words):
    fcost = {}
    f_l = len(f_sentence)
    options = None
    new_phrase_table = None
    for start in xrange(f_l):
        f_sentence_temp = f_sentence[start:f_l]
        states, trans_key, npt = monotone.decode(
            f_sentence_temp, phrase_table, seen_words, True)
        fcost[start] = {}
        for i in xrange(1, len(states)):
            end = start + i
            fcost[start][end] = states[i]
        if start == 0:
            options = trans_key
            new_phrase_table = npt
    return fcost, options, new_phrase_table


def cross(cover, option):
    for i in cover:
        if i >= option[0] and i < option[1]:
            return True
    return False


def merge(cover, option):
    new_cover = list(cover)
    news = range(option[0], option[1])
    s = -1
    if len(new_cover) == 0:
        new_cover = news
    elif new_cover[0] >= option[1]:
        new_cover = news + new_cover
    elif new_cover[-1] < option[0]:
        new_cover = new_cover + news
    else:
        for i in xrange(len(new_cover) - 1):
            if new_cover[i] < option[0] and new_cover[i + 1] >= option[1]:
                new_cover = new_cover[0:i + 1] + news + new_cover[i + 1:]
                break
    return tuple(new_cover)


def get_future_cost(fcost, cover, l):
    temp = []
    if len(cover) == 0:
        temp.append((0, l))
    else:
        if cover[0] > 0:
            temp.append((0, cover[0]))
        if cover[-1] < l - 1:
            temp.append((cover[-1] + 1, l))
        for i in xrange(len(cover) - 1):
            if cover[i] + 1 < cover[i + 1]:
                temp.append((cover[i] + 1, cover[i + 1]))
    c = 0.0
    for start, end in temp:
        c += fcost[start][end]
    return c



def decode(f_sentence, phrase_table, seen_words, lm_model,
           lm_weight, d_weight, d_limit, beam_size, debug=False):

    start = datetime.now()

    # using monotone to generate future cost and transition options
    fcost, options, new_phrase_table = future_cost_and_options(
        f_sentence, phrase_table, seen_words)

    new_phrase_table = lmize(lm_model, lm_weight, new_phrase_table)

    if debug:
        for key in new_phrase_table:
            s = new_phrase_table[key][0]
            print key, s
        print sorted(options)

    # beam search

    bins = []
    for i in xrange(len(f_sentence) + 1):
        b = heap_lm.Heap(beam_size)
        bins.append(b)

    empty = heap_lm.State((), 0, '<s>', 0, 0)
    bins[0].add(empty)

    for i in xrange(len(f_sentence)):
        b = bins[i]

        for k in xrange(b.size):
            state = b.data[k]

            for option in options:
                cover = state.cover
                j = state.j
                d = option[0] - j
                last_e = state.last_e

                if (not cross(cover, option)) and (abs(d) <= d_limit):

                    # whether current f_pharse is the last part un-translated 
                    is_end = False
                    new_cover = merge(cover, option)
                    if len(new_cover) == len(f_sentence):
                        is_end = True

                    # reorder the e_pharse based on last_e LM score
                    f_phrase = tuple(f_sentence[option[0]:option[1]])
                    items = new_phrase_table[f_phrase]
                    items = lm_order_list(
                        lm_model, items, lm_weight, last_e, is_end,limit = 10)

                    # add into the bins
                    if debug:
                        pass
                        stderr('{}'.format(len(items)))
                    
                    for item in items:
                        t_score = item[0]  # lm score has already incorporated
                        d_score = - abs(d) * d_weight  # note!
                        score = d_score + t_score + state.s

                        e_phrase = item[1]
                        new_last_e = e_phrase[-1]
                        new_j = option[1]
                        new_h = get_future_cost(fcost, new_cover, len(f_sentence))

                        child_state = heap_lm.State(
                            new_cover, new_j, new_last_e, score, new_h)
                        child_state.father = state
                        child_state.e_phrase = e_phrase
                        n_cover = len(new_cover)
                        bins[n_cover].add(child_state)

    if debug:
        for b in bins:
            print b.data

    # backtrack
    b = bins[-1]
    current = b.getMax()
    i = len(bins) - 2
    while current is None:
        current = bins[i].getMax()
        i -= 1
        if i == 0:
            break
    score = current.f
    e_phrases = []
    while True:
        father = current.father
        if father is None:
            break
        e_phrase = current.e_phrase
        e_phrases.append(e_phrase)
        current = father

    e_phrases.reverse()
    e_sentence = [' '.join(list(x)) for x in e_phrases]
    e_sentence = ' '.join(e_sentence)
    end = datetime.now()
    
    print end-start

    return (e_phrases, e_sentence, score)


            


def decode_k(f_sentence, phrase_table, seen_words, lm_model,
           lm_weight, d_weight, d_limit, beam_size, num_feature, tempFilePath, debug=False, k_best = 1):
    start = datetime.now()

    # using monotone to generate future cost and transition options
    fcost, options, new_phrase_table = future_cost_and_options(
        f_sentence, phrase_table, seen_words)

    new_phrase_table = lmize(lm_model, lm_weight, new_phrase_table)

    if debug:
        for key in new_phrase_table:
            s = new_phrase_table[key][0]
            print key, s
        print sorted(options)

    # beam search

    bins = []
    for i in xrange(len(f_sentence) + 1):
        b = heap_lm_k.Heap(beam_size,k_best)
        bins.append(b)

    empty = heap_lm_k.State((), 0, '<s>', 0, 0,[0.0]*num_feature)
    bins[0].add(empty)

    for i in xrange(len(f_sentence)):
        b = bins[i]

        for k in xrange(b.size):
            state = b.data[k]

            for option in options:
                cover = state.cover
                j = state.j
                d = option[0] - j
                last_e = state.last_e

                if (not cross(cover, option)) and (abs(d) <= d_limit):

                    # whether current f_pharse is the last part un-translated 
                    is_end = False
                    new_cover = merge(cover, option)
                    if len(new_cover) == len(f_sentence):
                        is_end = True

                    # reorder the e_pharse based on last_e LM score
                    f_phrase = tuple(f_sentence[option[0]:option[1]])
                    items = new_phrase_table[f_phrase]
                    items = lm_order_list(
                        lm_model, items, lm_weight, last_e, is_end,limit = 10)

                    # add into the bins
                                        
                    for item in items:
                        t_score = item[0]  # lm score has already incorporated
                        d_score = - abs(d) * d_weight  # note!
                        score = d_score + t_score + state.s

                        partial_score = list(item[2])
                        partial_score.append( - abs(d) )
                        new_partial_score = array_plus(partial_score, state.partial_score)

                        e_phrase = item[1]
                        new_last_e = e_phrase[-1]
                        new_j = option[1]
                        new_h = get_future_cost(fcost, new_cover, len(f_sentence))


                        child_state = heap_lm_k.State(
                            new_cover, new_j, new_last_e, score, new_h, new_partial_score)
                        child_state.e_phrase = e_phrase
                        delta = (child_state.f, child_state.s - state.s, child_state.e_phrase,array_minus(child_state.partial_score, state.partial_score),state)
                        child_state.fathers = [delta,]
                        n_cover = len(new_cover)
                        bins[n_cover].add(child_state)


    if debug:
        for b in bins:
            print b.data

    cPickle.dump(bins,open('/Users/xingshi/Workspace/misc/pyPBMT/var/temp.pickle1','w'))
    # generate fst to use carmel
    #paths = _mcr.get_k_best_paths(bins,k_best,tempFilePath)


    end = datetime.now()
    print end-start

    




######## Test Code ############

def test_merge():
    cover = (1, 4, 5)
    option = (0, 1)
    print merge(cover, option)


def test_decode():
    weights = [0.2, 0.2, 0.2, 0.2]
    mask = [1, 1, 1, 1]
    wp = 0.1
    pp = 0.1
    d_weight = 0.3
    d_limit = 6
    lm_weight = 0.5
    beam_size = 100
    f_string = 'ich mag diesen tisch sehr viel .'
    #'als abgeordneter einer tabakanbauregion möchte ich hier die vorbehalte zum ausdruck bringen , die ich zu diesem bericht über den vorschlag für eine tabakrichtlinie habe .'
    #'mit anderen programmen soll china bei der erfüllung bestimmter wto-vorgaben unterstützt werden .'
    #'1848 , während des kampfes gegen die herrschaft der österreich-ungarischen monarchie in mailand , als es den mailänder patrioten gelang , den zigarettenkonsum einzuschränken , um die monarchie finanziell zu schädigen .'
    #'an der spitze der australischen delegation , der drei abgeordnete des repräsentantenhauses sowie zwei abgeordnete des senats angehören , steht bruce baird .'

    #'ich mag diesen tisch sehr viel .'

    f_sentence = f_string.split()
    phrase_table, seen_words = phraseTable.get_phrase_table(
        weights, mask, pp, wp, '../data/phrase-table')

    lm_model = lm.getLM()

    e_phrases, e_sentence, score = decode(
        f_sentence, phrase_table, seen_words, lm_model, lm_weight, d_weight, d_limit, beam_size, False)
    print e_phrases
    print e_sentence
    print score


def test_decode_k():
    weights = [0.2, 0.2, 0.2, 0.2]
    mask = [1, 1, 1, 1]
    wp = 0.1
    pp = 0.1
    d_weight = 0.3
    d_limit = 6
    lm_weight = 0.5
    beam_size = 100
    f_string = 'ich mag diesen tisch sehr viel .'
    #'als abgeordneter einer tabakanbauregion möchte ich hier die vorbehalte zum ausdruck bringen , die ich zu diesem bericht über den vorschlag für eine tabakrichtlinie habe .'
    #'mit anderen programmen soll china bei der erfüllung bestimmter wto-vorgaben unterstützt werden .'
    #'1848 , während des kampfes gegen die herrschaft der österreich-ungarischen monarchie in mailand , als es den mailänder patrioten gelang , den zigarettenkonsum einzuschränken , um die monarchie finanziell zu schädigen .'
    #'an der spitze der australischen delegation , der drei abgeordnete des repräsentantenhauses sowie zwei abgeordnete des senats angehören , steht bruce baird .'

    #

    f_sentence = f_string.split()
    phrase_table, seen_words = phraseTable.get_phrase_table(
        weights, mask, pp, wp, '../data/phrase-table')

    lm_model = lm.getLM()
    num_feature = 8
    decode_k(
        f_sentence, phrase_table, seen_words, lm_model, lm_weight, d_weight, d_limit, beam_size,num_feature,'', True, k_best = 10)
    





if __name__ == '__main__':

    a = datetime.now()
    test_decode_k()
    #main()
    b = datetime.now()
    stderr(str(b - a))
