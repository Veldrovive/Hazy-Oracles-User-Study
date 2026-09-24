import random
import uuid
from collections import deque
import igraph as ig
import matplotlib.pyplot as plt
import networkx as nx
import base64

def create_children(G, parent_id, parent_type, parent_depth, 
                    a_total, a_expand, b_total, b_expand):
    """
    Generates children for a node, adds them to the graph, and returns 
    the randomly selected subset that should be added to the frontier.
    """
    if parent_type == 'A':
        num_children = a_total
        num_expand = a_expand
        child_type = 'B'
    else:
        num_children = b_total
        num_expand = b_expand
        child_type = 'A'
        
    children = []
    for _ in range(num_children):
        child_id = str(uuid.uuid4())
        # We add the child to the graph as an unexpanded "stub"
        G.add_node(child_id, type=child_type, depth=parent_depth + 1, expanded=False)
        G.add_edge(parent_id, child_id)
        children.append(child_id)
        
    # Randomly select which ones actually go to the frontier
    to_expand = random.sample(children, min(num_expand, num_children))
    return children, to_expand

def expand_tree(max_expansions=40, max_depth=None, dfs_steps=5, bfs_steps=1, 
                a_total=5, a_expand=2, b_total=4, b_expand=1):
    """
    Simulates tree expansion using an alternating deque strategy (DFS/BFS hybrid).
    """
    G = nx.DiGraph()
    root_id = "ROOT"
    G.add_node(root_id, type='A', depth=0, expanded=False)
    
    node_ids = {root_id: tuple()}  # We rely on the new ordered dicts to maintain the order
    node_expansion_order = []
    frontier = deque([root_id])
    expansions = 0
    
    while frontier and expansions < max_expansions:
        # Phase 1: DFS (pop right)
        for _ in range(dfs_steps):
            if not frontier or expansions >= max_expansions: break
            current = frontier.pop() # Pop right
            
            node_data = G.nodes[current]
            node_data['expanded'] = True
            expansions += 1
            
            if max_depth is None or node_data['depth'] < max_depth:
                children, new_nodes = create_children(G, current, node_data['type'], node_data['depth'], 
                                            a_total, a_expand, b_total, b_expand)
                frontier.extend(new_nodes) # Add to right
                parent_node_id = node_ids[current]
                for child_index, child_id in enumerate(children):
                    node_ids[child_id] = parent_node_id + (child_index,)
                    node_expansion_order.append(parent_node_id + (child_index,))
            
        # Phase 2: BFS (pop left)
        for _ in range(bfs_steps):
            if not frontier or expansions >= max_expansions: break
            current = frontier.popleft() # Pop left
            
            node_data = G.nodes[current]
            node_data['expanded'] = True
            expansions += 1
            
            if max_depth is None or node_data['depth'] < max_depth:
                children, new_nodes = create_children(G, current, node_data['type'], node_data['depth'], 
                                            a_total, a_expand, b_total, b_expand)
                frontier.extend(new_nodes) # Add to right
                parent_node_id = node_ids[current]
                for child_index, child_id in enumerate(children):
                    node_ids[child_id] = parent_node_id + (child_index,)
                    node_expansion_order.append(parent_node_id + (child_index,))

    return G, node_ids, node_expansion_order

# --- Visualization Utilities ---

def get_igraph_tree_layout(G, root_id):
    """
    Uses python-igraph's Reingold-Tilford algorithm to compute a tree layout.
    This properly spaces out branches based on subtree size, preventing
    node compression at deeper levels.
    """
    # Map networkx node IDs to integer indices for igraph
    node_list = list(G.nodes())
    node_mapping = {node: i for i, node in enumerate(node_list)}
    
    edges = [(node_mapping[u], node_mapping[v]) for u, v in G.edges()]
    
    g_ig = ig.Graph(n=len(node_list), edges=edges, directed=True)
    root_idx = node_mapping[root_id]
    
    # Compute the tree layout
    layout = g_ig.layout_reingold_tilford(root=[root_idx])
    
    pos = {}
    for i, coords in enumerate(layout):
        # igraph layout coords are (x, y). We negate y so the root is at the top.
        pos[node_list[i]] = (coords[0], -coords[1])
        
    return pos

def draw_and_save_tree(G, filename="tree_expansion.jpg", title="Tree Expansion (Alternating Deque)"):
    plt.figure(figsize=(14, 10))
    
    # Use igraph's Reingold-Tilford algorithm for a structural tree layout
    pos = get_igraph_tree_layout(G, "ROOT")
    
    # Separate nodes by type and whether they were expanded for coloring
    nodes_A_exp = [n for n, d in G.nodes(data=True) if d['type'] == 'A' and d['expanded']]
    nodes_B_exp = [n for n, d in G.nodes(data=True) if d['type'] == 'B' and d['expanded']]
    nodes_A_unexp = [n for n, d in G.nodes(data=True) if d['type'] == 'A' and not d['expanded']]
    nodes_B_unexp = [n for n, d in G.nodes(data=True) if d['type'] == 'B' and not d['expanded']]
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=False, alpha=0.6)
    
    # Draw expanded nodes (Solid colors)
    nx.draw_networkx_nodes(G, pos, nodelist=nodes_A_exp, node_color='skyblue', node_size=300, label='Type A (Expanded)')
    nx.draw_networkx_nodes(G, pos, nodelist=nodes_B_exp, node_color='lightcoral', node_size=300, label='Type B (Expanded)')
    
    # Draw unexpanded nodes (Smaller, faded colors representing the dropped children)
    nx.draw_networkx_nodes(G, pos, nodelist=nodes_A_unexp, node_color='lightblue', node_size=100, alpha=0.4, label='Type A (Stub)')
    nx.draw_networkx_nodes(G, pos, nodelist=nodes_B_unexp, node_color='mistyrose', node_size=100, alpha=0.4, label='Type B (Stub)')
    
    plt.title(title, fontsize=16)
    plt.legend(scatterpoints=1, loc='upper left')
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(filename, format='jpg', dpi=150)
    plt.close()

def int_to_b64_char(n: int) -> str:
    if not (0 <= n <= 63):
        raise ValueError("Integer must be between 0 and 63")
    
    # Standard Base64 alphabet
    b64_alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
    return b64_alphabet[n]

def tuple_id_to_base64(tuple_id: tuple[int]) -> str:
    string = "".join(map(int_to_b64_char, tuple_id))
    return string

# --- Execution ---

if __name__ == "__main__":
    PARAMS = {
        'a_total': 2,
        'a_expand': 2,
        'b_total': 4,
        'b_expand': 1,
        'max_expansions': 1e6,
        'max_depth': 6,
        'dfs_steps': 4,
        'bfs_steps': 1
    }
    
    output_filename = "tree_expansion.jpg"
    print("Running Tree Expansion (Alternating Deque)...")
    tree, node_ids, node_expansion_order = expand_tree(**PARAMS)
    draw_and_save_tree(tree, output_filename, f"Tree Expansion: Alternating Deque ({PARAMS['dfs_steps']} DFS : {PARAMS['bfs_steps']} BFS)")
    print(f"Done! Saved '{output_filename}'.")

    node_order = list(node_ids.values())
    print(node_order)

    print(node_expansion_order)

    base64_expansion_order = [tuple_id_to_base64(tuple_id) for tuple_id in node_expansion_order]
    print(base64_expansion_order)
    print(f"Num expansions: {len(node_expansion_order)}")

    import pickle

    order_obj = {
        "params": PARAMS,
        "expansion_order_tuples": node_order,
        "expansion_order_base64": base64_expansion_order
    }

    with open("data/expansion_order.pkl", "wb") as f:
        pickle.dump(order_obj, f)
    