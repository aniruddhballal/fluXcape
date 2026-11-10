"""Investigate archived CHECKSUM failures independently from header parsing.

The FITS standard checksum is the one's-complement 32-bit sum of the raw HDU,
which must equal 0xffffffff. Read bytes without Astropy repairing header cards.
"""
import json
from pathlib import Path
import numpy as np
from astropy.io import fits
from audit_core import ROOT

OUT=Path(__file__).resolve().parent


def raw_ones_complement_sum(data):
    words=np.frombuffer(data,dtype='>u4')
    total=int(words.astype(np.uint64).sum())
    while total>>32:
        total=(total&0xffffffff)+(total>>32)
    return total


def main():
    result=[]
    for path in sorted((ROOT/'SFT'/'fits_files').rglob('*.fits')):
        content=path.read_bytes()
        value=raw_ones_complement_sum(content)
        with fits.open(path,memmap=False) as hdus:
            header=hdus[0].header
            result.append({'path':path.relative_to(ROOT).as_posix(),'cr':header['CAR_ROT'],
                           'raw_file_checksum_hex':hex(value),'raw_checksum_valid':value==0xffffffff,
                           'CHECKSUM':header.get('CHECKSUM'),'DATASUM':header.get('DATASUM'),
                           'audited_input':2119<=header['CAR_ROT']<=2125})
    (OUT/'evidence'/'raw_fits_checksums.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Raw-byte checksum verification:',sum(r['raw_checksum_valid'] for r in result),'/',len(result))
    print('Audited inputs:',[(r['cr'],r['raw_checksum_valid']) for r in result if r['audited_input']])


if __name__=='__main__':
    main()
