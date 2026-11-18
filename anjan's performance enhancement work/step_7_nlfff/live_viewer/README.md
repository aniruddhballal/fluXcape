# WSR / NLFFF live viewer

From `step_7_nlfff/`, in a second terminal:

```bash
python live_viewer/serve.py
```

Open **http://127.0.0.1:8766/** in Firefox. The local server selects the most recently updated `runs/*/convergence.csv` at startup and stays attached to that file. It prints the exact selected path. Start the new measurement first and wait for its CSV to appear. To choose a specific run, use `--csv runs/RUN_ID/convergence.csv`. If port 8766 is occupied, pass `--port 8767` and open the printed URL.

The page polls every two seconds with caching disabled. It displays accepted steps, attempts/rejections, objective L and L/initial-L, next dt, elapsed wall time and time per attempt. The top row splits equally into L and next-dt graphs (both logarithmic); attempt timing spans the row below. The shared X-axis selector switches all three between elapsed minutes and attempt count. Narrow screens stack the top graphs. There is no artificial L=0.001 line: that was the step 6 stopping criterion, not the step 7 objective.

All attempt events are shown. `next_dt` is after the original accepted +1% / rejected halving update, not the dt just used. Wall-clock elapsed is distinct from the numerical relaxation_time column. The first attempt interval includes initial checkpoint writing; periodic checkpoint overhead appears in the next interval. A finished event marks normal code exit; a stale CSV alone cannot distinguish computation, checkpoint writing or a stopped process. A timeout does not generate a normal finished event.

No packages, internet connection or uploaded data are needed. The server binds to localhost and exposes only viewer assets, selected CSV and its path metadata. It does not write the CSV or run the reconstruction. Ctrl+C stops only the viewer. Existing text logs and numerical checkpoint files remain unchanged. Older step 7 runs have no CSV; start a new measurement with the updated script.

## Zoom

- Drag a rectangle over any plot to zoom into both axes. A mostly horizontal or vertical drag zooms only that axis.
- Use the mouse wheel over a plot to zoom in/out around the pointer.
- Double-click the plot or click its **Reset zoom** button to restore the full view.
- Each plot has an independent zoom. Live CSV refreshes preserve it; changing the shared X-axis selector resets all plots because the axis units change.

Curves are clipped to the selected region; all CSV data remain available. Zooming only changes the browser display, never the running solver or its output files. Firefox tests covered rectangle/wheel zoom, reset, independent plots, live-update persistence and the compact desktop layout.

## Fullscreen

Each graph has a **Fullscreen** button. The selected panel fills the screen while zoom controls and live updates keep working. Use **Exit fullscreen** or the browser's Escape key to return. Existing zoom is preserved on entry/exit. Firefox checks covered all three panels, live refresh in fullscreen and restoration of the compact layout. No solver process or CSV changes are involved.

## Moving hover marker

Move over any graph to see a highlighted dot snap to the nearest visible logged point, with a vertical guide and value bubble. The bubble shows the graph's value, attempt/accepted-step counts, elapsed minutes and event. It follows the curve's recorded samples rather than inventing interpolated values. Markers work in zoomed/fullscreen views, hide during drag selection or on pointer leave, and are restored during live redraws while the pointer remains over the graph. No data or solver settings are changed.

## Resumed runs and retained evidence

The viewer supports the history/`resumed` rows written by the current [measurement and resume tools](../README.md). A resumed invocation writes a new CSV with preserved history and a continued active-time axis; this is not the same as the wall time of that invocation or the numerical relaxation time. Start a new viewer or pass `--csv` to select that new file: an existing server never follows the newest run automatically after startup.

[The step 7 guide](../README.md#current-status) links the finalized bounded-run reports and a dated 18 November continuation snapshot. The [retained timestep comparison](../analysis/dt_curve_comparison_from_minute_240_20261118.png) is a static diagnostic, not the live source. Run CSVs and restart packages are local ignored artifacts; a clone does not contain them. Checkpoint capture/resume is handled by the runner, not by browser controls. Documentation reviewed 18 November 2026; no live data were modified.
