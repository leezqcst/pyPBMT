#!/usr/bin/env python
'''
Author: Xing Shi
'''
import argparse
from multiprocessing import Queue, Process
import subprocess as sp
import sys


def ap():
    # argparse http://docs.python.org/2/library/argparse.html#module-argparse
    parser = argparse.ArgumentParser(
        description='Run any command line in multiprocess. \n'
        'The program should read from STDIN and output to STDOUT in a batch style.')

    # actions:
    # action='store_const', const=42
    # action='store_true'

    parser.add_argument('-j', type=int, required=True, help="# of processes")
    parser.add_argument('-g', type=int, default = 1 , help= "# of group lines")
    parser.add_argument('-b', default = False, action='store_true',help='the cmd can process multiple lines at a time')
    # optional arguments

    parser.add_argument(
        '-c', required=True, type=str, help="command line")
    # version info
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    args = vars(parser.parse_args())
    return args


def worker(lines, cmd, r, b, g, q):
    
    out, err ='',''
    if b:
        p = sp.Popen(cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE)
        out, err = p.communicate(input=''.join(lines))
    else:
        l = len(lines)/g
        for i in xrange(l):
            p = sp.Popen(cmd.split(), stdin=sp.PIPE, stdout=sp.PIPE)
            outt,errr = p.communicate(input=''.join(lines[i*g:(i+1)*g]))
            out += outt
            err += err
    q.put((r, out))


def split_list(l, n, g):
    sn = 0
    lg = len(l)/g
    if lg % n == 0:
        sn = lg / n
    else:
        sn = lg / n + 1

    results = []
    for i in xrange(n):
        start = i * sn * g
        end = min(len(l), (i + 1) * sn * g)
        results.append(l[start:end])
    return results


def main():
    args = ap()
    n_core = args['j']
    cmd = args['c']
    g = args['g']
    b = args['b']

    lines = sys.stdin.readlines()
    line_groups = split_list(lines, n_core,g)

    processes = []
    queue = Queue()
    for i in xrange(n_core):
        group = line_groups[i]
        p = Process(target=worker, args=(group, cmd, i, b, g, queue))
        p.start()
        processes.append(p)

    d = {}
    for i in xrange(n_core):
        key, out = queue.get()
        d[key] = out

    for p in processes:
        p.join()

    for i in xrange(n_core):
        group = d[i]
        if group != '':
            print group,

if __name__ == '__main__':
    main()

