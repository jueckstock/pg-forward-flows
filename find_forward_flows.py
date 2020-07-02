#!/usr/bin/env python3
import functools
import json
import os
import sys
import re
from collections import deque

import networkx as nx


def whole_string(s: str) -> str:
    return s


PARAM_PART = re.compile(r"[?#](.*)$")


def params_only(s: str) -> str:
    m = PARAM_PART.search(s)
    return m.group(1) if m else ""


WEB_APIS = {
    "Document.referrer": params_only,
    "Location.href": params_only,
    # "Location.protocol",
    # "Location.port",
    # "Location.host",
    # "Location.hostname",
    "Location.hash": whole_string,
    "Location.search": whole_string,
    # "Location.replace",
    # "Location.assign",
    # "Location.reload",
}

SINK_EDGES = {"storage set"}

SINK_NODES = {
    "local storage",
    "cookie jar",
    "resource",
}


def get_forward_edges(G, node, base_id):
    return [
        (nu, nv, ek, eid)
        for nu, nv, ek, eid in G.edges(node, data="id", keys=True)
        if eid > base_id
    ]


def forward_flow_set(G, source_node):
    touched_nodes = {source_node}
    edge_queue = deque(get_forward_edges(G, source_node, G.nodes[source_node]["id"]))
    while edge_queue:
        nu, nv, ek, eid = edge_queue.popleft()
        print(nv, G.nodes[nv], ek, G.edges[nu, nv, ek])
        touched_nodes.add(nv)
        edge_queue.extend(get_forward_edges(G, nv, eid))
    return touched_nodes


def get_next_forward_edge(G, node, base_id):
    edge_list = [
        (nu, nv, ek, eid)
        for nu, nv, ek, eid in G.edges(node, data="id", keys=True)
        if eid == base_id + 1
    ]
    if edge_list:
        return edge_list[0]
    else:
        return None


def forward_flow_dfs(G, source_node):
    source_edge_set = set(G.edges(nbunch=source_node, data="id", keys=True))

    def _rffd(edge1):
        try:
            source_edge_set.remove(edge1)
        except KeyError:
            pass
        nu, nv, ek, eid = edge1
        edge2 = get_next_forward_edge(G, nv, eid)
        if edge2:
            return [edge1] + _rffd(edge2)
        else:
            return [edge1]

    while source_edge_set:
        edge1 = source_edge_set.pop()
        yield _rffd(edge1)


# Returns longest common substring of X[0..m-1] and Y[0..n-1]
# (shamelessly stolen/hacked from https://www.geeksforgeeks.org/longest-common-substring-dp-29/)
# (the original version tracked/reported only substring lengths; this version does string values)
def LCSubStr(X, Y):
    m = len(X)
    n = len(Y)

    # Create a table to store longest common suffixes of substrings.
    # Note that LCSuff[i][j] contains the longest common suffix of
    # X[0...i-1] and Y[0...j-1]. The first row and first column entries
    # have no logical meaning, they are used only for simplicity of the program.

    # LCSuff is the table with each cell initially empty
    LCSuff = [["" for k in range(n + 1)] for l in range(m + 1)]

    # To store the longest common substring (which implies its length)
    result = ""

    # Following steps to build
    # LCSuff[m+1][n+1] in bottom up fashion
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                LCSuff[i][j] = ""
            elif X[i - 1] == Y[j - 1]:
                LCSuff[i][j] = LCSuff[i - 1][j - 1] + X[i - 1]
                if len(LCSuff[i][j]) > len(result):
                    result = LCSuff[i][j]
            else:
                LCSuff[i][j] = ""
    return result


def main(argv):
    try:
        filename = argv[1]
    except IndexError:
        print(f"usage: {argv[0]} GRAPHML_FILENAME")
        return

    G = nx.read_graphml(filename)

    sources = {}
    for nid, attrs in G.nodes.items():
        if attrs.get("node type") == "web API" and attrs.get("method") in WEB_APIS:
            sources[nid] = attrs

    found_paths = []
    for s, sattr in sources.items():
        source_value_filter = WEB_APIS[sattr["method"]]

        for path in forward_flow_dfs(G, s):
            nu2, nv2, ek2, _ = path[-1]
            eattr2 = G.edges[nu2, nv2, ek2]

            if eattr2["edge type"] in SINK_EDGES:
                nu1, nv1, ek1, _ = path[0]
                eattr1 = G.edges[nu1, nv1, ek1]
                first_value = source_value_filter(eattr1.get("value", ""))
                last_value = eattr2.get("value", "")
                lcs = LCSubStr(first_value, last_value)
                if lcs:
                    found_paths.append((path, {"lcs": lcs}))
                    print(lcs)

    if found_paths:
        with open(filename + "-candidates.json", "wt", encoding="utf-8") as fd:
            json.dump(found_paths, fd)
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main(sys.argv)
