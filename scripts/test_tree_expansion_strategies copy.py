import random
import uuid
from collections import deque
import igraph as ig
import matplotlib.pyplot as plt
import networkx as nx

def add_single_child(G, parent_id, a_total, a_expand, b_total, b_expand):
    """
    Adds a single child to the parent node.
    Returns the child_id and a boolean indicating whether the child should be added to the frontier.
    """
    node_data = G.nodes[parent_id]
    parent_type = node_data['type']
    parent_depth = node_data['depth']
    
    total_limit = a_total if parent_type == 'A' else b_total
    expand_limit = a_expand if parent_type == 'A' else b_expand
    
    # Initialize expansion tracking for this node if not present
    if 'num_children' not in node_data:
        node_data['num_children'] = 0
        node_data['expandable_indices'] = set(random.sample(range(total_limit), min(expand_limit, total_limit)))
        node_data['num_expanded'] = 0

    num_children = node_data['num_children']
    
    # Create the single new child
    child_type = 'B' if parent_type == 'A' else 'A'
    child_id = str(uuid.uuid4())
    
    G.add_node(child_id, type=child_type, depth=parent_depth + 1, expanded=False)
    G.add_edge(parent_id, child_id)
    
    # Determine if this child goes on the frontier
    goes_to_frontier = num_children in node_data['expandable_indices']
    
    # Update parent state
    node_data['num_children'] += 1
    node_data['expanded'] = True # Mark as having at least one child expanded
    if goes_to_frontier:
        node_data['num_expanded'] += 1
        
    return child_id, goes_to_frontier

def expand_tree(max_expansions=40, depth_limit=5, dfs_steps=5, bfs_steps=1, 
                a_total=5, a_expand=2, b_total=4, b_expand=1):
    """
    Simulates tree expansion using an alternating deque strategy (DFS/BFS hybrid),
    with an atomic unit of adding a single child at a time.
    """
    G = nx.DiGraph()
    root_id = "ROOT"
    G.add_node(root_id, type='A', depth=0, expanded=False)
    
    frontier = deque([root_id])
    expansions = 0
    
    while frontier and expansions < max_expansions:
        # Phase 1: DFS (pop right)
        steps_taken = 0
        while steps_taken < dfs_steps and frontier and expansions < max_expansions:
            current = frontier.pop() # Pop right
            node_data = G.nodes[current]
            
            total_limit = a_total if node_data['type'] == 'A' else b_total
            num_children = node_data.get('num_children', 0)
            
            # Check if node is dead
            if num_children >= total_limit or node_data['depth'] >= depth_limit:
                continue
                
            # It's alive, add a single child
            child_id, goes_to_frontier = add_single_child(G, current, a_total, a_expand, b_total, b_expand)
            expansions += 1
            steps_taken += 1
            
            # Put parent back on frontier if it can still produce more children
            if node_data['num_children'] < total_limit and node_data['depth'] < depth_limit:
                frontier.append(current) # Add to right
                
            # Add child to frontier if it's selected to be expandable
            if goes_to_frontier:
                frontier.append(child_id) # Add to right
                
        # Phase 2: BFS (pop left)
        steps_taken = 0
        while steps_taken < bfs_steps and frontier and expansions < max_expansions:
            current = frontier.popleft() # Pop left
            node_data = G.nodes[current]
            
            total_limit = a_total if node_data['type'] == 'A' else b_total
            num_children = node_data.get('num_children', 0)
            
            # Check if node is dead
            if num_children >= total_limit or node_data['depth'] >= depth_limit:
                continue
                
            # It's alive, add a single child
            child_id, goes_to_frontier = add_single_child(G, current, a_total, a_expand, b_total, b_expand)
            expansions += 1
            steps_taken += 1
            
            # Put parent back on frontier if it can still produce more children
            if node_data['num_children'] < total_limit and node_data['depth'] < depth_limit:
                frontier.append(current) # Add to right (back of the line for BFS)
                
            # Add child to frontier if it's selected to be expandable
            if goes_to_frontier:
                frontier.append(child_id) # Add to right

    return G

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

# --- Execution ---

if __name__ == "__main__":
    PARAMS = {
        'a_total': 2,
        'a_expand': 2,
        'b_total': 4,
        'b_expand': 1,
        'max_expansions': 40,
        'depth_limit': 4,
        'dfs_steps': 5,
        'bfs_steps': 1
    }
    
    output_filename = "tree_expansion.jpg"
    print("Running Tree Expansion (Alternating Deque)...")
    tree = expand_tree(**PARAMS)
    draw_and_save_tree(tree, output_filename, f"Tree Expansion: Alternating Deque ({PARAMS['dfs_steps']} DFS : {PARAMS['bfs_steps']} BFS, max depth {PARAMS['depth_limit']})")
    print(f"Done! Saved '{output_filename}'.")