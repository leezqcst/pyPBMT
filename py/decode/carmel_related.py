import cPickle
from . import heap_lm_k
import subprocess as sp
from utils.utils import array_plus

def generate_fst_str(bins):
    fst_strs = []
    for i in xrange(len(bins)-1,0,-1):
        bin = bins[i]
        if i == len(bins)-1:
            dst = '_END'
            for j in xrange(bin.size):
                name = '{}_{}'.format(i,j)
                s = '({} ({} {} {} {}))'.format(name,dst,dst,dst,1)
                fst_strs.append(s)
        for j in xrange(bin.size):
            state = bin.data[j]
            for ftid,father_tuple in enumerate(state.fathers):
                father_state = father_tuple[-1]
                weight = father_tuple[1]
                dst = '{}_{}'.format(i,j)
                dst_accept = '{}_{}_{}'.format(i,j,ftid)
                father_key = father_state.getKey()
                father_bin_id = len(father_key[0])
                src_j = bins[father_bin_id].d[father_key]
                src = '{}_{}'.format(father_bin_id,src_j)
                s = '({} ({} {} e^{}))'.format(src,dst,dst_accept,weight)
                fst_strs.append(s)
    fst_strs.reverse()
    fst_str = '\n'.join(fst_strs)
    fst_str = '_END\n'+fst_str
    return fst_str

def carmel_parse(fst_path,k_best):
    cmd = 'carmel -OWk {} {}'.format(k_best,fst_path)
    carmel = sp.Popen(cmd.split(),stdout=sp.PIPE, stdin=sp.PIPE)
    output,err = carmel.communicate()
    paths = []
    for line in output.split('\n'):
        state_strs = line.split()
        if len(state_strs)>0:
            path = []
            for state_str in state_strs:
                if state_str == '_END':
                    break
                ss = state_str.split('_')
                bin_id = int(ss[0])
                state_id = int(ss[1])
                ft_id = int(ss[2])
                path.append((bin_id,state_id,ft_id))
            paths.append(path)
    return paths

def get_k_best_paths(bins,k_best,tempFilePath):
    fst_str = generate_fst_str(bins)
    f = open(tempFilePath,'w')
    f.write(fst_str)
    f.close()
    paths = carmel_parse(tempFilePath,k_best)
    return paths

def backtrack_k(bins,paths):
    partial_scores = []
    translated_sentences = []
    tags = heap_lm_k.FT.tags
    for path in paths:
        partial_score = bins[0].data[0].partial_score
        translated_sentence = []
        father_key = bins[0].data[0].getKey()
        for i in xrange(len(path)):
            bin_id = path[i][0]
            state_id = path[i][1]
            ft_id = path[i][2]
            state = bins[bin_id].data[state_id]
            father_tuple = state.fathers[ft_id]
            assert( father_key == father_tuple[tags.FATHER_KEY].getKey())
            e_pharse = father_tuple[tags.E_PHRASE]
            ps = father_tuple[tags.PARTIAL_SCORE]
            partial_score = array_plus(partial_score,ps)
            translated_sentence.append(e_pharse)
            father_key = state.getKey()
        partial_scores.append(partial_score)
        translated_sentences.append(translated_sentence)
    return partial_scores, translated_sentences

if __name__ == '__main__':
    f = open('/Users/xingshi/Workspace/misc/pyPBMT/var/temp.pickle1')
    bins = cPickle.load(f)
    f.close()
    # fst_str = generate_fst_str(bins)
    # f = open('/Users/xingshi/Workspace/misc/pyPBMT/var/temp.fsa','w')
    # f.write(fst_str)
    temp_path = '/Users/xingshi/Workspace/misc/pyPBMT/var/temp.fsa'
    k_best = 5
    paths = get_k_best_paths(bins,k_best,temp_path)
    print paths
    ps,ts = backtrack_k(bins,paths)
    print ts
    print ps
    cPickle.dump((ps,ts),open('/Users/xingshi/Workspace/misc/pyPBMT/var/pts.pickle','w'))
