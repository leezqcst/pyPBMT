class State:
    def __init__(self,cover,j,last_e,s,h):
        self.cover = cover # ordered tuple
        self.j = j # ordered tuple
        self.last_e = last_e
        self.s = s
        self.h = h
        self.f = self.s + self.h
        self.father = None # State
        self.e_phrase = None
    
    def getKey(self):
        return (self.cover,self.j,self.last_e)

    def clone(self,state):
        self.cover = state.cover
        self.j = state.j
        self.last_e = state.last_e
        self.s = state.s
        self.h = state.h
        self.f = state.f
        self.father = state.father
        self.e_phrase = state.e_phrase


    def __repr__(self):
        s = [ repr(self.cover), self.j, self.s, self.h, self.f, self.last_e]
        s = [str(x) for x in s]
        return ' '.join(s)





class Heap:
    # minimize heap
    def __init__(self,max_size):
        self.size = 0
        self.max_size = max_size
        self.data = [None] * (max_size+1)
        self.d = {} # store the subscription of data


    def getMax(self):
        max_id = 0
        for i in xrange(self.size):
            if self.data[max_id].f < self.data[i].f:
                max_id = i
        return self.data[max_id]

    def add(self,state):
        key = state.getKey()
        if key in self.d:
            # update
            i = self.d[key]
            if self.data[i].f < state.f:                
                self.data[i].clone(state)
                self.heapify_down(i)
        else:
            # add
            if self.size == self.max_size:
                if self.data[0].f < state.f:
                    del self.d[self.data[0].getKey()]
                    self.data[0].clone(state)
                    self.d[self.data[0].getKey()] = 0
                    self.heapify_down(0)
            else:
                self.data[self.size] = state
                self.d[state.getKey()] = self.size
                self.size += 1
                self.heapify_up(self.size-1)
                
                
    def heapify_down(self,i):
        current = i
        while True:
            l_child = 2*current + 1
            r_child = 2*current + 2
            min_ele = current
            if l_child < self.size and self.data[l_child].f < self.data[min_ele].f:
                min_ele = l_child
            if r_child < self.size and self.data[r_child].f < self.data[min_ele].f:
                min_ele = r_child
            if min_ele == current:
                break
            temp = self.data[current]
            self.data[current] = self.data[min_ele]
            self.data[min_ele] = temp
            self.d[self.data[current].getKey()] = current
            self.d[self.data[min_ele].getKey()] = min_ele
            current = min_ele
    
    def heapify_up(self,i):
        current = i
        while current != 0:
            father = (current+1)/2 - 1
            if self.data[father].f > self.data[current].f:
                temp = self.data[father]
                self.data[father] = self.data[current]
                self.data[current] = temp
                self.d[self.data[father].getKey()] = father
                self.d[self.data[current].getKey()] = current
                current = father
            else:
                break
                      
    def __repr__(self):
        s = ['==HEAP==',self.max_size,self.size, self.d, self.data]
        s = [str(x) for x in s]
        return '\n'.join(s)



def test():
    s1 = State((1,2,3),1,   1,0)
    s2 = State((1,2,3),1,   2,0)
    s3 = State((1,3,2),1,   3,0)
    s4 = State((1,2,3),1,   1,0)
    s = [s1,s2,s3,s4]
    for i in xrange(10):
        ss = State((i,i+1),i+1, i%3+1, i%2)
        s.append(ss)
    h = Heap(10)
    for ss in s:
        #print
        #print 'add:', ss
        h.add(ss)
        #print h















if __name__ == '__main__':
    test()

    
        
