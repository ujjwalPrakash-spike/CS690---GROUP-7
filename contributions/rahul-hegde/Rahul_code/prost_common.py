"""PROST settings shared by the MERFISH and STARmap runs. Run on a CUDA GPU: CPU and GPU give
slightly different floats, which breaks exact reproducibility."""
import PROST
import scanpy as sc

SEED = 818  # PROST's default seed


def prepare(a, seed=SEED):
    """normalize_total + log1p, then PCA 20 (PROST's input). Raw counts stay in a.layers['counts']."""
    a = a.copy()
    a.layers["counts"] = a.X.copy()
    sc.pp.normalize_total(a); sc.pp.log1p(a)
    sc.pp.pca(a, n_comps=20, random_state=seed)
    return a


def run(a, n_clusters, k_neighbors, init="kmeans", seed=SEED):
    """One PROST run. post_processing=False: no label smoothing, so the raw PROST clusters are reported."""
    a = a.copy()
    PROST.setup_seed(seed)
    PROST.run_PNN(a, SEED=seed, init=init, n_clusters=n_clusters,
                  adj_mode="neighbour", k_neighbors=k_neighbors,
                  lr=0.1, tol=5e-3, max_epochs=100,
                  post_processing=False, cuda=True, key_added="PROST")
    return a.obs["clustering"].astype(int).astype(str)
