import sys
import random
import networkx as nx
import numpy as np

if __name__ == "__main__":
    if len(sys.argv) != 11:
        print("Usage: python generate_network_positions.py <num_txhost> <num_rxhost> <num_rxtxhost> <num_relays> <max_area> <seed> <max_reps> <betweenness_threshold> <num_repeats> <outputfile>")
        sys.exit(1)

    num_txhost = int(sys.argv[1])
    num_rxhost = int(sys.argv[2])
    num_rxtxhost = int(sys.argv[3])
    num_relays = int(sys.argv[4])
    max_area = float(sys.argv[5])
    seed = int(sys.argv[6])
    max_reps = int(sys.argv[7])
    betweenness_threshold = float(sys.argv[8])
    num_repeats = int(sys.argv[9])
    outputfile = str(sys.argv[10])

    random.seed(seed)

    graphs = []

    for graph_num in range(num_repeats):
        print(f"\n=== Generating graph {graph_num} ===")

        for attempt in range(3):
            G = nx.Graph()

            for i in range(num_txhost):
                x = random.uniform(0, max_area)
                y = random.uniform(0, max_area)
                node_id = f"txhost[{i}]"
                G.add_node(node_id, type="txhost", pos=(x, y))
                print(f"txhost,{x},{y}")

            for i in range(num_rxhost):
                x = random.uniform(0, max_area)
                y = random.uniform(0, max_area)
                node_id = f"rxhost[{i}]"
                G.add_node(node_id, type="rxhost", pos=(x, y))
                print(f"rxhost,{x},{y}")

            for i in range(num_rxtxhost):
                x = random.uniform(0, max_area)
                y = random.uniform(0, max_area)
                node_id = f"rxtxhost[{i}]"
                G.add_node(node_id, type="rxtxhost", pos=(x, y))
                print(f"rxtxhost,{x},{y}")

            found = False
            for rep in range(max_reps):
                for i in range(num_relays):
                    x = random.uniform(0, max_area)
                    y = random.uniform(0, max_area)
                    node_id = f"relay[{i}]"
                    G.add_node(node_id, type="relay", pos=(x, y))

                # Add edges between nodes within 200m distance
                edges = nx.geometric_edges(G, radius=200)
                G.add_edges_from(edges)

                if not nx.is_connected(G):
                    print(f"Graph {graph_num}, Attempt {attempt}, Rep {rep}: Graph not connected, trying again")
                    for i in range(num_relays):
                        G.remove_node(f"relay[{i}]")
                    continue

                betweenness = nx.betweenness_centrality(G)
                relay_betweenness = [betweenness[f"relay[{i}]"] for i in range(num_relays)]
                print(f"Graph {graph_num}, Attempt {attempt}, Rep {rep}: Relay betweenness: {relay_betweenness}")

                if all(b > betweenness_threshold for b in relay_betweenness):
                    found = True
                    break

                for i in range(num_relays):
                    G.remove_node(f"relay[{i}]")

            if found:
                break

            print(f"Graph {graph_num}, Attempt {attempt} failed, regenerating all nodes...")

        for i in range(num_relays):
            x, y = G.nodes[f"relay[{i}]"]["pos"]
            print(f"relay,{x},{y}")

        graphs.append(G)

    # Generate output file
    with open(outputfile, "w") as f:
        for node_id in graphs[0].nodes():
            node_type = graphs[0].nodes[node_id]["type"]
            if node_type == "txhost":
                idx = int(node_id.split("[")[1].split("]")[0])
                x_values = ", ".join([f"{G.nodes[f'txhost[{idx}]']['pos'][0]:.2f}" for G in graphs])
                y_values = ", ".join([f"{G.nodes[f'txhost[{idx}]']['pos'][1]:.2f}" for G in graphs])
                f.write(f"**.txhost[{idx}].mobility.initialX = ${{{x_values} ! repetition}}m\n")
                f.write(f"**.txhost[{idx}].mobility.initialY = ${{{y_values} ! repetition}}m\n")
            elif node_type == "rxhost":
                idx = int(node_id.split("[")[1].split("]")[0])
                x_values = ", ".join([f"{G.nodes[f'rxhost[{idx}]']['pos'][0]:.2f}" for G in graphs])
                y_values = ", ".join([f"{G.nodes[f'rxhost[{idx}]']['pos'][1]:.2f}" for G in graphs])
                f.write(f"**.rxhost[{idx}].mobility.initialX = ${{{x_values} ! repetition}}m\n")
                f.write(f"**.rxhost[{idx}].mobility.initialY = ${{{y_values} ! repetition}}m\n")
            elif node_type == "rxtxhost":
                idx = int(node_id.split("[")[1].split("]")[0])
                x_values = ", ".join([f"{G.nodes[f'rxtxhost[{idx}]']['pos'][0]:.2f}" for G in graphs])
                y_values = ", ".join([f"{G.nodes[f'rxtxhost[{idx}]']['pos'][1]:.2f}" for G in graphs])
                f.write(f"**.rxtxhost[{idx}].mobility.initialX = ${{{x_values} ! repetition}}m\n")
                f.write(f"**.rxtxhost[{idx}].mobility.initialY = ${{{y_values} ! repetition}}m\n")
            elif node_type == "relay":
                idx = int(node_id.split("[")[1].split("]")[0])
                x_values = ", ".join([f"{G.nodes[f'relay[{idx}]']['pos'][0]:.2f}" for G in graphs])
                y_values = ", ".join([f"{G.nodes[f'relay[{idx}]']['pos'][1]:.2f}" for G in graphs])
                f.write(f"**.relay[{idx}].mobility.initialX = ${{{x_values} ! repetition}}m\n")
                f.write(f"**.relay[{idx}].mobility.initialY = ${{{y_values} ! repetition}}m\n")
