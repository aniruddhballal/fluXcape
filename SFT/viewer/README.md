# Synoptic Studio

The Python reconstruction calculates the original map, both reconstructed maps
and their comparison metrics. `prepare_viewer_data.py` exports those results to the
ignored `public/maps.json` file. The React viewer reads that file and handles
display only; it does not run the reconstruction.

From the repository root, install the viewer dependencies once:

```powershell
cd SFT\viewer
npm install
cd ..\..
```

Then prepare the data and launch the viewer:

```powershell
.\.venv\Scripts\python.exe SFT\prepare_viewer_data.py
cd SFT\viewer
npm run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173/). The
data preparation command regenerates the data, so rerun it after changes to the
reconstruction or chosen rotations. Press Ctrl+C in the terminal to stop the
viewer.

The 2D and 3D views display the same FITS values. For the globe, the renderer
maps the FITS sine-latitude rows onto the sphere; missing pixels remain dark.
The version dropdown switches between the precomputed maps, while the
color saturation slider only affects display. Comparison metrics are differences
from the original map, not errors against ground truth.
