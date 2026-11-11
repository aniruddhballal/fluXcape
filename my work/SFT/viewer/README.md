# Synoptic Studio

The Python reconstruction calculates the original map and both reconstructed maps.
`validate_observations.py` compares them with an HMI 45-second observation using
one common mask. `prepare_viewer_data.py` exports those results to the
ignored `public/maps.json` file. The React viewer reads that file and handles
display only; it does not run the reconstruction.

From the repository root, install the viewer dependencies once:

```powershell
npm --prefix ".\my work\SFT\viewer" install
```

Then prepare the data and launch the viewer:

```powershell
.\.venv\Scripts\python.exe ".\my work\SFT\validate_observations.py" --rotation 2120
.\.venv\Scripts\python.exe ".\my work\SFT\prepare_viewer_data.py"
npm --prefix ".\my work\SFT\viewer" run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173/). The
validation requires JSOC access and accepts another central rotation when three
consecutive input maps are available. Rerun validation and data preparation
after changing the reconstruction or input maps. Stale scores are omitted.
Synoptic input maps are shared from `my work/fits_files/`; the downloader is
`my work/download_synoptic_maps.py`.
Press Ctrl+C in the terminal to stop the viewer.

The 2D and 3D views display the same FITS values. For the globe, the renderer
maps the FITS sine-latitude rows onto the sphere; missing pixels remain dark.
The version dropdown switches between the precomputed maps, while the
color saturation slider only affects display. The viewer shows observational
comparison metrics, with the qualifications in `../observational_validation.md`.
