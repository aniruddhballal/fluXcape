# WSR / NLFFF live viewer

From `step_7_nlfff/`, in a second terminal:

```bash
python live_viewer/serve.py
```

Open **http://127.0.0.1:8766/** in Firefox. The local server selects the most recently updated `runs/*/convergence.csv` at startup and stays attached to that file. It prints the exact selected path. Start the new measurement first and wait for its CSV to appear. To choose a specific run, use `--csv runs/RUN_ID/convergence.csv`. If port 8766 is occupied, pass `--port 8767` and open the printed URL.

The page polls every two seconds with caching disabled. It displays accepted steps, attempts/rejections, objective L and L/initial-L, next dt, elapsed wall time and time per attempt. The graphs show L and attempt timing against elapsed minutes or attempt count. There is no artificial L=0.001 line: that was the step 6 stopping criterion, not the step 7 objective.

All attempt events are shown. `next_dt` is after the original accepted +1% / rejected halving update, not the dt just used. Wall-clock elapsed is distinct from the numerical relaxation_time column. The first attempt interval includes initial checkpoint writing; periodic checkpoint overhead appears in the next interval. A finished event marks normal code exit; a stale CSV alone cannot distinguish computation, checkpoint writing or a stopped process. A timeout does not generate a normal finished event.

No packages, internet connection or uploaded data are needed. The server binds to localhost and exposes only viewer assets, selected CSV and its path metadata. It does not write the CSV or run the reconstruction. Ctrl+C stops only the viewer. Existing text logs and numerical checkpoint files remain unchanged. Older step 7 runs have no CSV; start a new measurement with the updated script.
