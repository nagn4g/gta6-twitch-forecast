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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--truth-dir',type=Path)
    parser.add_argument('--truth',type=Path,help='External practice JSON; never copied into the repository')
    parser.add_argument('--input-dir',type=Path,default=Path('/home/hatch/workspace/makefun/gta6-kit/gta6-twitch-ccu-forecast-01-kit/input'))
    parser.add_argument('--calibrate',action='store_true')
    parser.add_argument('--output-dir',type=Path,help='Score saved entry outputs instead of forecasting in process')
    parser.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    if args.truth:
        practice(args)
        return
    if args.self_test:
        self_test()
    if args.truth_dir is None:
        if args.self_test:
            return
        parser.error('--truth-dir is required for practice scoring')
    if args.output_dir is None:
        args.output_dir=Path('out')
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


def practice(args):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    import main as entry
    source=json.loads(args.truth.read_text())
    cases=[json.loads(p.read_text()) for p in sorted(args.input_dir.glob('*.in'))]
    curves=[next(v for k,v in sorted(source.items()) if k.split()[0]==case['id']) for case in cases]
    assert len(cases)==4 and len(source)==4,'Calibration expects four practice launches'
    assert all(len(v)==24 and v[0]==next(r['viewers'] for r in c['known'] if r['hour']==1) for c,v in zip(cases,curves)),'Truth/input first-hour mismatch'
    if args.calibrate:
        calibrate(entry,cases,curves)
    else:
        ts,ps=[],[]
        for case,values in zip(cases,curves):
            truth={'hours':[{'hour':h,'viewers':values[h-1]} for h in range(2,25)]}
            pred=(json.loads((args.output_dir/(case['id']+'.out')).read_text())
                  if args.output_dir else entry.forecast_case(case))
            result=metrics(truth,pred)
            print(case['id'],'loss=%.6f miss=%.2f%% coverage=%.2f%%'%(result[0],result[1],100*result[2]))
            for t,p in zip(truth['hours'],pred['hours']):
                index=len(ts)+2
                ts.append(dict(t,hour=index)); ps.append(dict(p,hour=index))
        result=metrics({'hours':ts},{'hours':ps})
        print('Overall loss=%.6f miss=%.2f%% coverage=%.2f%%'%(result[0],result[1],100*result[2]))


def calibrate(entry,cases,curves):
    """Fit level regression and spline shape corrections with practice holdouts.

    Configuration selection uses all four holdout scores. Reported LOO is therefore
    a tuning diagnostic, not an independent estimate of final-launch performance.
    Sigma pooling also uses the four held-out residual curves, never fitted errors.
    """
    first=[c['known'][0]['viewers'] for c in cases]
    trend=[entry.slope(c['history_hourly'],c['day_start']) for c in cases]
    truth_g=[math.log(sum(v[5:23])/18/p) for v,p in zip(curves,first)]
    truth_s=[[math.log(y/(sum(v[5:23])/18)) for y in v] for v in curves]
    bases={h:entry.basis(h) for h in range(2,25)}
    def fit(parts,ids,ridge):
        x=[math.log(p/100000) for p in first]
        features=[[1,x[k],trend[k]*10] for k in range(4)]
        mat=[[sum(features[k][i]*features[k][j] for k in ids)+(ridge if i==j else 0) for j in range(3)] for i in range(3)]
        rhs=[sum(features[k][i]*(truth_g[k]-parts[k][0]) for k in ids) for i in range(3)]
        lc=entry.solve(mat,rhs)
        n=len(bases[2])
        mat=[[sum(bases[h][i]*bases[h][j] for k in ids for h in range(2,25))+(1 if i==j else 0) for j in range(n)] for i in range(n)]
        rhs=[sum(bases[h][i]*(truth_s[k][h-1]-parts[k][1][h-1]) for k in ids for h in range(2,25)) for i in range(n)]
        return lc,entry.solve(mat,rhs)
    best=None
    for bw in (0.2,0.3,0.5,0.7,1.0,1.5,2.0,4.0):
        for strength in (0,1,3):
            for mix,persistence in ((0,0),(0.5,0),(1,0),(0.5,0.1),(0.5,0.25),(1,0.1),(1,0.25)):
                config=(bw,strength,mix,persistence)
                parts=[entry.separated(p,t,config) for p,t in zip(first,trend)]
                for ridge in (0.001,0.01,0.03,0.1,0.3,1,10):
                    residual=[]
                    for k in range(4):
                        lc,sc=fit(parts,[i for i in range(4) if i!=k],ridge)
                        residual.append([math.log(curves[k][h-1]/first[k])-parts[k][0]-lc[0]-lc[1]*math.log(first[k]/100000)-lc[2]*trend[k]*10-parts[k][1][h-1]-sum(c*x for c,x in zip(sc,entry.basis(h))) for h in range(2,25)])
                    sigmas=[max(0.10,math.sqrt(sum(residual[k][j]**2 for k in range(4) for j in range(max(0,h-2),min(23,h+3)))/(4*len(range(max(0,h-2),min(23,h+3)))))) for h in range(23)]
                    loss=sum(2*max(t*(r-z*s),(t-1)*(r-z*s)) for rs in residual for r,s in zip(rs,sigmas) for t,z in zip(LEVELS,entry.T))/(4*23*5)
                    if best is None or loss<best[0]:
                        best=(loss,config,ridge,fit(parts,list(range(4)),ridge),sigmas,residual)
    loss,config,ridge,(lc,sc),sigmas,residual=best
    print('Practice LOO loss',loss,'config',config,'ridge',ridge)
    print('LEVEL_COEF =',tuple(round(v,9) for v in lc))
    print('SHAPE_COEF =',tuple(round(v,9) for v in sc))
    print('SIGMA =',tuple(round(v,6) for v in [0.1]+sigmas))
    for k,rs in enumerate(residual):
        heldout_loss=sum(2*max(t*(r-z*s),(t-1)*(r-z*s)) for r,s in zip(rs,sigmas) for t,z in zip(LEVELS,entry.T))/(23*5)
        coverage=sum(entry.T[0]*s<=r<=entry.T[-1]*s for r,s in zip(rs,sigmas))/23
        print('LOO',cases[k]['id'],'loss=%.6f miss=%.2f%% coverage=%.2f%%'%(heldout_loss,100*math.expm1(sum(map(abs,rs))/23),100*coverage))


if __name__ == '__main__':
    main()
