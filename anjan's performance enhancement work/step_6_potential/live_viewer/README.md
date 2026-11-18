# Local convergence viewer

From `step_6_potential/`, open another terminal and run:

```bash
python live_viewer/serve.py
```

Then open **http://127.0.0.1:8765/** in Firefox. No additional packages or internet access are needed. Leave the viewer server and solver running in their separate terminals.

By default the server selects the most recently updated `runs/*/convergence.csv` **at startup** and prints the selected path. It stays attached to that file. To select the current run explicitly:

```bash
python live_viewer/serve.py --csv runs/20261116_103848_750500/convergence.csv
```

If the port is occupied, add `--port 8766` and open the printed URL. Ctrl+C stops only this viewer, not the solver. This server is bound to 127.0.0.1 and exposes only the viewer assets, selected CSV and its path metadata; it does not serve the rest of the repository. It never writes to the CSV or starts/modifies a simulation. Open the printed HTTP URL rather than double-clicking index.html: browser file access restrictions prevent automatic local CSV reads under file://.

The page polls the selected CSV every **2 seconds**, disables response caching, and redraws on changed contents. It ignores incomplete trailing rows while the logger appends data. Data continues to display after a run stops; a stale timestamp does not by itself establish whether the solver is running.

It shows:

- Latest logged iteration, maximum change, solver elapsed time and interval-average seconds per iteration.
- Maximum change on a logarithmic vertical axis, against iteration or elapsed minutes, with the 0.001 tolerance line. Hover over the error plot to inspect a sample.
- Interval-average iteration timing against the same selected horizontal axis.

The CSV is the sole data source; it records only logged iteration samples, not every individual iteration or final run status. No new numerical measurements are introduced. Firefox checks covered loading real run data, both charts, axis switching, automatic updates after appending to a disposable CSV copy, and ignoring an incomplete appended row. The user's real CSV was not changed by those tests.

## Retained run and chart evidence

The [completed potential-field report](../potential_20261116_103848_750500.md) is the execution evidence for the example CSV above. A [saved convergence screenshot](snapshots/convergence_20261116.png) is retained for reference; live readings require the ignored local CSV. If the example run data are absent after cloning, the screenshot/report remain readable but the viewer needs a compatible CSV or a new deliberately launched run. This viewer does not provide WSR checkpoint/resume controls; [step 7's separate viewer](../../step_7_nlfff/live_viewer/README.md) reads the reconstruction progress schema. Documentation reviewed 18 November 2026; no solver or CSV was changed.
