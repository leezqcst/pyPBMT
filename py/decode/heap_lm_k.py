import heapq

class State:
    def __init__(self,cover,j,last_e,s,h, partial_score):
        self.cover = cover # ordered tuple
        self.j = j # ordered tuple
        self.last_e = last_e
        self.s = s
        self.h = h
        self.f = self.s + self.h
        self.partial_score = partial_score
        self.e_phrase = None
        self.fathers = [] # (f,s,e_phrase,partial_score,State) # minimize heap

    
    def getKey(self):
        return (self.cover,self.j,self.last_e)

    def clone(self,state):
        self.cover = state.cover
        self.j = state.j
        self.last_e = state.last_e
        self.s = state.s
        self.h = state.h
        self.f = state.f
        self.partial_score = state.partial_score
        self.fathers = state.fathers
        self.e_phrase = state.e_phrase

    def absorb(self,state,father_limit):
        value_changed = False
        if self.f < state.f: # add to fathers
            value_changed = True
            self._father_add(state.fathers[0],father_limit)
            self.h = state.h
            self.s = state.s
            self.f = state.f
            self.partial_score = state.partial_score
            self.e_phrase = state.e_phrase
        else:
            self._father_add(state.fathers[0],father_limit)

        return value_changed

    def _father_add(self,father_state,father_limit):
        heapq.heappush(self.fathers,father_state)
        if len(self.fathers) > father_limit:
            heapq.heappop(self.fathers)

        


    def __repr__(self):
        s = [ repr(self.cover), self.j, self.last_e]
        key_str = ' '.join([str(x) for x in s])
        s = [self.s,self.h,self.f,self.e_phrase]
        state_str = ' '.join([str(x) for x in s])
        s = ['({} {} {} {} {})'.format(x[0],x[1],x[2],x[3],x[4].getKey()) for x in self.fathers]
        father_str = ':'.join(s) 
        return '::'.join([key_str,state_str,father_str])


class Heap:
    # minimize heap
    def __init__(self,max_size,father_limit=1):
        self.size = 0
        self.max_size = max_size
        self.data = [None] * (max_size+1)
        self.d = {} # store the subscription of data
        self.father_limit = father_limit

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
            value_changed = self.data[i].absorb(state,self.father_limit)
            if value_changed:
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
    fathers = []
    for i in xrange(5):
        s = State((1,i),1,'a',i,i,[i,i,i])
        s.e_phrase = 'e'
        fathers.append(s)

    h = Heap(3,3)
    k = 0
    for father in fathers:
        for i in xrange(4):
            child = State((i,i),1,'a',i+k,i,[i,i,k])
            child.e_phrase = '{}{}'.format(i,i)
            child.fathers = [(child.f,child.s,child.e_phrase,child.partial_score,father),]

            h.add(child)
            k+=1
            print
            print 'add:', child
            print h

















if __name__ == '__main__':
    test()

    
        
