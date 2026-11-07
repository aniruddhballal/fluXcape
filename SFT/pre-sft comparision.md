For CR 2120, **Recons fixed differs less from the original map** than Recons Ananya does:

| Metric | Recons Ananya | Recons fixed |
|---|---:|---:|
| Mean difference, or bias | −0.168 G | −0.009 G |
| Mean absolute difference, or MAE | 11.728 G | 8.807 G |
| Root mean square difference, or RMSE | 37.601 G | 22.178 G |
| Pixels compared | 257,018 / 259,200 | 256,844 / 259,200 |

These are **differences from the original synoptic map**, not accuracy errors against ground truth. A smaller difference doesn’t establish which reconstruction is more accurate.

## What the two reconstructions mean

Both versions use CR 2119, 2120 and 2121 to reconstruct a map for CR 2120. Their difference is the latitude-dependent rotation rate.

**Recons Ananya** reproduces the rotation-rate expression as called during initialization in Ananya’s code:

$$
\omega_{\text{Ananya}}(\lambda)
= 0.18 - 2.3\cos^2\lambda - 1.62\cos^4\lambda
\quad \text{degrees/day}
$$

Here $\lambda$ is latitude. Her rotation function is written for **colatitude**, but her initialization passes it latitude directly.

**Recons fixed** addresses that apparent coordinate mismatch. Since colatitude $\theta=90^\circ-\lambda$, the same rotation law expressed in latitude is:

$$
\omega_{\text{fixed}}(\lambda)
= 0.18 - 2.3\sin^2\lambda - 1.62\sin^4\lambda
\quad \text{degrees/day}
$$

At the equator, the Ananya initialization expression gives **−3.74°/day**, while the fixed expression gives **+0.18°/day**.

## How each map is calculated

After choosing the rotation rate, both versions follow the same steps:

1. **Time offset:** For each longitude $\phi$, use Ananya’s reference longitude and rate:

   $$
   \Delta t = \frac{\phi-180^\circ}{13.2^\circ/\text{day}}
   $$

2. **Corrected longitude:** For each pixel, combine its longitude, time offset and latitude-dependent rate:

   $$
   \phi' = \phi + \omega(\lambda)\Delta t
   $$

3. **Source map:** Use CR 2120 if $\phi'$ remains in its longitude range. If it crosses a boundary, select the neighbouring CR map and wrap the longitude.

4. **New magnetic-field value:** Sample the selected map at the original latitude and corrected longitude using SciPy’s cubic **`RectBivariateSpline`**. The sampled value becomes $B_{\text{new}}$ for that pixel. Incomplete edge rows and coordinates outside the sampled range remain missing.

Recons Ananya reproduces her **rotation expression**, not her entire original pipeline. Both of our versions use FITS-derived coordinates and our current missing-pixel handling; her code constructs coordinate grids from array dimensions.

## How the metrics are calculated

For each pixel that has a valid value in both the original and reconstructed maps:

$$
d_i = B_{\text{reconstructed},i} - B_{\text{original},i}
$$

- **Bias** is the average of $d_i$. Positive and negative differences can cancel, so a bias near zero doesn’t mean every pixel is unchanged.
- **MAE** is the average of $|d_i|$. It measures the typical magnitude of the pixel-by-pixel change.
- **RMSE** is the square root of the average of $d_i^2$. It gives larger differences more weight.

The versions have slightly different valid-pixel counts because some reconstructed coordinates fall outside the sampled data. Missing pixels are excluded from the metrics.