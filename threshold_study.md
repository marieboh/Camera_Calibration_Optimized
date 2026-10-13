## View-Zahl (schlechteste Kamera): Held-out-RMS 90. Perzentil ueber die Draws, max. Gewinn rational (Training), Median Held-out/Train

| N | held-out RMS p90 [px] | held-out RMS median [px] | rational max gain | held-out / train (median) | draws |
|---|---|---|---|---|---|
| 6 | 93766647816.44 | 0.40 | 7.7 % | 2.14 | 60 |
| 8 | 1.17 | 0.32 | 5.1 % | 1.52 | 60 |
| 10 | 1.10 | 0.30 | 3.4 % | 1.42 | 60 |
| 12 | 0.36 | 0.30 | 3.3 % | 1.21 | 60 |
| 15 | 0.51 | 0.30 | 2.9 % | 1.22 | 60 |
| 20 | 0.31 | 0.29 | 2.3 % | 1.21 | 60 |
| 30 | 0.32 | 0.30 | 1.7 % | 1.15 | 60 |
| 40 | 0.33 | 0.28 | 1.4 % | 1.07 | 60 |
| 60 | 0.32 | 0.27 | 1.1 % | 1.04 | 40 |

## Coverage-Bins (alle Kameras gepoolt): Held-out-RMS auf den ausgeschlossenen aeusseren Views

| Coverage | Teilmengen | held-out RMS median [px] | held-out RMS max [px] | train RMS median [px] |
|---|---|---|---|---|
| 0–35 % | 19 | 2.02 | 10772226768896.00 | 0.306 |
| 35–55 % | 6 | 0.74 | 88.30 | 0.275 |
| 55–75 % | 10 | 0.35 | 8.82 | 0.264 |
| 75–100 % | 6 | 0.32 | 1.14 | 0.261 |

## Voller View-Satz und 5-fache Kreuzvalidierung

| Kamera | Views | train RMS 5-param | train RMS rational | Gewinn | CV held-out 5-param | CV held-out rational |
|---|---|---|---|---|---|---|
| CAM1 | 117 | 0.2500 | 0.2491 | 0.37 % | 0.252 | 0.252 |
| CAM2 | 61 | 0.2824 | 0.2816 | 0.28 % | 0.285 | 0.285 |
| CAM3 | 67 | 0.2697 | 0.2693 | 0.13 % | 0.273 | 0.273 |
