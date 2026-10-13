"""F_threshold_study.py - Sensitivitaet der Kalibrier-Schwellen (Thesis Abschnitt 5.1.3).

Nutzt die akzeptierten Views aus mono_cam{1,2,3}.pkl (raw_detections: path, ids, charuco).
  1. View-Zahl: je Kamera und N zufaellige Teilmengen von N Views, Kalibrierung 5-Param und rational;
     Held-out-Fehler auf allen uebrigen Views, indem nur die Board-Pose neu gefittet wird (solvePnP).
  2. Coverage: verschachtelte Teilmengen der zentralsten Views (Abstand Eckenschwerpunkt zur Bildmitte),
     Kalibrierung 5-Param, Held-out auf den ausgeschlossenen aeusseren Views, nach Coverage-Bins.
  3. 5-fache Kreuzvalidierung 5-Param gegen rational auf dem vollen View-Satz.
Ausgabe: threshold_study.csv (Langformat) und threshold_study.md (Tabellen), aus ~/Documents/TestCalib/.
    conda activate masterprojekt && python F_threshold_study.py
"""
from __future__ import annotations
import csv, pickle, sys, time
import numpy as np, cv2
import calib_common as cc

rng = np.random.default_rng(0)
N_LIST = [6, 8, 10, 12, 15, 20, 30, 40, 60]
DRAWS = 20
COV_BINS = [(0.0, 0.35), (0.35, 0.55), (0.55, 0.75), (0.75, 1.01)]
CRIT = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 300, 1e-9)
board = cc.make_board()
rows = []


def add(**kw):
    rows.append(kw)


def load(cam):
    d = pickle.load(open(f"mono_cam{cam}.pkl", "rb"))
    views = []
    for v in d["raw_detections"]:
        corners = np.asarray(v["charuco"], dtype=np.float32).reshape(-1, 1, 2)
        ids = np.asarray(v["ids"], dtype=np.int32).reshape(-1, 1)
        obj, img = board.matchImagePoints(corners, ids)
        views.append(dict(obj=obj.reshape(-1, 1, 3).astype(np.float32), img=img.reshape(-1, 1, 2).astype(np.float32)))
    return views, tuple(d["image_size"]), float(d["rms"])


def calib(views, size, flags):
    rms, K, D, rv, tv = cv2.calibrateCamera([v["obj"] for v in views], [v["img"] for v in views], size, None, None, flags=flags, criteria=CRIT)
    return rms, K, D


def heldout(views, K, D):
    """RMS ueber alle Punkte der Held-out-Views nach solvePnP (nur Board-Pose gefittet); plus RMS je View."""
    se, n, per = 0.0, 0, []
    for v in views:
        ok, r, t = cv2.solvePnP(v["obj"], v["img"], K, D, flags=cv2.SOLVEPNP_ITERATIVE)
        if not ok:
            continue
        proj, _ = cv2.projectPoints(v["obj"], r, t, K, D)
        d2 = np.sum((proj.reshape(-1, 2) - v["img"].reshape(-1, 2)) ** 2, axis=1)
        se += d2.sum(); n += len(d2); per.append(float(np.sqrt(d2.mean())))
    return float(np.sqrt(se / max(n, 1))), np.array(per)


t0 = time.time()
for cam in (1, 2, 3):
    views, size, rms_full = load(cam)
    V = len(views)
    print(f"[cam{cam}] {V} views, size {size}, RMS full {rms_full:.4f}", flush=True)
    # --- 1. View-Zahl
    for N in N_LIST:
        if N > V - 5:
            continue
        for d in range(DRAWS):
            idx = rng.permutation(V); tr, te = idx[:N], idx[N:]
            trv, tev = [views[i] for i in tr], [views[i] for i in te]
            try:
                r5, K5, D5 = calib(trv, size, 0)
                rR, KR, DR = calib(trv, size, cv2.CALIB_RATIONAL_MODEL)
            except cv2.error as e:
                add(study="views", cam=cam, N=N, draw=d, note="calib failed"); continue
            h5, _ = heldout(tev, K5, D5); hR, _ = heldout(tev, KR, DR)
            add(study="views", cam=cam, N=N, draw=d, train5=r5, trainR=rR, held5=h5, heldR=hR,
                gainR=(r5 - rR) / r5, ratio5=h5 / r5, fx5=float(K5[0, 0]), fxR=float(KR[0, 0]))
        print(f"  N={N} done ({time.time()-t0:.0f}s)", flush=True)
    # --- 2. Coverage (verschachtelt, zentralste Views zuerst)
    cx, cy = size[0] / 2, size[1] / 2
    cent = np.array([np.hypot(*(v["img"].reshape(-1, 2).mean(0) - (cx, cy))) for v in views])
    order = np.argsort(cent)
    for k in list(range(12, V, max(1, (V - 12) // 12))) + [V]:
        sub = [views[i] for i in order[:k]]; out = [views[i] for i in order[k:]]
        cov = cc.coverage_heatmap_score([v["img"] for v in sub], size)
        r5, K5, D5 = calib(sub, size, 0)
        if out:
            h5, per = heldout(out, K5, D5)
            add(study="coverage", cam=cam, k=k, coverage=cov, train5=r5, held5=h5, held_med=float(np.median(per)), held_max=float(per.max()), n_out=len(out))
        else:
            add(study="coverage", cam=cam, k=k, coverage=cov, train5=r5, n_out=0)
    print(f"  coverage done ({time.time()-t0:.0f}s)", flush=True)
    # --- 3. 5-fold CV
    idx = rng.permutation(V); folds = np.array_split(idx, 5)
    for fi, te in enumerate(folds):
        tr = np.setdiff1d(idx, te)
        r5, K5, D5 = calib([views[i] for i in tr], size, 0); rR, KR, DR = calib([views[i] for i in tr], size, cv2.CALIB_RATIONAL_MODEL)
        h5, _ = heldout([views[i] for i in te], K5, D5); hR, _ = heldout([views[i] for i in te], KR, DR)
        add(study="cv5", cam=cam, fold=fi, train5=r5, trainR=rR, held5=h5, heldR=hR, gainR=(r5 - rR) / r5)
    r5, _, _ = calib(views, size, 0); rR, _, _ = calib(views, size, cv2.CALIB_RATIONAL_MODEL)
    add(study="full", cam=cam, train5=r5, trainR=rR, gainR=(r5 - rR) / r5, V=V)

keys = sorted({k for r in rows for k in r})
with open("threshold_study.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)

# --- Tabellen
md = []
md.append("## View-Zahl (schlechteste Kamera): Held-out-RMS 90. Perzentil ueber die Draws, max. Gewinn rational (Training), Median Held-out/Train\n")
md.append("| N | held-out RMS p90 [px] | held-out RMS median [px] | rational max gain | held-out / train (median) | draws |\n|---|---|---|---|---|---|")
for N in N_LIST:
    sel = [r for r in rows if r["study"] == "views" and r["N"] == N and "held5" in r]
    if not sel: continue
    p90 = max(np.percentile([r["held5"] for r in sel if r["cam"] == c], 90) for c in (1, 2, 3) if any(r["cam"] == c for r in sel))
    med = max(np.median([r["held5"] for r in sel if r["cam"] == c]) for c in (1, 2, 3) if any(r["cam"] == c for r in sel))
    gain = max(r["gainR"] for r in sel); ratio = max(np.median([r["ratio5"] for r in sel if r["cam"] == c]) for c in (1, 2, 3) if any(r["cam"] == c for r in sel))
    md.append(f"| {N} | {p90:.2f} | {med:.2f} | {100*gain:.1f} % | {ratio:.2f} | {len(sel)} |")
md.append("\n## Coverage-Bins (alle Kameras gepoolt): Held-out-RMS auf den ausgeschlossenen aeusseren Views\n")
md.append("| Coverage | Teilmengen | held-out RMS median [px] | held-out RMS max [px] | train RMS median [px] |\n|---|---|---|---|---|")
for lo, hi in COV_BINS:
    sel = [r for r in rows if r["study"] == "coverage" and r.get("n_out", 0) > 0 and lo <= r["coverage"] < hi]
    if not sel: continue
    md.append(f"| {100*lo:.0f}–{100*min(hi,1):.0f} % | {len(sel)} | {np.median([r['held_med'] for r in sel]):.2f} | {max(r['held_max'] for r in sel):.2f} | {np.median([r['train5'] for r in sel]):.3f} |")
md.append("\n## Voller View-Satz und 5-fache Kreuzvalidierung\n")
md.append("| Kamera | Views | train RMS 5-param | train RMS rational | Gewinn | CV held-out 5-param | CV held-out rational |\n|---|---|---|---|---|---|---|")
for c in (1, 2, 3):
    fu = [r for r in rows if r["study"] == "full" and r["cam"] == c][0]; cv = [r for r in rows if r["study"] == "cv5" and r["cam"] == c]
    md.append(f"| CAM{c} | {fu['V']} | {fu['train5']:.4f} | {fu['trainR']:.4f} | {100*fu['gainR']:.2f} % | {np.mean([r['held5'] for r in cv]):.3f} | {np.mean([r['heldR'] for r in cv]):.3f} |")
open("threshold_study.md", "w").write("\n".join(md) + "\n")
print("\n".join(md)); print(f"done in {time.time()-t0:.0f}s")
