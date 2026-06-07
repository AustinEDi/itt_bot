import numpy as np
import joblib
import os

class DecisionTree:
    def __init__(self, max_depth=5, min_samples_split=5):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree = None

    def _gini(self, y):
        _, counts = np.unique(y, return_counts=True)
        probs = counts / len(y)
        return 1 - np.sum(probs ** 2)

    def _best_split(self, X, y):
        best_gini = 1.0
        best_feat, best_val = None, None
        n = len(y)
        if n < self.min_samples_split:
            return None, None
        for feat in range(X.shape[1]):
            vals = np.unique(X[:, feat])
            for val in vals:
                left = y[X[:, feat] <= val]
                right = y[X[:, feat] > val]
                if len(left) == 0 or len(right) == 0:
                    continue
                gini = (len(left)/n)*self._gini(left) + (len(right)/n)*self._gini(right)
                if gini < best_gini:
                    best_gini = gini
                    best_feat = feat
                    best_val = val
        return best_feat, best_val

    def _build(self, X, y, depth):
        if depth >= self.max_depth or len(np.unique(y)) == 1:
            return np.mean(y)
        feat, val = self._best_split(X, y)
        if feat is None:
            return np.mean(y)
        left_mask = X[:, feat] <= val
        left = self._build(X[left_mask], y[left_mask], depth+1)
        right = self._build(X[~left_mask], y[~left_mask], depth+1)
        return (feat, val, left, right)

    def fit(self, X, y):
        self.tree = self._build(X, y, 0)

    def _predict_one(self, x, node):
        if not isinstance(node, tuple):
            return node
        feat, val, left, right = node
        if x[feat] <= val:
            return self._predict_one(x, left)
        else:
            return self._predict_one(x, right)

    def predict_proba(self, X):
        probas = np.array([self._predict_one(x, self.tree) for x in X])
        return np.column_stack([1 - probas, probas])

class RandomForest:
    def __init__(self, n_estimators=50, max_depth=5, min_samples_split=5, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.rng = np.random.RandomState(random_state)
        self.trees = []

    def fit(self, X, y):
        n = X.shape[0]
        for _ in range(self.n_estimators):
            idx = self.rng.choice(n, size=n, replace=True)
            tree = DecisionTree(max_depth=self.max_depth, min_samples_split=self.min_samples_split)
            tree.fit(X[idx], y[idx])
            self.trees.append(tree)

    def predict_proba(self, X):
        all_proba = np.array([tree.predict_proba(X) for tree in self.trees])
        return np.mean(all_proba, axis=0)

class AIAnalyst:
    def __init__(self, model_path='model.pkl'):
        self.model_path = model_path
        self.scaler_mean = None
        self.scaler_std = None
        self.features = ['profile_bullish','profile_bearish','sweep','absorption',
                         'choch_bull','choch_bear','displacement','fvg_distance']
        if os.path.exists(model_path):
            data = joblib.load(model_path)
            self.model = data['model']
            self.scaler_mean = data['scaler_mean']
            self.scaler_std = data['scaler_std']
        else:
            self.model = RandomForest(n_estimators=50, max_depth=5, min_samples_split=5)

    def _scale(self, X):
        X = np.array(X, dtype=np.float64)
        if self.scaler_mean is not None and self.scaler_std is not None:
            return (X - self.scaler_mean) / (self.scaler_std + 1e-8)
        return X

    def predict_proba(self, feat_dict):
        vec = [feat_dict.get(f, 0) for f in self.features]
        X = np.array(vec).reshape(1, -1)
        X = self._scale(X)
        proba = self.model.predict_proba(X)[0, 1]
        return float(proba)

    def update_model(self, trades_df):
        if len(trades_df) < 10:
            return
        X = trades_df[self.features].fillna(0).values.astype(np.float64)
        y = trades_df['result'].values.astype(np.float64)
        self.scaler_mean = X.mean(axis=0)
        self.scaler_std = X.std(axis=0)
        X_scaled = (X - self.scaler_mean) / (self.scaler_std + 1e-8)
        self.model = RandomForest(n_estimators=50, max_depth=5, min_samples_split=5)
        self.model.fit(X_scaled, y)
        joblib.dump({
            'model': self.model,
            'scaler_mean': self.scaler_mean,
            'scaler_std': self.scaler_std
        }, self.model_path)
