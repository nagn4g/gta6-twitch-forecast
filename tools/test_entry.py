"""Run isolated cases twice and check the complete entry contract."""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time


def validate(data):
    assert set(data)=={'hours'}
    assert len(data['hours'])==23
    assert sorted(r['hour'] for r in data['hours'])==list(range(2,25))
    for row in data['hours']:
        assert set(row)=={'hour','q'}
        q=row['q']
        assert len(q)==5
        assert all(type(v) in (int,float) and math.isfinite(v) and 1<=v<=1e9 for v in q)
        assert q==sorted(q)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input_dir',type=Path)
    parser.add_argument('--repeats',type=int,default=2)
    args=parser.parse_args()
    assert args.repeats>=2,'At least two runs are required to verify determinism'
    root=Path(__file__).resolve().parents[1]
    sources=sorted(args.input_dir.glob('*.in'))
    assert sources,'No case files found'
    for source in sources:
        with tempfile.TemporaryDirectory(dir=root) as directory:
            base=Path(directory)
            inputs=base/'input';inputs.mkdir()
            (inputs/source.name).write_bytes(source.read_bytes())
            env=dict(os.environ,MAKEFUN_INPUT_DIR=str(inputs),MAKEFUN_OUTPUT_DIR=str(base/'output'))
            previous=None
            timings=[]
            for repeat in range(args.repeats):
                start=time.perf_counter()
                subprocess.run([sys.executable,'-P','-s',str(root/'main.py')],env=env,check=True,timeout=8)
                elapsed=time.perf_counter()-start
                timings.append(elapsed)
                assert elapsed<=8,'case exceeded time budget'
                raw=(base/'output'/(source.stem+'.out')).read_bytes()
                assert not (base/'output'/(source.stem+'.out')).is_symlink()
                assert len(raw)<=65536
                validate(json.loads(raw))
                assert previous is None or previous==raw,'nondeterministic output'
                previous=raw
            print(source.stem,'PASS byte-identical (%d runs); max %.3fs'%(args.repeats,max(timings)))


if __name__=='__main__':
    main()
