#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq


# Publication-oriented style
plt.rcParams.update(
    {
        "figure.dpi": 140,
        "savefig.dpi": 320,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "font.family": "DejaVu Serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "legend.fontsize": 9,
    }
)

COLORS = {
    "value": "#2A9D8F",
    "adv": "#E76F51",
    "indicator": "#264653",
    "intervention": "#F4A261",
    "success": "#1b9e77",
    "failure": "#d95f02",
}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def moving_avg(x: np.ndarray, k: int) -> np.ndarray:
    if k <= 1:
        return x.copy()
    kernel = np.ones(k, dtype=np.float64) / float(k)
    return np.convolve(x, kernel, mode="same")


def normalize_episode_series(values: np.ndarray, target_len: int = 200) -> np.ndarray:
    if values.size == 0:
        return np.zeros(target_len, dtype=np.float32)
    if values.size == 1:
        return np.full(target_len, float(values[0]), dtype=np.float32)
    x_old = np.linspace(0.0, 1.0, values.size)
    x_new = np.linspace(0.0, 1.0, target_len)
    return np.interp(x_new, x_old, values).astype(np.float32)


def load_data(dataset_root: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    data_file = dataset_root / "data" / "chunk-000" / "file-000.parquet"
    ep_file = dataset_root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"

    cols = [
        "index",
        "episode_index",
        "frame_index",
        "timestamp",
        "task_index",
        "complementary_info.value",
        "complementary_info.advantage",
        "complementary_info.acp_indicator",
        "complementary_info.is_intervention",
        "action",
        "observation.state",
    ]
    table = pq.read_table(data_file, columns=cols)
    df = table.to_pandas()
    df = df.rename(
        columns={
            "complementary_info.value": "value",
            "complementary_info.advantage": "advantage",
            "complementary_info.acp_indicator": "acp_indicator",
            "complementary_info.is_intervention": "is_intervention",
        }
    )
    df["acp_indicator"] = df["acp_indicator"].astype(np.int64)
    df["is_intervention"] = (df["is_intervention"].astype(np.float32) > 0.5).astype(np.int64)

    def l2_norm(arr: Iterable[float]) -> float:
        a = np.asarray(arr, dtype=np.float32)
        return float(np.linalg.norm(a))

    df["action_norm"] = df["action"].apply(l2_norm)
    df["state_norm"] = df["observation.state"].apply(l2_norm)
    df = df.drop(columns=["action", "observation.state"]).sort_values(["episode_index", "frame_index"])

    ep_cols = ["episode_index", "length", "episode_success", "dataset_from_index", "dataset_to_index"]
    ep_df = pq.read_table(ep_file, columns=ep_cols).to_pandas()
    ep_df["success"] = (ep_df["episode_success"].astype(str).str.lower() == "success").astype(np.int64)

    df = df.merge(ep_df[["episode_index", "success", "length"]], on="episode_index", how="left")
    return df, ep_df


def build_episode_stats(df: pd.DataFrame) -> pd.DataFrame:
    stats = (
        df.groupby("episode_index", as_index=False)
        .agg(
            frames=("index", "count"),
            success=("success", "max"),
            mean_value=("value", "mean"),
            std_value=("value", "std"),
            mean_adv=("advantage", "mean"),
            std_adv=("advantage", "std"),
            acp_pos_ratio=("acp_indicator", "mean"),
            intervention_ratio=("is_intervention", "mean"),
            mean_action_norm=("action_norm", "mean"),
            mean_state_norm=("state_norm", "mean"),
            last_value=("value", "last"),
            last_adv=("advantage", "last"),
        )
        .sort_values("episode_index")
    )
    stats["quality_score"] = (
        stats["mean_value"]
        + 0.45 * stats["mean_adv"]
        - 0.35 * stats["intervention_ratio"]
        - 0.15 * stats["acp_pos_ratio"]
    )
    return stats


def plot_overview(stats: pd.DataFrame, out: Path) -> None:
    n_eps = len(stats)
    success = int(stats["success"].sum())
    failure = n_eps - success

    fig, axs = plt.subplots(2, 2, figsize=(12, 8))
    axs = axs.ravel()

    axs[0].bar(["success", "failure"], [success, failure], color=[COLORS["success"], COLORS["failure"]])
    axs[0].set_title("Episode Outcome Count")
    axs[0].set_ylabel("episodes")

    axs[1].hist(stats["frames"] / 30.0, bins=16, color="#4C78A8", alpha=0.9)
    axs[1].set_title("Episode Duration Distribution")
    axs[1].set_xlabel("seconds")

    axs[2].scatter(
        stats["intervention_ratio"],
        stats["mean_value"],
        c=stats["success"].map({1: COLORS["success"], 0: COLORS["failure"]}),
        alpha=0.9,
        s=35,
    )
    axs[2].set_title("Mean Value vs Intervention Ratio")
    axs[2].set_xlabel("intervention ratio")
    axs[2].set_ylabel("mean value")

    axs[3].scatter(
        stats["acp_pos_ratio"],
        stats["intervention_ratio"],
        c=stats["quality_score"],
        cmap="viridis",
        s=40,
    )
    axs[3].set_title("ACP Positive Ratio vs Intervention Ratio")
    axs[3].set_xlabel("acp positive ratio")
    axs[3].set_ylabel("intervention ratio")

    fig.suptitle("Dataset Overview (Frame/episode-level)", y=1.02, fontsize=14)
    fig.tight_layout()
    fig.savefig(out / "fig01_dataset_overview.png")
    plt.close(fig)


def plot_distributions(df: pd.DataFrame, stats: pd.DataFrame, out: Path) -> None:
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))

    for success_flag, label, color in [(1, "success", COLORS["success"]), (0, "failure", COLORS["failure"])]:
        vals = df.loc[df["success"] == success_flag, "value"].to_numpy()
        axs[0, 0].hist(vals, bins=60, alpha=0.55, density=True, label=label, color=color)
    axs[0, 0].set_title("Value Distribution by Episode Outcome")
    axs[0, 0].set_xlabel("value")
    axs[0, 0].set_ylabel("density")
    axs[0, 0].legend(frameon=False)

    for iv_flag, label, color in [
        (1, "intervention", COLORS["intervention"]),
        (0, "autonomous", COLORS["value"]),
    ]:
        vals = df.loc[df["is_intervention"] == iv_flag, "advantage"].to_numpy()
        axs[0, 1].hist(vals, bins=60, alpha=0.55, density=True, label=label, color=color)
    axs[0, 1].set_title("Advantage Distribution by Control Mode")
    axs[0, 1].set_xlabel("advantage")
    axs[0, 1].set_ylabel("density")
    axs[0, 1].legend(frameon=False)

    axs[1, 0].hexbin(df["value"], df["advantage"], gridsize=60, cmap="magma", mincnt=1)
    axs[1, 0].set_title("Value-Advantage Joint Density")
    axs[1, 0].set_xlabel("value")
    axs[1, 0].set_ylabel("advantage")

    jitter = np.random.default_rng(0).normal(0.0, 0.003, size=len(df))
    axs[1, 1].scatter(
        df["value"].to_numpy(),
        df["acp_indicator"].to_numpy() + jitter,
        s=1,
        alpha=0.15,
        c=np.where(df["is_intervention"].to_numpy() > 0, COLORS["intervention"], COLORS["indicator"]),
    )
    axs[1, 1].set_title("ACP Indicator vs Value (colored by intervention)")
    axs[1, 1].set_xlabel("value")
    axs[1, 1].set_ylabel("acp indicator")
    axs[1, 1].set_yticks([0, 1])

    fig.tight_layout()
    fig.savefig(out / "fig02_label_distributions.png")
    plt.close(fig)


def pr_roc_from_scores(y_true: np.ndarray, score: np.ndarray) -> dict[str, np.ndarray]:
    order = np.argsort(-score)
    y = y_true[order].astype(np.int64)
    s = score[order]

    tp = np.cumsum(y)
    fp = np.cumsum(1 - y)
    total_pos = max(1, int(np.sum(y_true)))
    total_neg = max(1, int(len(y_true) - np.sum(y_true)))

    recall = tp / total_pos
    precision = tp / np.maximum(1, tp + fp)

    tpr = tp / total_pos
    fpr = fp / total_neg

    # budget-recall curve: top-k% frames -> intervention recall
    ks = np.linspace(0.01, 1.0, 100)
    budget_recall = []
    for k in ks:
        m = max(1, int(round(k * len(y))))
        budget_recall.append(float(np.sum(y[:m]) / total_pos))

    return {
        "precision": precision,
        "recall": recall,
        "tpr": tpr,
        "fpr": fpr,
        "budget": ks,
        "budget_recall": np.asarray(budget_recall, dtype=np.float32),
    }


def auc_xy(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    if x.size < 2:
        return 0.0
    order = np.argsort(x)
    return float(np.trapz(y[order], x[order]))


def plot_detection_curves(df: pd.DataFrame, out: Path) -> None:
    y_true = df["is_intervention"].to_numpy().astype(np.int64)
    score_indicator = df["acp_indicator"].to_numpy().astype(np.float32)
    score_adv = df["advantage"].to_numpy().astype(np.float32)
    score_risk = (-df["value"].to_numpy()).astype(np.float32)

    curves = {
        "ACP indicator": (score_indicator, "#264653"),
        "advantage": (score_adv, "#E76F51"),
        "risk=-value": (score_risk, "#2A9D8F"),
    }

    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))

    for name, (score, color) in curves.items():
        c = pr_roc_from_scores(y_true, score)
        auc_pr = auc_xy(c["recall"], c["precision"])
        auc_roc = auc_xy(c["fpr"], c["tpr"])
        axs[0].plot(c["recall"], c["precision"], lw=1.8, color=color, label=f"{name} (AUPR={auc_pr:.3f})")
        axs[1].plot(c["fpr"], c["tpr"], lw=1.8, color=color, label=f"{name} (AUROC={auc_roc:.3f})")
        axs[2].plot(c["budget"], c["budget_recall"], lw=1.8, color=color, label=name)

    axs[0].set_title("Intervention Detection: PR Curve")
    axs[0].set_xlabel("recall")
    axs[0].set_ylabel("precision")
    axs[0].legend(frameon=False, loc="lower left")

    axs[1].plot([0, 1], [0, 1], "k--", lw=1)
    axs[1].set_title("Intervention Detection: ROC Curve")
    axs[1].set_xlabel("false positive rate")
    axs[1].set_ylabel("true positive rate")
    axs[1].legend(frameon=False, loc="lower right")

    axs[2].set_title("Budget-Recall Curve")
    axs[2].set_xlabel("selected frame budget ratio")
    axs[2].set_ylabel("intervention recall")
    axs[2].legend(frameon=False, loc="lower right")

    fig.tight_layout()
    fig.savefig(out / "fig03_detection_curves.png")
    plt.close(fig)


def build_normalized_mats(df: pd.DataFrame, target_len: int = 220):
    episodes = sorted(df["episode_index"].unique().tolist())
    v_mat, a_mat, i_mat, h_mat = [], [], [], []
    success = []
    for ep in episodes:
        d = df[df["episode_index"] == ep].sort_values("frame_index")
        v_mat.append(normalize_episode_series(d["value"].to_numpy(), target_len))
        a_mat.append(normalize_episode_series(d["advantage"].to_numpy(), target_len))
        i_mat.append(normalize_episode_series(d["acp_indicator"].to_numpy(), target_len))
        h_mat.append(normalize_episode_series(d["is_intervention"].to_numpy(), target_len))
        success.append(int(d["success"].iloc[0]))

    return (
        np.asarray(episodes, dtype=np.int64),
        np.asarray(success, dtype=np.int64),
        np.stack(v_mat),
        np.stack(a_mat),
        np.stack(i_mat),
        np.stack(h_mat),
    )


def plot_heatmaps(df: pd.DataFrame, stats: pd.DataFrame, out: Path) -> None:
    eps, suc, v_mat, a_mat, i_mat, h_mat = build_normalized_mats(df, target_len=240)

    order = np.argsort(np.lexsort((-stats.set_index("episode_index").loc[eps, "mean_value"].to_numpy(), -suc)))
    # lexsort behavior is tricky; force custom ordering: success first then mean_value desc
    sort_key = np.stack([-suc, -stats.set_index("episode_index").loc[eps, "mean_value"].to_numpy()], axis=1)
    order = np.lexsort((sort_key[:, 1], sort_key[:, 0]))

    v = v_mat[order]
    a = a_mat[order]
    i = i_mat[order]
    h = h_mat[order]

    fig, axs = plt.subplots(2, 2, figsize=(14, 9), sharex=True, sharey=True)
    im0 = axs[0, 0].imshow(v, aspect="auto", cmap="viridis")
    axs[0, 0].set_title("Value Heatmap (episodes x normalized time)")
    fig.colorbar(im0, ax=axs[0, 0], fraction=0.046)

    im1 = axs[0, 1].imshow(a, aspect="auto", cmap="coolwarm")
    axs[0, 1].set_title("Advantage Heatmap")
    fig.colorbar(im1, ax=axs[0, 1], fraction=0.046)

    im2 = axs[1, 0].imshow(i, aspect="auto", cmap="Greys")
    axs[1, 0].set_title("ACP Indicator Raster")
    fig.colorbar(im2, ax=axs[1, 0], fraction=0.046)

    im3 = axs[1, 1].imshow(h, aspect="auto", cmap="Oranges")
    axs[1, 1].set_title("Intervention Raster")
    fig.colorbar(im3, ax=axs[1, 1], fraction=0.046)

    for ax in axs.ravel():
        ax.set_xlabel("normalized time")
        ax.set_ylabel("episode rank")

    fig.tight_layout()
    fig.savefig(out / "fig04_episode_heatmaps.png")
    plt.close(fig)


def plot_onset_aligned(df: pd.DataFrame, out: Path, fps: int = 30) -> None:
    pre = int(2.5 * fps)
    post = int(3.5 * fps)
    span = pre + post + 1

    value_segments = []
    adv_segments = []
    ind_segments = []

    for ep, d in df.groupby("episode_index"):
        d = d.sort_values("frame_index")
        iv = d["is_intervention"].to_numpy().astype(np.int64)
        onsets = np.where((iv[1:] == 1) & (iv[:-1] == 0))[0] + 1
        vals = d["value"].to_numpy()
        adv = d["advantage"].to_numpy()
        ind = d["acp_indicator"].to_numpy().astype(np.float32)
        n = len(d)
        for idx in onsets:
            l = idx - pre
            r = idx + post
            if l < 0 or r >= n:
                continue
            value_segments.append(vals[l : r + 1])
            adv_segments.append(adv[l : r + 1])
            ind_segments.append(ind[l : r + 1])

    if len(value_segments) == 0:
        return

    value_arr = np.stack(value_segments)
    adv_arr = np.stack(adv_segments)
    ind_arr = np.stack(ind_segments)

    t = (np.arange(span) - pre) / float(fps)

    def mean_ci(arr: np.ndarray):
        m = arr.mean(axis=0)
        s = arr.std(axis=0) / max(1.0, np.sqrt(arr.shape[0]))
        return m, m - 1.96 * s, m + 1.96 * s

    mv, lv, uv = mean_ci(value_arr)
    ma, la, ua = mean_ci(adv_arr)
    mi, li, ui = mean_ci(ind_arr)

    fig, axs = plt.subplots(3, 1, figsize=(10, 9), sharex=True)

    axs[0].plot(t, mv, color=COLORS["value"], lw=2)
    axs[0].fill_between(t, lv, uv, color=COLORS["value"], alpha=0.25)
    axs[0].axvline(0.0, color="k", ls="--", lw=1)
    axs[0].set_title("Intervention Onset-aligned Value Dynamics")
    axs[0].set_ylabel("value")

    axs[1].plot(t, ma, color=COLORS["adv"], lw=2)
    axs[1].fill_between(t, la, ua, color=COLORS["adv"], alpha=0.25)
    axs[1].axvline(0.0, color="k", ls="--", lw=1)
    axs[1].set_ylabel("advantage")

    axs[2].plot(t, mi, color=COLORS["indicator"], lw=2, label="ACP indicator")
    axs[2].fill_between(t, li, ui, color=COLORS["indicator"], alpha=0.2)
    axs[2].axvline(0.0, color="k", ls="--", lw=1)
    axs[2].set_ylabel("indicator probability")
    axs[2].set_xlabel("seconds from intervention onset")

    fig.tight_layout()
    fig.savefig(out / "fig05_onset_aligned_dynamics.png")
    plt.close(fig)


def plot_confusion_and_calibration(df: pd.DataFrame, out: Path) -> None:
    y = df["is_intervention"].to_numpy().astype(np.int64)
    p = df["acp_indicator"].to_numpy().astype(np.int64)

    tp = int(np.sum((p == 1) & (y == 1)))
    fp = int(np.sum((p == 1) & (y == 0)))
    fn = int(np.sum((p == 0) & (y == 1)))
    tn = int(np.sum((p == 0) & (y == 0)))
    cm = np.array([[tn, fp], [fn, tp]], dtype=np.float64)
    cm_norm = cm / np.maximum(1.0, cm.sum(axis=1, keepdims=True))

    q = pd.qcut(df["advantage"], 10, labels=False, duplicates="drop")
    cal = (
        pd.DataFrame({"q": q, "iv": y, "acp": p})
        .groupby("q", as_index=False)
        .agg(intervention_rate=("iv", "mean"), acp_positive_rate=("acp", "mean"), count=("iv", "count"))
    )

    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))

    im = axs[0].imshow(cm_norm, cmap="Blues", vmin=0.0, vmax=1.0)
    for i in range(2):
        for j in range(2):
            axs[0].text(j, i, f"{cm[i,j]:.0f}\n({cm_norm[i,j]:.2f})", ha="center", va="center", fontsize=10)
    axs[0].set_xticks([0, 1], labels=["pred 0", "pred 1"])
    axs[0].set_yticks([0, 1], labels=["true 0", "true 1"])
    axs[0].set_title("ACP Indicator vs Intervention\n(confusion matrix)")
    fig.colorbar(im, ax=axs[0], fraction=0.048)

    axs[1].plot(cal["q"], cal["intervention_rate"], "-o", color=COLORS["intervention"], label="intervention rate")
    axs[1].plot(cal["q"], cal["acp_positive_rate"], "-s", color=COLORS["indicator"], label="acp positive rate")
    axs[1].set_title("Calibration Across Advantage Deciles")
    axs[1].set_xlabel("advantage decile")
    axs[1].set_ylabel("rate")
    axs[1].set_ylim(0, 1)
    axs[1].legend(frameon=False)

    fig.tight_layout()
    fig.savefig(out / "fig06_confusion_calibration.png")
    plt.close(fig)


def plot_temporal_profiles(df: pd.DataFrame, out: Path) -> None:
    eps, suc, v_mat, a_mat, i_mat, h_mat = build_normalized_mats(df, target_len=220)

    succ_mask = suc == 1
    fail_mask = suc == 0

    def mean_band(arr: np.ndarray):
        if arr.size == 0:
            z = np.zeros(arr.shape[1] if arr.ndim == 2 else 220)
            return z, z, z
        m = arr.mean(axis=0)
        p25 = np.percentile(arr, 25, axis=0)
        p75 = np.percentile(arr, 75, axis=0)
        return m, p25, p75

    t = np.linspace(0, 1, v_mat.shape[1])

    fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True)

    for mask, label, color in [(succ_mask, "success", COLORS["success"]), (fail_mask, "failure", COLORS["failure"])]:
        m, l, u = mean_band(v_mat[mask])
        axs[0, 0].plot(t, m, color=color, lw=2, label=label)
        axs[0, 0].fill_between(t, l, u, color=color, alpha=0.18)

        m, l, u = mean_band(a_mat[mask])
        axs[0, 1].plot(t, m, color=color, lw=2, label=label)
        axs[0, 1].fill_between(t, l, u, color=color, alpha=0.18)

        m, l, u = mean_band(i_mat[mask])
        axs[1, 0].plot(t, m, color=color, lw=2, label=label)
        axs[1, 0].fill_between(t, l, u, color=color, alpha=0.18)

        m, l, u = mean_band(h_mat[mask])
        axs[1, 1].plot(t, m, color=color, lw=2, label=label)
        axs[1, 1].fill_between(t, l, u, color=color, alpha=0.18)

    axs[0, 0].set_title("Value Trajectory (normalized timeline)")
    axs[0, 1].set_title("Advantage Trajectory")
    axs[1, 0].set_title("ACP Indicator Probability")
    axs[1, 1].set_title("Intervention Probability")

    for ax in axs.ravel():
        ax.set_xlabel("normalized episode progress")
        ax.legend(frameon=False)

    fig.tight_layout()
    fig.savefig(out / "fig07_temporal_profiles_success_failure.png")
    plt.close(fig)


def compute_run_lengths(binary: np.ndarray) -> list[int]:
    runs = []
    cnt = 0
    for x in binary:
        if int(x) == 1:
            cnt += 1
        else:
            if cnt > 0:
                runs.append(cnt)
                cnt = 0
    if cnt > 0:
        runs.append(cnt)
    return runs


def plot_runlength_and_lag(df: pd.DataFrame, out: Path) -> None:
    acp_runs = compute_run_lengths(df["acp_indicator"].to_numpy())
    iv_runs = compute_run_lengths(df["is_intervention"].to_numpy())

    # lag correlation (frame level, approximate)
    x = df["acp_indicator"].to_numpy().astype(np.float32)
    y = df["is_intervention"].to_numpy().astype(np.float32)
    x = (x - x.mean()) / (x.std() + 1e-6)
    y = (y - y.mean()) / (y.std() + 1e-6)
    max_lag = 180
    lags = np.arange(-max_lag, max_lag + 1)
    corr = []
    for lag in lags:
        if lag < 0:
            a = x[-lag:]
            b = y[: len(y) + lag]
        elif lag > 0:
            a = x[: len(x) - lag]
            b = y[lag:]
        else:
            a = x
            b = y
        corr.append(float(np.mean(a * b)))
    corr = np.asarray(corr, dtype=np.float32)

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))

    bins = np.arange(1, max(max(acp_runs or [1]), max(iv_runs or [1])) + 2)
    axs[0].hist(acp_runs, bins=bins, alpha=0.6, label="acp indicator", color=COLORS["indicator"], density=True)
    axs[0].hist(iv_runs, bins=bins, alpha=0.6, label="intervention", color=COLORS["intervention"], density=True)
    axs[0].set_yscale("log")
    axs[0].set_title("Consecutive Positive Run Length Distribution")
    axs[0].set_xlabel("run length (frames)")
    axs[0].set_ylabel("density (log)")
    axs[0].legend(frameon=False)

    axs[1].plot(lags / 30.0, corr, color="#4C78A8", lw=1.8)
    axs[1].axvline(0.0, ls="--", color="k", lw=1)
    axs[1].set_title("Cross-correlation: ACP Indicator vs Intervention")
    axs[1].set_xlabel("lag (seconds)")
    axs[1].set_ylabel("normalized correlation")

    fig.tight_layout()
    fig.savefig(out / "fig08_runlength_lagcorr.png")
    plt.close(fig)


def plot_episode_case_study(df: pd.DataFrame, stats: pd.DataFrame, out: Path) -> list[int]:
    succ = stats[stats["success"] == 1].sort_values("quality_score", ascending=False)
    fail = stats[stats["success"] == 0].sort_values("quality_score", ascending=True)

    chosen = []
    if len(succ) >= 2:
        chosen.extend([int(succ.iloc[0]["episode_index"]), int(succ.iloc[min(1, len(succ)-1)]["episode_index"])])
    if len(fail) >= 2:
        chosen.extend([int(fail.iloc[0]["episode_index"]), int(fail.iloc[min(1, len(fail)-1)]["episode_index"])])
    chosen = chosen[:4]

    fig, axs = plt.subplots(len(chosen), 1, figsize=(14, 2.5 * len(chosen)), sharex=False)
    if len(chosen) == 1:
        axs = [axs]

    for ax, ep in zip(axs, chosen, strict=True):
        d = df[df["episode_index"] == ep].sort_values("frame_index")
        x = d["frame_index"].to_numpy() / 30.0
        v = d["value"].to_numpy()
        a = d["advantage"].to_numpy()
        iv = d["is_intervention"].to_numpy().astype(np.float32)
        ind = d["acp_indicator"].to_numpy().astype(np.float32)

        ax.plot(x, moving_avg(v, 9), color=COLORS["value"], lw=1.6, label="value")
        ax.plot(x, moving_avg(a, 9), color=COLORS["adv"], lw=1.4, label="advantage")
        ax.fill_between(x, -0.02, 0.02, where=iv > 0.5, color=COLORS["intervention"], alpha=0.25, label="intervention")
        ax.fill_between(x, -0.045, -0.025, where=ind > 0.5, color=COLORS["indicator"], alpha=0.7, label="acp=1")

        s = int(d["success"].iloc[0])
        ax.set_title(f"Episode {ep} | {'success' if s == 1 else 'failure'}")
        ax.set_ylabel("score")
        ax.legend(frameon=False, ncol=4, loc="upper right")
        ax.grid(alpha=0.25)

    axs[-1].set_xlabel("time (s)")
    fig.tight_layout()
    fig.savefig(out / "fig09_case_study_timelines.png")
    plt.close(fig)
    return chosen


def plot_budget_tables(stats: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    scores = stats["quality_score"].to_numpy()
    idx = np.argsort(-scores)
    sorted_success = stats["success"].to_numpy()[idx]

    budgets = np.array([1, 2, 3, 5, 8, 13, 21, 34, 51])
    budgets = budgets[budgets <= len(sorted_success)]
    hit = np.array([sorted_success[:b].mean() for b in budgets])

    ax.plot(budgets, hit, "-o", color="#6A4C93", lw=2)
    ax.set_ylim(0, 1.05)
    ax.set_xlabel("Top-k episodes selected by quality score")
    ax.set_ylabel("success ratio")
    ax.set_title("Episode Ranking Utility Curve")
    ax.grid(alpha=0.3)

    fig.tight_layout()
    fig.savefig(out / "fig10_episode_ranking_curve.png")
    plt.close(fig)


def save_tables(df: pd.DataFrame, stats: pd.DataFrame, out: Path) -> None:
    table_dir = out / "tables"
    ensure_dir(table_dir)
    stats.to_csv(table_dir / "episode_stats.csv", index=False)

    summary = {
        "num_frames": int(len(df)),
        "num_episodes": int(stats.shape[0]),
        "success_episodes": int(stats["success"].sum()),
        "failure_episodes": int((stats["success"] == 0).sum()),
        "frame_intervention_ratio": float(df["is_intervention"].mean()),
        "frame_acp_positive_ratio": float(df["acp_indicator"].mean()),
        "value_mean": float(df["value"].mean()),
        "value_std": float(df["value"].std()),
        "advantage_mean": float(df["advantage"].mean()),
        "advantage_std": float(df["advantage"].std()),
    }
    with open(table_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate publication-grade visualizations for Evo-RL value-infer dataset.")
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    fig_dir = args.output_dir / "figures"
    ensure_dir(fig_dir)
    ensure_dir(args.output_dir)

    df, ep_df = load_data(args.dataset_root)
    stats = build_episode_stats(df)

    save_tables(df, stats, args.output_dir)
    plot_overview(stats, fig_dir)
    plot_distributions(df, stats, fig_dir)
    plot_detection_curves(df, fig_dir)
    plot_heatmaps(df, stats, fig_dir)
    plot_onset_aligned(df, fig_dir)
    plot_confusion_and_calibration(df, fig_dir)
    plot_temporal_profiles(df, fig_dir)
    plot_runlength_and_lag(df, fig_dir)
    chosen = plot_episode_case_study(df, stats, fig_dir)
    plot_budget_tables(stats, fig_dir)

    print(f"[done] output_dir={args.output_dir}")
    print(f"[done] figures={fig_dir}")
    print(f"[done] chosen_case_episodes={chosen}")


if __name__ == "__main__":
    main()
