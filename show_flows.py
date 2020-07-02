#!/usr/bin/env python3
import json
import sys

import networkx as nx


def main(argv):
    try:
        graphml_name = argv[1]
    except IndexError:
        print(f"usage: {argv[0]} GRAPHML_FILE [JSON_FILE]")
        exit(2)

    try:
        json_name = argv[2]
    except IndexError:
        json_name = graphml_name + "-candidates.json"

    G = nx.read_graphml(graphml_name)
    with open(json_name, encoding="utf-8") as fd:
        paths = json.load(fd)

    for path, attrs in paths:
        nu, _, _, _ = path[0]
        print(G.nodes[nu])
        for nu, nv, ek, _ in path:
            print("->", G.edges[nu, nv, ek])
            print(G.nodes[nv])
        if "lcs" in attrs:
            print("-" * 60)
            print(f"Longest common substring: {attrs['lcs']}")
        print("=" * 60)


if __name__ == "__main__":
    main(sys.argv)
