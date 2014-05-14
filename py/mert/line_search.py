import cPickle
import numpy as np

def combine_break_points(break_points_list):
    


def search_break_points(partial_scores,feature_values,feature_id):
    '''
    partial_scores, feature_values, should be a 2D np.array
    '''
    feature = partial_scores[:,feature_id]
    b = np.dot(partial_scores,feature_values.T)[:,0]
    b = b-feature # 1 d
    
    lines = [(i,feature[i],b[i]) for i in xrange(len(partial_scores))] 
    lines = sorted(lines, key = lambda x: (x[1],-x[2])) # sort according to slope of target weight (the target feature value)

    print lines

    # search break points
    break_points = []
    belongs = []
    current = 0
    belongs.append(lines[0][0])
    while True:
        left_most = float('inf')
        belong = -1
        a1 = lines[current][1]
        b1 = lines[current][2]
        next_id = -1
        for i in xrange(current+1,len(lines)):
            a2 = lines[i][1]
            b2 = lines[i][2]
            if a1 == a2:
                continue
            break_point = (b2-b1)/(a1-a2)
            if break_point < left_most:
                left_most = break_point
                belong = lines[i][0]
                next_id = i
        if belong != -1:
            break_points.append(left_most)
            belongs.append(belong)
        current = next_id
        if current == -1 or current == len(lines)-1:
            break

    return break_points, belongs
    


if __name__ == '__main__':
    ps,ts = cPickle.load(open('/Users/xingshi/Workspace/misc/pyPBMT/var/pts.pickle'))
    ps = np.array(ps)
    feature_values = np.array([[0.2,0.2,0.2,0.2,0.1,0.1,0.5,0.3]])
    bps,bls = search_break_points(ps,feature_values,5)
    print bps
    print bls
