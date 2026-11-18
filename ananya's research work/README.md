I added here all the important codes that I was working on for last couple of years. So, we mainly developed two models: (a) PFSS and (b) SFT.
We also added some applications of SFT and spherical harmonics decomposition. Every details related to code as well as algorithm are mentioned 
in the coresponding '.py' and '.txt' files. To get better understanding, one should first go through the theoretical modeling before jumping 
into the codes. I will suggest you to follow my paper "Uncovering the Dominant Spatial Scales of the Sun’s Magnetic Field in Solar Cycle 24" for
PFSS and Anthony's thesis for SFT part.

Both the PFSS modeling and applications of SFT modeling were done for several carrington rorations.

## Repository guide added 18 November 2026

The supplied description above is retained. The current folder contains:

| Location | Contents |
| --- | --- |
| [PFSS/](PFSS/) | `CR_2193_80_full.py` for the harmonic/potential-field calculation and `jul80_field_line.py` for tracing from saved fields. |
| [SFT/](SFT/) | `SFT.py` surface evolution; `main.py` and `sharptools.py` for SHARP/BMR catalogue preparation; the supplied emergence catalogue, instructions, and four spatial-scale research experiments. |
| [Implementation and magnetogram-handling review](sft-implementation-and-magnetogram-handling-review.md) | Source-level explanation of equations, inputs, grids, source insertion, outputs and questions to resolve. This is a review, not a full-run validation. |

The dated experiment FITS, MDI-labelled initial maps, CR2193 PFSS input and generated model archives expected by these scripts are absent from this folder. The `test_*.py` files are computational research experiments, not lightweight unit tests. Several scripts execute substantial work when imported.

The continuation is described in [my work/README.md](<../my work/README.md>): it includes HMI acquisition, a separate pre-SFT reconstruction and its [quantitative ablation record](../my%20work/pre_sft_reconstruction/pre_sft_ablation_justification.md), plus MF study/planning. That reconstruction is not wired into this SFT solver. No magnetofrictional solver is supplied in this inherited folder. [The root overview](../README.md) connects the work areas and separates supplied models from later validation and performance tooling.
