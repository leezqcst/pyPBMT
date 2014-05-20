from random import random
class Weight:
    def __init__(self):
        self.phrase_weights = []
        self.word_penalty = 0.0
        self.phrase_penalty = 0.0
        self.lm_weight = 0.0
        self.d_weight = 0.0

    def parse(self, config):
        for name in ['w0','w1','w2','w3']:
            if config.has_option('weights',name):
                self.phrase_weights.append(config.getfloat('weights',name))

        if config.has_option('weights','wpp'):
            self.phrase_penalty = config.getfloat('weights','wpp')

        if config.has_option('weights','wwp'):
            self.word_penalty = config.getfloat('weights','wwp')

        if config.has_option('weights','wlm'):
            self.lm_weight = config.getfloat('weights','wlm')

        if config.has_option('weights','wd'):
            self.d_weight = config.getfloat('weights','wd')


    def get_weights(self):
        # standard order: ['w0','w1','w2','w3','wpp','wwp','wlm','wd']
        temp = list(self.phrase_weights)
        temp.append(self.phrase_penalty)
        temp.append(self.word_penalty)
        temp.append(self.lm_weight)
        temp.append(self.d_weight)
        return temp
    
def get_random_weights(weights):
    # based on weights, random in +- 1
    temp = []
    for weight in weights:
        t = weight + (random()-0.5)*6
        temp.append(t)
    return temp
    
        
def weight_to_config(weights,config):
    i = 0

    for name in ['w0','w1','w2','w3']:
        if config.has_option('weights',name):
            config.set('weights',name,str(weights[i]))
            i += 1

    if config.has_option('weights','wpp'):
        config.set('weights','wpp',str(weights[i]))
        i += 1
        
    if config.has_option('weights','wwp'):
        config.set('weights','wwp',str(weights[i]))
        i += 1
        
    if config.has_option('weights','wlm'):
        config.set('weights','wlm',str(weights[i]))
        i += 1
        
    if config.has_option('weights','wd'):
        config.set('weights','wd',str(weights[i]))
        i += 1

    return config

        
def normalize_weights(weights):
    temp = []
    biggest = .0
    for w in weights:
        if biggest < abs(w):
            biggest = abs(w)
    for w in weights:
        temp.append(w/biggest)
    return temp
