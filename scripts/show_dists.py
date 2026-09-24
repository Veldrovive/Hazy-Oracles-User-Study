import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta

def get_geometric_pmf(N, p):
    """Truncated Geometric: p determines the drop-off rate."""
    k = np.arange(1, N + 1)
    pmf = p * (1 - p)**(k - 1)
    return pmf / np.sum(pmf)  # Normalize for truncation

def get_zipf_pmf(N, s):
    """Zipfian (Power Law): s determines the heavy tail."""
    k = np.arange(1, N + 1)
    pmf = k**(-float(s))
    return pmf / np.sum(pmf)

def get_softmax_pmf(N, tau):
    """Softmax: tau (temperature) smooths out the distribution."""
    k = np.arange(1, N + 1)
    pmf = np.exp(-k / tau)
    return pmf / np.sum(pmf)

def get_beta_pmf(N, a, b):
    """
    Discretized Beta: alpha (a) and beta (b) control the curve shape.
    Using CDF differences ensures the discrete probabilities sum to 1.
    """
    edges = np.linspace(0, 1, N + 1)
    pmf = np.diff(beta.cdf(edges, a, b))
    return pmf

def render_distributions(N=50):
    """Plots all four distributions for visual comparison."""
    k = np.arange(1, N + 1)
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    
    # 1. Truncated Geometric
    p = 0.1
    axes[0, 0].bar(k, get_geometric_pmf(N, p), color='skyblue', edgecolor='black', linewidth=0.5)
    axes[0, 0].set_title(f'Truncated Geometric (p={p})')
    
    # 2. Zipfian
    s = 1.2
    axes[0, 1].bar(k, get_zipf_pmf(N, s), color='salmon', edgecolor='black', linewidth=0.5)
    axes[0, 1].set_title(f'Zipfian (s={s})')
    
    # 3. Softmax
    tau = 10.0
    axes[1, 0].bar(k, get_softmax_pmf(N, tau), color='lightgreen', edgecolor='black', linewidth=0.5)
    axes[1, 0].set_title(f'Softmax ($\\tau$={tau})')
    
    # 4. Discretized Beta
    a, b = 1.0, 5.0
    axes[1, 1].bar(k, get_beta_pmf(N, a, b), color='plum', edgecolor='black', linewidth=0.5)
    axes[1, 1].set_title(f'Discretized Beta ($\\alpha$={a}, $\\beta$={b})')
    
    for ax in axes.flat:
        ax.set_xlabel("List Index (Rank)")
        ax.set_ylabel("Probability")
        ax.set_xlim(0, N + 1)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        
    plt.tight_layout()
    plt.show()

# 1. Render the plots for a list of 50 items
render_distributions(N=400)

# 2. Example: How to sample a single item from the list using the Zipfian distribution
my_list = ["Item_" + str(i) for i in range(1, 51)]
probabilities = get_zipf_pmf(N=50, s=1.2)

# np.random.choice uses the probabilities array to pick one index
sampled_index = np.random.choice(np.arange(50), p=probabilities)
print(f"Sampled Item: {my_list[sampled_index]} at index {sampled_index}")