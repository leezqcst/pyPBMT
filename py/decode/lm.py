# language model

import kenlm

def getLM():
    path = '/Users/xingshi/Workspace/misc/NLPKK/599/hw3/data/europarl.en.2gram.arpa'
    model = kenlm.LanguageModel(path)
    return model

def lm_score(model,sentence,with_start,with_end): # sentence is a list
    score = 0.0
    start = 0
    end = len(sentence) + 1
    if not with_start:
        start = 1
    if not with_end:
        end = end - 1
    k = 0
    for prob, length in model.full_scores(' '.join(sentence)):
        if k >= start and k < end:
            score += prob
        k += 1

    return score

def lm_2(model,w1,w2):
    sentence = w1+' '+w2
    k = 0
    for prob, length in model.full_scores(sentence):
        if k == 1:
            return prob
        k += 1

def lm_start(model,w):
    k = 0
    for prob,length in model.full_scores(w):
        if k == 0:
            return prob
        k+=1


def lm_end(model,w):
    k = 0
    for prob,length in model.full_scores(w):
        if k == 1:
            return prob
        k+=1




def lm_order_best(lm_model, items, lm_weight, last_e, is_end):
    '''Get the best e_phrase given lm_weight, last_e and is_end
    
    items: [(score,e_phrase)] for the same f_phrase from phrase_table
    is_end: whether this e_phrase will appear at the end of the translated sentence.

    return: the single (score,e_phrase) with the highest score
    '''
    temp = None
    max_score = -float('inf')
    for score, e_phrase in items:
        kms = 0.0
        if score < max_score:
            continue
        if last_e == '<s>':
            lms = lm_start(lm_model, e_phrase[0])
        else:
            lms = lm_2(lm_model, last_e, e_phrase[0])
        if is_end:
            lms += lm_end(lm_model, e_phrase[-1])
        score += lm_weight * lms
        if max_score < score:
            max_score = score
            temp = [(score, e_phrase)]

    return temp


def lm_order_list(lm_model, items, lm_weight, last_e, is_end,limit = -1):
    '''Get the ordered (score,e_phrase) array given lm_weight, last_e and is_end
    
    items: [(score,e_phrase)] for the same f_phrase from phrase_table
    is_end: whether this e_phrase will appear at the end of the translated sentence.

    return: the ordered (score,e_phrase) array with the descending order of weights
    '''
    temp = []
    i  = 0
    for score, e_phrase, partial_score in items:
        if limit != -1 and i > limit:
            break
        i+= 1
        lms = 0.0
        if last_e == '<s>':
            lms = lm_start(lm_model, e_phrase[0])
        else:
            lms = lm_2(lm_model, last_e, e_phrase[0])
        if is_end:
            lms += lm_end(lm_model, e_phrase[-1])
        score += lm_weight * lms
        partial_score[-1] += lms
        temp.append((score,e_phrase,partial_score))
        
    temp = sorted(temp, key= lambda x: -x[0])
    return temp

def lmize(lm_model, lm_weight, phrase_table):
    '''Incorporate the pharse_table with within-pharse-LM scores
    '''
    for key in phrase_table:
        items = phrase_table[key]
        temp = []
        for score, e_phrase, partial_score in items:
            lms = lm_score(lm_model, e_phrase, False, False)
            partial_score.append(lms)
            score += lms * lm_weight
            temp.append((score, e_phrase,partial_score))
        
        temp = sorted(temp, key=lambda x: -x[0])
        phrase_table[key] = temp
    return phrase_table




def test():
    sentence = 'this is good sx'
    model = getLM()
    print lm_score(model,sentence.split(),False,False)

if __name__ == '__main__':
    test()
