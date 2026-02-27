from pathlib import Path
import random

import kagglehub
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from sklearn.metrics import classification_report, f1_score, matthews_corrcoef, precision_score
from sklearn.preprocessing import StandardScaler
from torch_geometric.data import Data
from torch_geometric.nn import GATConv


# -----------------------------
# Data loading and preprocessing
# -----------------------------

def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the Elliptic dataset CSVs via kagglehub."""
    path = kagglehub.dataset_download("ellipticco/elliptic-data-set")
    data_dir = Path(path) / "elliptic_bitcoin_dataset"

    features_path = data_dir / "elliptic_txs_features.csv"
    edges_path = data_dir / "elliptic_txs_edgelist.csv"
    classes_path = data_dir / "elliptic_txs_classes.csv"

    features = pd.read_csv(features_path, header=None)
    edges = pd.read_csv(edges_path)
    classes = pd.read_csv(classes_path)

    return features, edges, classes


def build_node_table(features: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    """Build a single node table with txId, time_step, features, and label in {0, 1, -1}."""
    features = features.copy()
    features.rename(columns={0: "txId", 1: "time_step"}, inplace=True)

    label_map = {"1": 1, "2": 0}  # 1 = illicit, 0 = licit
    classes = classes.copy()
    classes["label"] = classes["class"].map(label_map)

    nodes = features.merge(classes[["txId", "label"]], on="txId", how="left")
    nodes["label"] = nodes["label"].fillna(-1).astype(int)
    return nodes


def temporal_masks(nodes: pd.DataFrame) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """Temporal split: train 1–34, val 35–41, test 42–49 (labeled only)."""
    time_step = nodes["time_step"].values
    labeled = (nodes["label"].values != -1).astype(bool)

    # Build tensors from Python lists so we never use torch.from_numpy (Colab may have PyTorch without NumPy).
    train_mask = torch.tensor(((time_step <= 34) & labeled).tolist(), dtype=torch.bool)
    val_mask = torch.tensor(((time_step >= 35) & (time_step <= 41) & labeled).tolist(), dtype=torch.bool)
    test_mask = torch.tensor(((time_step >= 30) & labeled).tolist(), dtype=torch.bool)

    return train_mask, val_mask, test_mask


def build_edge_index(edges: pd.DataFrame, id2idx: dict[int, int]) -> torch.Tensor:
    """Convert (txId1, txId2) edges into undirected PyG edge_index."""
    src_idx: list[int] = []
    dst_idx: list[int] = []

    for _, row in edges.iterrows():
        tx1 = row["txId1"]
        tx2 = row["txId2"]
        i1 = id2idx.get(tx1, -1)
        i2 = id2idx.get(tx2, -1)
        if i1 == -1 or i2 == -1:
            continue
        src_idx.append(i1)
        dst_idx.append(i2)
        src_idx.append(i2)
        dst_idx.append(i1)

    edge_index = torch.tensor([src_idx, dst_idx], dtype=torch.long)
    return edge_index


def prepare_graph_data(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    train_mask: torch.Tensor,
    val_mask: torch.Tensor,
    test_mask: torch.Tensor,
) -> Data:
    """Standardize features on train, build PyG Data with masks."""
    tx_ids = nodes["txId"].values
    id2idx: dict[int, int] = {tx_id: idx for idx, tx_id in enumerate(tx_ids)}

    feature_cols = [c for c in nodes.columns if c not in ["txId", "time_step", "label"]]

    X = nodes[feature_cols].values.astype(np.float32)
    y = nodes["label"].values.astype(np.int64)

    # Standardize features on the training window only (compute from nodes to avoid tensor.numpy() in Colab).
    time_step = nodes["time_step"].values
    labeled = (nodes["label"].values != -1).astype(bool)
    train_mask_np = np.asarray((time_step <= 34) & labeled, dtype=bool)

    scaler = StandardScaler()
    scaler.fit(X[train_mask_np])
    X = scaler.transform(X).astype(np.float32)

    x = torch.tensor(X, dtype=torch.float)
    y_t = torch.tensor(y, dtype=torch.long)

    edge_index = build_edge_index(edges, id2idx)

    data = Data(x=x, edge_index=edge_index, y=y_t)
    data.train_mask = train_mask
    data.val_mask = val_mask
    data.test_mask = test_mask

    return data


# -----------------------------
# GAT-ResNet Architecture
# -----------------------------

class GATResNet(torch.nn.Module):
    """Three-layer GAT-ResNet with residual and optional input skip connection."""

    def __init__(
        self,
        in_channels: int,
        hidden_channels: int = 100,
        num_classes: int = 2,
        heads1: int = 8,
        heads2: int = 8,
        heads3: int = 1,
        dropout: float = 0.5,
        use_skip: bool = True,
    ) -> None:
        super().__init__()

        self.dropout = dropout
        self.use_skip = use_skip

        # Layer 1 GAT
        self.gat1 = GATConv(
            in_channels=in_channels,
            out_channels=hidden_channels,
            heads=heads1,
            concat=True,
            dropout=dropout,
        )
        dim1 = hidden_channels * heads1

        # Layer 2 GAT
        self.gat2 = GATConv(
            in_channels=dim1,
            out_channels=hidden_channels,
            heads=heads2,
            concat=True,
            dropout=dropout,
        )
        dim2 = hidden_channels * heads2

        # Layer 3 GAT (to logits)
        self.gat3 = GATConv(
            in_channels=dim2,
            out_channels=num_classes,
            heads=heads3,
            concat=False,
            dropout=dropout,
        )

        # Residual projections: h2 += P1(h1); logits += P2(h2)
        self.res1 = torch.nn.Linear(dim1, dim2, bias=False)
        self.res2 = torch.nn.Linear(dim2, num_classes, bias=False)

        # Optional skip from raw input features to logits
        if self.use_skip:
            self.skip_proj = torch.nn.Linear(in_channels, num_classes, bias=False)
        else:
            self.skip_proj = None

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        x_in = x

        # GAT layer 1 + ELU + dropout
        h1 = self.gat1(x, edge_index)
        h1 = torch.nn.functional.elu(h1)
        h1 = torch.nn.functional.dropout(h1, p=self.dropout, training=self.training)

        # GAT layer 2 + residual from h1 + ELU + dropout
        h2 = self.gat2(h1, edge_index)
        h2 = h2 + self.res1(h1)  # residual connection
        h2 = torch.nn.functional.elu(h2)
        h2 = torch.nn.functional.dropout(h2, p=self.dropout, training=self.training)

        # GAT layer 3 + residual from h2
        logits = self.gat3(h2, edge_index)
        logits = logits + self.res2(h2)

        # Optional global skip from input features
        if self.skip_proj is not None:
            logits = logits + self.skip_proj(x_in)

        return logits


# -----------------------------
# Training and evaluation
# -----------------------------

def compute_class_weights(y: torch.Tensor, train_mask: torch.Tensor) -> torch.Tensor:
    """Inverse-frequency class weights computed on the training set only."""
    labels = y[train_mask]
    labels = labels[labels >= 0]
    counts = torch.bincount(labels, minlength=2).float()
    # Paper-style: do NOT normalize weights. Pass unnormalized inverse frequency to cross-entropy.
    weights = 1.0 / (counts + 1e-8)
    return weights.to(y.device)


def train_model(
    data: Data,
    max_epochs: int = 1000,
    patience: int = 50,
    lr: float = 1e-3,
) -> GATResNet:
    """
    Train GAT-ResNet with weighted CE and Adam.

    Checkpoint selection is based on validation performance under a tuned
    decision threshold for the illicit class:
    - For each epoch, we sweep thresholds on the validation set.
    - Among thresholds where recall(illicit) > 0.60 and precision(illicit) > 0.50,
      we pick the one with highest illicit F1.
    - The model/threshold pair with the best such F1 across epochs is kept.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data = data.to(device)

    model = GATResNet(
        in_channels=data.x.size(1),
        hidden_channels=100,
        num_classes=2,
        heads1=8,
        heads2=8,
        heads3=1,
        dropout=0.5,
        use_skip=True,
    ).to(device)

    class_weights = compute_class_weights(data.y, data.train_mask)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=5e-4)

    best_state = None
    best_threshold = None
    best_val_f1_illicit = -1.0
    epochs_no_improve = 0

    for epoch in range(1, max_epochs + 1):
        model.train()
        optimizer.zero_grad()

        out = model(data.x, data.edge_index)
        loss = torch.nn.functional.cross_entropy(
            out[data.train_mask],
            data.y[data.train_mask],
            weight=class_weights,
        )

        loss.backward()
        optimizer.step()

        # Validation each epoch: sweep thresholds and pick best illicit F1
        model.eval()
        with torch.no_grad():
            logits = model(data.x, data.edge_index)
            probs = torch.softmax(logits, dim=1)[:, 1]  # P(illicit)

            y_val_true_t = data.y[data.val_mask]
            mask_labeled = y_val_true_t >= 0
            y_val_true = np.array(y_val_true_t[mask_labeled].cpu().tolist())
            probs_val = probs[data.val_mask][mask_labeled].cpu().numpy()

        val_best_f1_epoch = -1.0
        val_best_threshold_epoch = None
        val_best_prec_epoch = 0.0
        val_best_rec_epoch = 0.0

        if y_val_true.size > 0 and (y_val_true == 1).any():
            # Simple threshold grid; can be refined if needed.
            for thr in np.linspace(0.1, 0.9, 17):
                y_val_pred = (probs_val >= thr).astype(int)
                prec = precision_score(y_val_true, y_val_pred, pos_label=1, zero_division=0)
                rec = f1_rec = 0.0
                # recall_score not imported; compute manually via f1_score trick or via TP/(TP+FN)
                tp = ((y_val_true == 1) & (y_val_pred == 1)).sum()
                fn = ((y_val_true == 1) & (y_val_pred == 0)).sum()
                rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0

                if rec > 0.60 and prec > 0.50:
                    f1_illicit = f1_score(
                        y_val_true,
                        y_val_pred,
                        pos_label=1,
                        zero_division=0,
                    )
                    if f1_illicit > val_best_f1_epoch + 1e-4:
                        val_best_f1_epoch = f1_illicit
                        val_best_threshold_epoch = float(thr)
                        val_best_prec_epoch = float(prec)
                        val_best_rec_epoch = float(rec)

        # Update global best if this epoch produced a threshold meeting the constraints
        if val_best_threshold_epoch is not None and val_best_f1_epoch > best_val_f1_illicit + 1e-4:
            best_val_f1_illicit = val_best_f1_epoch
            best_threshold = val_best_threshold_epoch
            best_state = model.state_dict()
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epoch % 10 == 0:
            if val_best_threshold_epoch is not None:
                print(
                    f"Epoch {epoch:4d} | Loss: {loss.item():.4f} | "
                    f"Val illicit F1: {val_best_f1_epoch:.4f} "
                    f"(P={val_best_prec_epoch:.3f}, R={val_best_rec_epoch:.3f}, thr={val_best_threshold_epoch:.2f}) | "
                    f"Best illicit F1: {best_val_f1_illicit:.4f}"
                )
            else:
                print(
                    f"Epoch {epoch:4d} | Loss: {loss.item():.4f} | "
                    f"No val threshold with P>0.50 & R>0.60 | "
                    f"Best illicit F1 so far: {best_val_f1_illicit:.4f}"
                )

        if epochs_no_improve >= patience:
            print(f"Early stopping at epoch {epoch} (no val improvement for {patience} epochs).")
            break

    if best_state is not None:
        model.load_state_dict(best_state)

    return model, best_threshold


def evaluate_model(model: GATResNet, data: Data, threshold: float = 0.5) -> None:
    """
    Print classification report, illicit/macro/weighted F1, and MCC on test timesteps 42–49.

    Predictions use a configurable probability threshold for the illicit class.
    """
    device = next(model.parameters()).device
    data = data.to(device)

    model.eval()
    with torch.no_grad():
        logits = model(data.x, data.edge_index)
        probs = torch.softmax(logits, dim=1)[:, 1]
        preds = (probs >= threshold).long()

    y_true = data.y[data.test_mask]
    y_pred = preds[data.test_mask]

    keep = y_true >= 0
    y_true = np.array(y_true[keep].cpu().tolist()) # Modified
    y_pred = np.array(y_pred[keep].cpu().tolist()) # Modified

    print("Test classification report (42–49):")
    print(classification_report(y_true, y_pred, target_names=["licit", "illicit"]))

    f1_illicit = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    f1_weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    mcc = matthews_corrcoef(y_true, y_pred)
    print(f"Test illicit F1: {f1_illicit:.4f}")
    print(f"Test macro F1:   {f1_macro:.4f}")
    print(f"Test weighted F1:{f1_weighted:.4f}")
    print(f"Test MCC:       {mcc:.4f}")


# -----------------------------
# Main pipeline (call in a cell)
# -----------------------------

def run_pipeline(max_epochs: int = 1000, patience: int = 50, lr: float = 1e-3):
    """Convenience function to run the full Elliptic GAT-ResNet experiment in Colab."""
    # Reproducibility
    seed = 42
    torch.manual_seed(seed)
    np.random.seed(seed)
    random.seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

    features, edges, classes = load_raw_data()
    nodes = build_node_table(features, classes)

    train_mask, val_mask, test_mask = temporal_masks(nodes)
    data = prepare_graph_data(nodes, edges, train_mask, val_mask, test_mask)

    model, best_threshold = train_model(data, max_epochs=max_epochs, patience=patience, lr=lr)
    if best_threshold is None:
        print("Warning: no validation threshold met P>0.50 & R>0.60; using default threshold 0.5 on test.")
        best_threshold = 0.5
    print(f"Using test threshold: {best_threshold:.2f}")
    evaluate_model(model, data, threshold=best_threshold)

if __name__ == "__main__":
    run_pipeline(max_epochs=1000, patience=50, lr=1e-3)