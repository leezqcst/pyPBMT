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
            if name in config:
                self.phrase_weights.append(config[name])
        if 'wwp' in config:
            self.word_penalty = config['wwp']

        if 'wpp' in config:
            self.phrase_penalty = config['wpp']

        if 'wlm' in config:
            self.lm_weight = config['wlm']

        if 'wd' in config:
            self.d_weight = config['wd']

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
        t = weight + (random()-0.5)*2
        temp.append(t)
    return temp
    
        
def weight_to_config(weights,config):
    i = 0
    for name in ['w0','w1','w2','w3']:
        if name in config:
            config[name] = weights[i]
            i+=1

    if 'wpp' in config:
        config['wpp'] = weights[i]
        i+=1        

    if 'wwp' in config:
        config['wwp'] = weights[i]
        i+=1

        
    if 'wlm' in config:
        config['wlm'] = weights[i]
        i+=1
        
    if 'wd' in config:
        config['wd'] = weights[i]
        i+=1

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
