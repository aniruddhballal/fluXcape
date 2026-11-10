# Repository inventory and preservation

The initial read-only census covered all 281 existing project artifacts, including ignored scientific inputs/outputs and the viewer's generated data, with SHA-256 hashes. Git internals, the Python environment, node packages, bytecode and compiled frontend build directories were excluded as infrastructure/cache. All project text was read for the census, and Python imports/functions were indexed where parseable. Detailed source review focused on reconstruction, validator, FITS downloader, cached metadata/results, existing coordinate tests, research initialization/evolution conventions, the viewer exporter, and accompanying reports.

| Area | Existing role | Audit treatment |
|---|---|---|
| `ananya_research_work-main/SFT/SFT.py` | Three-map MDI-labeled initialization, grid conversion, vector-potential SFT evolution and BMR insertion | Never imported/executed wholesale. Only original omega and pre-SFT reconstruction AST nodes executed with in-memory arrays |
| Research `main.py`, `sharptools.py`, catalogue | SHARP/BMR preprocessing and source-driven evolution | Read as context; not needed for pre-SFT test |
| Research `test_*.py` | Hard-coded scientific experiments on harmonic power / inversion-line length | Not a conventional unit-test suite; not executed |
| Research PFSS scripts | Spherical harmonic PFSS and field-line plotting with missing hard-coded inputs | Separate from reconstruction, not executed |
| `SFT/synoptic_reconstruction.py` | Existing physical HMI coordinates, latitude/original rate functions, cubic interpolation and plotting | Read-only helpers reused and independently checked |
| `SFT/validate_observations.py` | JSOC querying, cached HMI images, SunPy projection, LOS/mu, shared mask | Only numerical projection/parser helpers used; all writes/network entry points avoided |
| `SFT/test_coordinate_registration.py` | Existing positive-longitude and native-sampling tests | Read; existing tests also executed separately and logged |
| `SFT/download_synoptic_maps.py` | Download and header-enrichment from JSOC | Read, not run; all required FITS already available |
| `SFT/validation_data/` | Three raw 4096x4096 HMI images, JSOC metadata, prior arrays/metrics/plots | Read-only raw inputs and reproduction controls |
| `SFT/fits_files/` | 221 HMI 720x360 synoptic maps, CR2096..2316 | Full shape/finite/checksum census; seven unique maps used in triples centered 2120/2122/2124 |
| `SFT/prepare_viewer_data.py`, `SFT/viewer/` | React/Three.js display of existing maps/metrics | Reviewed for baseline provenance, not changed or built |
| `magnetofriction/` | Empty engine/output stubs, input notes and theory Q&A | Context only; not part of numerical reconstruction |
| Root research/audit Markdown | Brief, planned scientific context and sun-layer notes | Read as task context; embedded instructions were not taken as permission to edit research files |

No AGENTS.md was found in the repository or checked parent directories. In particular, the research `Instruction.txt` suggestions to modify code are historical document content, not an override of the user's preservation rule.

The inventory found pre-existing parse errors; they are recorded without modification:

- `ananya_research_work-main/SFT/test_length_zero_line_diffusion.py`: expected an indented block after function definition on line 406 (<unknown>, line 408)
- `ananya_research_work-main/SFT/test_p_advection_diffusion.py`: expected an indented block after function definition on line 561 (<unknown>, line 563)
- `ananya_research_work-main/SFT/test_p_diffusion.py`: expected an indented block after function definition on line 381 (<unknown>, line 383)
- `magnetofriction/model_input.py`: unterminated string literal (detected at line 1) (<unknown>, line 1)

These do not block the isolated pre-SFT audit. Missing optional SunPy map extras also do not block the coordinate-frame API used here. The actual environment is Python 3.12.7, NumPy 2.5.4, SciPy 1.18.1, Astropy 7.2.3, SunPy 8.0.1, Matplotlib 3.11.2.

All 221 raw synoptic file checksums pass; all DATASUM values pass. `available_inputs.json` distinguishes Astropy's post-header-parse verification from the independent raw-byte checksum investigation. The audited seven input maps have passing normal Astropy checks too. Cached full-disk HMI image SHA-256 values match the previous reports and the supplied metadata T_REC/T_OBS exactly.

Scientific evidence retrieved during the audit: SunPy official HMI/Carrington documentation, NASA's HMI product description and JSOC-SDP synoptic source pinned to commit `0cf0b90d354705ed866fdba040772b0d712de785`. The source snapshots and provenance live in `evidence/`; they are explanatory evidence, not the historic binary pipeline proven to have produced these FITS.

Original-file preservation is checked by hashes in the automated tests and again with `inventory.py --verify`. The verification compares the original file set and flags new files outside the audit tree. The same data and scripts remain in their original locations.
