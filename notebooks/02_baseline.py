# %% [markdown]
# ### This notebook features a baseline XGBoost model.

# %%
import kagglehub
import pandas as pd
from pathlib import Path

from sklearn.metrics import classification_report
from xgboost import XGBClassifier

# %%
def load_raw_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    1. Fetch the eliptic dataset from kagglehub.
    2. Load the feature, edges, and classes CSVs into DataFrames.
    """
    path = kagglehub.dataset_download("ellipticco/elliptic-data-set")
    # print("Path to dataset files:", path)
    data_dir = Path(path) / "elliptic_bitcoin_dataset"

    features_path = data_dir / "elliptic_txs_features.csv"
    edges_path = data_dir / "elliptic_txs_edgelist.csv"
    classes_path = data_dir / "elliptic_txs_classes.csv"

    features = pd.read_csv(features_path, header=None)
    edges = pd.read_csv(edges_path)
    classes = pd.read_csv(classes_path)

    return features, edges, classes

# %%
def build_node_table(features: pd.DataFrame, classes: pd.DataFrame) -> pd.DataFrame:
    """
    Merge the features and classes table to create a node table with labels
    Column 0: Transaction id (txId)
    Column 1: time_step (1-49)
    Column 2-166: Remaining numeric features
    """
    
    # rename features
    features = features.copy()
    features.rename(columns={0: 'txId', 1: 'time_step'}, inplace=True)

    # Join with labels on transaction id
    nodes = features.merge(classes, on='txId', how="left")
    return nodes

# %%
def preprocess_data(nodes: pd.DataFrame) -> tuple(pd.DataFrame, pd.Series, pd.Series):
    """
    Prepare for supervised learning:
    Drop unlabeled transactions, split features and label, etc.
    Returns X (features), y (labels), and time_step (for time-based splitting)
    """
    # Keep only labelled transactions
    labelled = nodes[nodes["class"] != "unknown"].copy()

    # Map string labels to ints for computation
    label_map = {"1" : 1, "2" : 0} # 1 = illicit, 0 = licit
    y = labelled["class"].map(label_map)
    # Guard: if mapping failed for any row, drop it (should be rare / none)
    keep = y.notna()
    labelled = labelled[keep].copy()
    y = y[keep].astype(int)

    # Save feature columns in X. Feature columns are all columns with integer labels (non-string)
    features = [c for c in labelled.columns if isinstance(c, int)]
    X = labelled[features].copy()

    # Keep time_step for time-based splitting
    time_step = labelled["time_step"].copy()

    return X, y, time_step


# %%
def train_xgboost(X: pd.DataFrame, y: pd.Series, time_step: pd.Series):
    """
    Train simple XGBoost baseline with time-based split and print evaluation.
    
    Time-based splits:
    - Train: time_step <= 34
    - Test: time_step >= 35
    
    Returns:
        model: Trained XGBoost classifier
    """

    # Paper split: Train = timesteps 1–34, Test = timesteps 35–49
    train_mask = (time_step <= 34)
    test_mask = (time_step >= 35)

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Train set size: {len(X_train)} (time_step <= 34)")
    print(f"Test set size: {len(X_test)} (time_step >= 35)")

    # Sanity checks to avoid reporting the wrong subset
    assert len(X_train) == train_mask.sum()
    assert len(X_test) == test_mask.sum()
    assert y_train.notna().all() and y_test.notna().all()

    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        n_estimators=50,
        max_depth=100,
        random_state=15,
        n_jobs=-1,
        tree_method="hist",
    )

    model.fit(X_train, y_train)

    # Evaluate on test set
    y_test_pred = model.predict(X_test)
    print("\nXGBoost Baseline Evaluation - Paper Temporal Test (time_step >= 35)")
    print(classification_report(y_test, y_test_pred, target_names=["licit (0)", "illicit (1)"]))
    
    return model

# %%
def main():
    features, edges, classes = load_raw_data()

    nodes = build_node_table(features, classes)

    print("\nClass distribution (including 'unknown'):")
    print(nodes["class"].value_counts())

    X, y, time_step = preprocess_data(nodes)

    print("\nLabelled samples:", len(y))
    print("Class distribution (labelled only):")
    print(y.value_counts(normalize=True))


    model = train_xgboost(X, y, time_step)
    return model

model = main()

# %%
# Save the trained model to the project directory
import os

# Create models directory if it doesn't exist
models_dir = Path("../models")
models_dir.mkdir(exist_ok=True)

# Save the model using the booster's save_model method

model_path = models_dir / "xgboost_baseline.json"
model.get_booster().save_model(str(model_path))
# print(f"Model saved to: {model_path.absolute()}")

# %% [markdown]
# ### A supervised XGBoost baseline achieves high performance on the Elliptic dataset, which indicates that the engineered tabular features already capture sufficient information about a transaction. However, this baseline treats transactions as independent, ignores unlabeled nodes, and relies on static features, making it poorly suited for a real-time inference system. We therefore continue with a GNN not to maximize metrics, but to model transaction risk as a property of a graph, leveraging the unlabeled structure and enabling real-time (realistic) streaming detection.
