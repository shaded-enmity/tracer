import collections
import os
import pprint
import re
import subprocess
import sys


Endpoint = collections.namedtuple('Endpoint', 'exe pid fd')
Exchange = collections.namedtuple('Exchange', 'address port endpoints')


ws = re.compile(r"\s*")
nl = re.compile(r"[\n\r]*")
ps = re.compile(r"\(.*?\)")
it = re.compile(r"\(\"(.+)\",pid=(\d*),fd=(\d*)\)")


ss_all_args = ["ss", "-xp"]
ss_listen_args = ["ss", "-xlp"]


def command(cmd):
    return nl.split(subprocess.check_output(cmd))


def parse_single(item):
    match = it.match(item)
    if match:
        return Endpoint(*match.groups())
    return None


def parse_users(item):
    if not item:
        return None
    prefix = 'users:'
    if not item.startswith(prefix):
        return None
    return ps.findall(item[len(prefix)+1:-1])


def get_ss_data(cmd):
    out = []
    stuff = command(cmd)
    for line in stuff:
        split = ws.split(line)
        if line and split:
            addr, port = split[4:6]
            parsed = parse_users(split[-1])
            if parsed:
                single = Exchange(addr, port, list(filter(None, [parse_single(p) for p in parsed])))
                out.append(single)
    return out


def get_listening_connections():
    return get_ss_data(ss_listen_args)


def get_all_connections():
    return get_ss_data(ss_all_args)

pprint.pprint(get_listening_connections())
pprint.pprint(get_all_connections())
