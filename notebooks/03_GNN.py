import kagglehub
import pandas as pd
import numpy as np
from pathlib import Path
import torch
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from sklearn.preprocessing import StandardScaler
import torch.nn.functional as F
from torch_geometric.nn import GCNConv
from sklearn.metrics import classification_report

def load_raw_data() -> tuple[features: pd.DataFrame, edges: pd.DataFrame, classes: pd.DataFrame]:
    # load data into dataframes
    path = kagglehub.dataset_download("ellipticco/elliptic-data-set")
    data_dir = Path(path) / "elliptic_bitcoin_dataset"

    features_path = data_dir / "elliptic_txs_features.csv"
    edges_path    = data_dir / "elliptic_txs_edgelist.csv"
    classes_path  = data_dir / "elliptic_txs_classes.csv"

    # Create pandas dataframes
    features = pd.read_csv(features_path, header=None)
    edges    = pd.read_csv(edges_path)
    classes  = pd.read_csv(classes_path)

    return features, edges, classes

def build_node_table(features: pd.DataFrame, classes: pd.Dataframe) -> pd.DataFrame:
    """
    Merge the features and classes table to create a node table with labels
    Column 0: Transaction id (txId)
    Column 1: time_step (1-49)
    Column 2-166: Remaining numeric features
    """
    
    # rename features
    features = features.copy()
    features.rename(columns={0: 'txId', 1: 'time_step'}, inplace=True)

    # Build labels
    label_map = {"1" : 1, "2" : 0} # 1 = illicit, 0 = licit
    classes["label"] = classes["class"].map(label_map)

    # Join with labels on transaction id
    nodes = features.merge(classes[["txId", "label"]], on='txId', how="left")
    nodes["label"] = nodes["label"].fillna(-1).astype(int)
    return nodes

def prepare_data(nodes):
    """
    Convert from pandas dataframes to tensors for ML and create an idx -> txID mapping for PyTorch Geometric GNN training
    """
    tx_ids = nodes["txId"].values
    id2idx = {}
    for idx, txId in enumerate(tx_ids):
        id2idx[txId] = idx
    feature_cols = [c for c in nodes.columns if c not in ["txId", "time_step", "label"]]

    x = torch.tensor(nodes[feature_cols].values, dtype=torch.float)

    y = torch.tensor(nodes["label"].values, dtype=torch.long)

    return x,y, id2idx

def build_edge_index(edges, id2idx):
    """
    Given the raw edge list and node index mapping, create a tensor representing edges in PyTorch compatible format
    """
    src_idx = []
    dest_idx = []

    for _, row in edges.iterrows():
        txId1 = row["txId1"]
        txId2 = row["txId2"]

        idx1 = id2idx.get(txId1, -1)
        idx2 = id2idx.get(txId2, -1)

        if idx1 != -1 and idx2 != -1:
            src_idx.append(idx1)
            dest_idx.append(idx2)

            # undirected
            src_idx.append(idx2)
            dest_idx.append(idx1)

    edge_index = torch.tensor([src_idx, dest_idx], dtype=torch.long)

    return edge_index

def build_masks(nodes: pd.DataFrame, y: torch.tensor):
    """
    Construct boolean masks based on the transaction time and label so GNN is trained 
    on early timestep nodes, validated on later timestep nodes, and tested on latest/future nodes. 
    Unlabeled nodes still participate in message parsing, so this is a semi-supervised approach.
    """
    time_step = nodes["time_step"].values
    labeled = (y != -1).numpy()

    train_mask = torch.tensor((time_step <= 34) & labeled, dtype=torch.bool)
    val_mask = torch.tensor((time_step >= 35) & (time_step <= 41) & labeled, dtype=torch.bool)
    test_mask = torch.tensor((time_step >= 42) & labeled, dtype=torch.bool)

    return train_mask, val_mask, test_mask

def build_graph_data(x, y, edge_index, train_mask, val_mask, test_mask):
    """
    Package everything into a PyTorch Geometric Data Object for training
    """
    data = Data(x=x, edge_index=edge_index, y=y)
    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask

    return data

class GCN(torch.nn.Module):
    """
    Model definition
    """
    def __init__(self, in_dim, hidden_dim = 64):
        super().__init__()

        self.conv1 = GCNConv(in_dim, hidden_dim)

        self.conv2 = GCNConv(hidden_dim, 2)
    
    def forward(self, x, edge_index):
        x = self.conv1(x, edge_index)

        x = F.relu(x)

        x = self.conv2(x, edge_index)

        return x

def train(data):
    model = GCN(in_dim = data.x.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr =0.01, weight_decay=5e-4)

    # Illicit gets more loss weight; account for class imbalance
    labels =data.y[data.train_mask]
    class_counts = torch.bincount(labels)
    class_weights = 1.0 / class_counts.float()
    class_weights = class_weights / class_weights.sum()

    out = model(data.x, data.edge_index)

    for epoch in range(1, 201):
        model.train()
        optimizer.zero_grad()
        out = model(data.x, data.edge_index)

        

        loss = F.cross_entropy(
            out[data.train_mask],
            data.y[data.train_mask],
            weight=class_weights
        )

        loss.backward()
        optimizer.step()

        # Simple logging
        if epoch % 20 == 0:
            print(f"Epoch {epoch}, Loss: {loss.item():.4f}")
    
    return model

def evaluate(model, data):
    model.eval()
    
    with torch.no_grad():
        out = model(data.x, data.edge_index)
        preds = out.argmax(dim = 1)

        y_true = data.y[data.test_mask].cpu().numpy()
        y_pred = preds[data.test_mask].cpu().numpy()

    print(classification_report(
        y_true,
        y_pred,
        target_names=["licit", "illicit"]
    )) 

def main():
    print("hey")
    features, edges, classes = load_raw_data()
    nodes = build_node_table(features, classes)

    x, y, id2idx = prepare_data(nodes)
    edge_index = build_edge_index(edges, id2idx)

    train_mask, val_mask, test_mask = build_masks(nodes, y)
    data = build_graph_data(x, y, edge_index, train_mask, val_mask, test_mask)

    model = train(data)
    evaluate(model, data)

if __name__ == "__main__":
    main()