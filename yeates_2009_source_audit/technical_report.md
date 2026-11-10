**Technical report: Yeates thesis longitude-correction source audit**

The linked deposit does not supply the source code needed to answer the interpolation question. I downloaded and extracted `Accompanying software.zip`; it contains twelve MPEG movies and no source files. Consequently, the exact number of neighboring field measurements, interpolation algorithm, and implementation cannot be established from this download.

The repository's [full item record](https://research-repository.st-andrews.ac.uk/handle/10023/734?show=full) lists two attachments: `A.R. Yeates PhD thesis.pdf` and [`Accompanying software.zip`](https://research-repository.st-andrews.ac.uk/bitstream/handle/10023/734/Accompanying%20software.zip?isAllowed=y&sequence=7). Inspection of the downloaded ZIP gives this complete inventory:

```text
alphaA4.mpg       alphaL4.mpg       bbso.mpg
dynamoadv.mpg     dynamodiff.mpg    hairyA4.mpg
rope12.mpg       rope42.mpg        rope5.mpg
skewA4.mpg       surfaceA4.mpg     surfaceL4.mpg
```

All twelve entries begin with the same MPEG pack-header bytes (`00 00 01 ba`); the ZIP contains no directories or nested archives. Its CRC integrity check passes. The filenames also match Appendix A, “List of Accompanying Movies,” printed pages 178–179 (PDF pages 203–204), in the [thesis](https://research-repository.st-andrews.ac.uk/bitstream/handle/10023/734/A.R.%20Yeates%20PhD%20thesis.pdf?isAllowed=y&sequence=6#page=203). The local [archive manifest](archive_manifest.json) records each entry's size and initial bytes.

| Requested source-code result | Finding |
| --- | --- |
| Longitude-correction filename, function, and line numbers | Unavailable: no implementation source is included. |
| Interpolation filename, function, and line numbers | Unavailable for the same reason. |
| Exact neighboring-measurement count per output pixel | Cannot be determined from the supplied files. |
| Interpolation algorithm and how it works | Cannot be determined from the supplied files. |

Assigning a sample count or naming an interpolation method would therefore exceed the available source evidence. The original implementation, including any interpolation routine it calls, is required to answer these questions with code citations.

For reproducibility, the downloaded archive is **37,727,958 bytes**, with SHA-256:

```text
2a08be85b03c6339fdaa13e4bfb39ea01d91f51f12fc32ec0520991670c188ce
```
