import subprocess, sys, os, shlex, time, threading, signal
from collections import namedtuple, defaultdict

StatRecord = namedtuple('StatRecord', 'op clock ppid pid tid nspid ret val file exe cmd')
CommRecord = namedtuple('CommRecord', 'file readers writers interprocess')

def begin_collect(timeout):
    # create a subprocess and collect stdout and ignore stderr
    stap = subprocess.Popen(
            ['stap', 'systemtap/syscall_stats.stp'], 
            stdout=subprocess.PIPE, 
            stderr=open(os.devnull, 'w')
    )

    # if the main loop fails to acquire this lock then
    # it was acquired by the killer thread already and
    # the loop should break
    stop_reading = threading.Lock()

    # function ran in a separate thread
    def _killer():
        time.sleep(timeout)
        stop_reading.acquire(True)
        stap.kill()

    # create thread object
    killer = threading.Thread(target=_killer)

    for out in stap.stdout:
        # this looks weird but we want to start the killer thread
        # only after we've actually received some input since
        # the systemtap probe can take time to init
        if not stop_reading.acquire(False):
            stap.stdout.close()
            break
        if not killer.is_alive():
            killer.start()
        yield StatRecord(*shlex.split(out[:-1]))
        stop_reading.release()


sr = list(begin_collect(timeout=5))
pp = defaultdict(set)
ppp = defaultdict(set)
fpp = defaultdict(set)
for r in sr:
    pp[r.pid].add(r)
    ppp[r.ppid].add(r.pid)
    fpp[r.file].add((r.op, r.pid, r.tid))

import pprint
pprint.pprint(dict(pp))
pprint.pprint(dict(ppp))
pprint.pprint(dict(fpp))

comm = []
for path, calls in fpp.items():
    reads, writes = set(), set()
    for (op, pid, tid) in calls:
        if 'r' in op:
            reads.add(tid)
        if 'w' in op:
            writes.add(tid)

    if reads and writes:
        interprocess = len(reads) != len(writes) or len(reads) > 1
        comm.append(CommRecord(path, reads, writes, interprocess))

pprint.pprint(comm)
