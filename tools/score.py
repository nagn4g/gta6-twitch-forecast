"""Exact competition metrics. Truth files: {hours: [{hour, viewers}]} ."""
import argparse
import json
import math
import sys
from pathlib import Path

LEVELS = (0.05,0.25,0.5,0.75,0.95)


def metrics(truth, prediction):
    rows = {r['hour']:r['q'] for r in prediction['hours']}
    losses, misses, covered = [], [], []
    for row in truth['hours']:
        y = math.log(max(1,row['viewers']))
        q = rows[row['hour']]
        for tau,value in zip(LEVELS,q):
            d = y-math.log(value)
            losses.append(2*max(tau*d,(tau-1)*d))
        misses.append(abs(y-math.log(q[2])))
        covered.append(q[0] <= max(1,row['viewers']) <= q[4])
    if not losses:
        raise ValueError('Truth contains no scored hours')
    return sum(losses)/len(losses),100*math.expm1(sum(misses)/len(misses)),sum(covered)/len(covered)


def self_test():
    q=[600000,800000,900000,1100000,1500000]
    result=metrics({'hours':[{'hour':2,'viewers':1000000},{'hour':3,'viewers':700000}]},
                   {'hours':[{'hour':2,'q':q},{'hour':3,'q':q}]})
    assert abs(result[0]-0.112545)<0.000001,result
    print('Rules worked example PASS: loss=%.6f'%result[0])


def loo():
    """Nested whole-launch validation, never training on the target launch."""
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    import main as entry
    truths,predictions=[],[]
    for i,launch in enumerate(entry.LAUNCHES):
        train=entry.LAUNCHES[:i]+entry.LAUNCHES[i+1:]
        config,sigmas,_=entry.fit(train)
        center=entry.blend(entry.components(launch[2][0],launch[1],train,config[0]),config[1])
        truth={'hours':[{'hour':h,'viewers':launch[2][h-1]} for h in range(2,25)]}
        pred={'hours':[{'hour':h,'q':[launch[2][0]*math.exp(center[h-1]+z*sigmas[h-1]) for z in entry.Z]} for h in range(2,25)]}
        result=metrics(truth,pred)
        print(launch[0],'loss=%.6f'%result[0])
        for t,p in zip(truth['hours'],pred['hours']):
            index=len(truths)+2
            truths.append(dict(t,hour=index));predictions.append(dict(p,hour=index))
    result=metrics({'hours':truths},{'hours':predictions})
    print('37-comparable nested LOO: loss=%.6f miss=%.2f%% coverage=%.2f%%'%(result[0],result[1],100*result[2]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truth-dir',type=Path)
    parser.add_argument('--output-dir',type=Path,default=Path('out'))
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--loo',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.loo:
        loo()
    if args.truth_dir is None:
        if args.self_test or args.loo:
            return
        parser.error('--truth-dir is required for practice scoring')
    results = []
    all_truth,all_predictions=[],[]
    for path in sorted(args.truth_dir.glob('*.out')):
        result = metrics(json.loads(path.read_text()),json.loads((args.output_dir/path.name).read_text()))
        results.append(result)
        truth=json.loads(path.read_text())
        prediction=json.loads((args.output_dir/path.name).read_text())
        by_hour={r['hour']:r for r in prediction['hours']}
        for row in truth['hours']:
            index=len(all_truth)+2
            all_truth.append(dict(row,hour=index))
            all_predictions.append(dict(by_hour[row['hour']],hour=index))
        print(path.stem,'loss=%.6f miss=%.2f%% coverage=%.2f%%'%(result[0],result[1],100*result[2]))
    if not results:
        parser.exit(2,'No truth *.out files found; practice metrics unavailable.\n')
    result=metrics({'hours':all_truth},{'hours':all_predictions})
    print('mean loss=%.6f miss=%.2f%% coverage=%.2f%%'%(result[0],result[1],100*result[2]))


if __name__ == '__main__':
    main()
