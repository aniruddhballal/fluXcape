Yes. `synoptic_reconstruction.py` should take three consecutive Carrington rotation (CR) FITS files, visualize them, reconstruct one approximately time-aligned magnetic-field map, and display/save the result.

I'd organize it into these functions, in execution order.

## Proposed functions

| Step | Function                          | What it does                                                                                                 |
| ---- | --------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| 1    | `load_fits()`                     | Read the three FITS files (previous, current, next), including magnetic-field arrays and metadata.           |
| 2    | `validate_maps()`                 | Check dimensions, coordinate systems, units, missing pixels, and CR sequence.                                |
| 3    | `build_coordinate_grid()`         | Generate longitude \\(\phi\\) and latitude \\(\lambda\\) for each pixel using FITS metadata.                 |
| 4    | `plot_input_maps()`               | Display all three original magnetograms, with identical color scales.                                        |
| 5    | `calculate_delta_t()`             | Calculate each longitude's time offset from the chosen reference.                                            |
| 6    | `calculate_rotation_rate()`       | Calculate the differential rotation rate for each latitude.                                                  |
| 7    | `calculate_corrected_longitude()` | Calculate \\(\phi'=\phi+\omega(\lambda)\Delta t\\) for each pixel.                                           |
| 8    | `select_source_map()`             | Determine whether \\(\phi'\\) falls within the previous, current, or next CR. Wrap longitude when necessary. |
| 9    | `interpolate_field()`             | Obtain \\(B_r\\) at the corrected coordinates using linear or cubic spline interpolation.                    |
| 10   | `reconstruct_map()`               | Assemble the interpolated magnetic-field values into one output map.                                         |
| 11   | `plot_reconstruction()`           | Display the reconstructed map beside the original central CR map.                                            |
| 12   | `plot_diagnostics()`              | Visualize longitude shifts, differences, and which FITS file supplied each pixel.                            |
| 13   | `save_reconstruction()`           | Export the reconstructed field to FITS with its coordinate system, parameters, and provenance.               |
| 14   | `main()`                          | Execute the complete workflow in order.                                                                      |

## Execution flow

Three input FITS files

CR2095 · CR2096 · CR2097

`load_fits()` → `validate_maps()` → `build_coordinate_grid()`

`plot_input_maps()`

Temporal reconstruction

`calculate_delta_t()`

`calculate_rotation_rate()`

`calculate_corrected_longitude()`

`select_source_map()`

`interpolate_field()`

`reconstruct_map()`

Output and verification

`plot_reconstruction()` → `plot_diagnostics()` → `save_reconstruction()`

## Supporting our five versions

The same functions can handle all five versions by changing two parameters:

| Version | `rotation_model`      | `interpolation_method` |
| ------- | --------------------- | ---------------------- |
| v0      | `none`                | `linear`               |
| v1      | `simple`              | `linear`               |
| v2      | `snodgrass_corrected` | `linear`               |
| v3      | `ananya_original`     | `linear`               |
| v4      | `ananya_original`     | `cubic_spline`         |

Two important design choices:

1. Keep `calculate_rotation_rate()` separate from `calculate_corrected_longitude()` so we can isolate and test the coordinate inconsistency.
2. Keep reconstruction separate from validation against observations. Later, a separate `validate_reconstruction.py` can compare v0–v4 with synthetic ground truth and real observations.

Final output: One reconstructed FITS file per version, plus before/after visualizations and diagnostics.

Note that this is a proposed, more robust implementation—not a claim that Ananya's original code already performs all these checks or uses FITS metadata.