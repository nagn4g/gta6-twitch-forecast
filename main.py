"""Deterministic launch analog forecast; factual curves attributed to SullyGnome."""
import json
import math
import os
from datetime import datetime
from pathlib import Path

# Release-day hourly means from the kit's SullyGnome comparables. No practice truth.
LAUNCHES = [["007 First Light",-0.1241751,[127800,103323,73369,71379,66479,59204,45074,48236,49459,47403,50542,52659,68821,83350,98296,106295,117579,135532,167655,196150,186210,161994,134225,149242]],["ARC Raiders",0.02263421,[1410,1079,1522,1799,1845,1733,3100,6916,17081,94344,206814,244738,271465,293730,298783,316460,346834,351641,366272,359179,328796,330746,321777,299499]],["Assassin's Creed Shadows",0.04504002,[146993,150026,100270,58619,54063,52006,45046,50231,56102,68976,75622,84053,96525,108936,108659,108657,150408,138015,142676,145238,126550,125560,153787,129905]],["Baldur's Gate 3",-0.15052017,[3447,2628,2717,2017,1243,873,1401,2079,3242,3882,4447,6586,37242,68216,136881,298811,419017,462928,460259,454418,423422,356170,320006,269169]],["Battlefield 6",-0.0887482,[2470,2415,2305,2207,1776,1517,1982,3812,5629,7498,10170,13304,25059,54119,139418,480363,544918,557115,563617,508306,443847,386247,325809,281673]],["Black Myth: Wukong",0.04618132,[4941,15465,129864,179550,179798,172951,178246,179393,181648,181518,188907,220328,271320,302508,340425,332501,377607,400885,230726,191591,400869,454807,388384,323886]],["Borderlands 4",-0.0714951,[133568,224179,143612,93747,90277,79272,77739,73714,64358,55895,66393,69615,67770,75580,86197,92143,100848,108514,131750,137965,140197,124277,133261,155510]],["Call of Duty: Black Ops 6",-0.08480004,[139097,126603,117395,117492,159470,179313,176167,174795,166187,157303,155765,152862,166957,182681,211191,253172,284982,317858,361816,372096,351387,381046,366243,357618]],["Call of Duty: Black Ops 7",-0.060395,[79207,68712,62687,61208,60302,66229,70891,73515,72489,74357,76210,76648,79710,82232,92235,107458,126199,123951,141296,141288,134739,148277,152696,126886]],["Call of Duty: Modern Warfare 4",-0.09558542,[59162,57358,53981,50378,51377,56437,57916,58049,59064,56370,54913,57859,72935,88100,98391,110272,115444,122180,142084,140306,141578,142945,140372,133813]],["Call of Duty: Modern Warfare III",0.00970562,[114417,102746,96139,85820,85473,113200,127871,132441,124353,123517,124169,123310,119767,127213,144066,139918,145742,154495,163279,167353,184179,196264,192781,181532]],["Clair Obscur: Expedition 33",-0.07388994,[10639,8083,5001,5601,5524,4178,7043,20896,27234,34521,35007,41283,56687,73811,86835,84611,89843,92476,108209,118507,110598,105380,88289,74423]],["Cyberpunk 2077",-0.07962166,[851999,1069278,995577,850031,699555,602023,498033,438312,383905,367829,375572,403060,487807,564272,643269,784869,816409,835993,799197,766621,802592,742566,640580,465734]],["DOOM: The Dark Ages",-0.1612946,[50351,49227,35314,24889,23489,23969,25076,30138,29874,25584,24927,29188,35120,45972,58653,64232,69540,69955,82460,68298,59283,53008,48334,52442]],["Death Stranding 2: On the Beach",-0.13622692,[42221,33279,29569,31536,33126,33289,33493,34049,30861,29408,27474,32386,39328,47959,58888,67074,65266,72219,68823,65201,63084,58986,43911,41894]],["Diablo IV",0.01427399,[533455,530948,503876,472870,442758,410241,406382,435375,458980,486331,502541,526706,529750,556614,565994,593747,641676,673808,667235,659542,641086,611591,562471,511985]],["ELDEN RING",0.0058364,[875155,801446,702720,601715,574451,554129,530371,483325,462126,464263,485314,497332,541078,604672,662454,723256,778472,800143,833065,783355,786696,749953,681368,631975]],["Elden Ring Nightreign",0.67554958,[319909,281672,221580,243654,205943,162686,154408,157688,153862,152990,160002,155941,170146,189579,212750,251328,285319,313194,318853,303083,295823,290326,280103,262159]],["FINAL FANTASY VII REBIRTH",0.02281579,[53526,56862,48523,44124,44756,59660,55981,50431,44430,41996,45400,49334,56691,63196,70973,74736,71545,73795,80201,108373,119842,115321,97219,70124]],["Forza Horizon 5",0.14332316,[43895,30550,21402,19309,13099,13811,19604,21590,20922,27838,34385,40692,38930,32290,34107,48414,53919,59906,48365,56133,57963,70132,85143,52167]],["Forza Horizon 6",-0.13878598,[26312,19771,19947,19406,23263,25764,25222,25029,26270,29142,32817,38248,44558,53985,58325,67862,63652,66850,87179,125867,139327,118158,112256,64273]],["Ghost of Tsushima",0.00436283,[131910,108753,95323,85486,124326,141038,124670,118567,116307,111938,116648,120672,149818,182632,204887,217971,233567,257298,270268,296147,297240,286950,276745,268908]],["Ghost of Yōtei",-0.17043854,[27206,18855,8251,11370,21853,24871,28298,31468,36051,36094,36331,39916,53510,63292,72404,73932,75229,97895,96013,93905,98353,95311,87610,93764]],["HELLDIVERS 2",0.27614183,[419,256,76,88,97,161,314,496,3366,25104,37602,40452,47599,59831,72075,75928,69547,94337,101451,135090,145323,141693,127007,120111]],["Halo Infinite",0.21534423,[20526,25209,25238,26289,25597,24523,23463,15495,12047,12262,9742,7976,5921,6166,5873,7207,10561,32030,116250,177911,178864,143458,125755,98220]],["Hogwarts Legacy",-0.01908177,[387358,343540,240332,206025,196331,182564,167667,182593,168165,180767,185439,198925,236314,323013,350276,339925,495060,504995,487760,448784,465689,473456,479390,431354]],["Hollow Knight: Silksong",0.16283409,[164,90,91,101,121,137,181,205,486,2869,3781,5397,15177,84185,331898,347773,336616,335439,307362,284160,263805,242822,217429,178413]],["Kingdom Come: Deliverance II",-0.40209115,[414,556,725,890,1055,1175,1274,1620,3350,6081,6470,11330,15485,18551,25048,91063,284150,372658,390855,408919,457359,402929,318844,266445]],["Marathon",-0.0658944,[1393,1077,534,613,406,411,406,434,480,521,546,613,866,1254,2374,9868,18124,42919,155173,169074,159261,152709,128302,118344]],["Marvel Rivals",0.56602068,[165939,217796,232319,210065,179058,162853,137564,121023,108186,92784,78673,79684,83059,95166,104568,114678,125459,136425,140250,138319,241299,267048,187032,139748]],["Monster Hunter Wilds",-0.01208997,[152314,125382,106536,103872,95137,268922,341332,337057,334126,336903,326066,326278,351525,382873,400695,402550,391290,383222,387694,367167,354951,355276,339833,317580]],["Resident Evil Requiem",-0.08215652,[46345,40190,33088,41692,56465,161815,211719,213498,197268,195552,205288,223126,256252,291819,327085,396788,423526,464981,536372,562811,531986,465856,423991,381249]],["Saros",-0.37511112,[6400,5577,4823,4694,3935,4858,7344,8211,8377,7333,10481,10839,16598,20263,28054,32337,30747,34715,36036,33159,32111,31724,23077,18162]],["Starfield",0.01250152,[156828,166355,164663,144040,96754,89498,80184,87544,77817,66657,56078,57464,92738,90671,91201,86663,90366,97814,108281,110518,101721,102875,113449,110634]],["Stellar Blade",-0.07897286,[27057,21168,12896,14044,25119,26925,17080,15745,20094,22208,23369,27820,30183,35207,57521,73663,70163,71371,91985,87836,86181,83651,75783,66781]],["The Last of Us Part II",0.05444674,[365019,269441,195646,166186,259030,243461,218913,200413,184445,177586,184121,214184,261016,304149,357312,391414,437142,452883,478046,488329,466235,419207,425927,426550]],["The Legend of Zelda: Tears of the Kingdom",0.06380046,[129948,108228,86621,66537,139947,151282,149761,137757,133313,150319,166642,193032,212895,248661,291198,293987,329230,338112,346283,343496,322754,298676,283571,247201]]]
Z = (-1.645, -0.674, 0.0, 0.674, 1.645)
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)


def slope(rows, start, key="from"):
    """Log change per hour over the final six pre-launch hours."""
    points = []
    origin = datetime.fromisoformat(start.replace("Z", "+00:00"))
    for row in sorted(rows, key=lambda r: r[key]):
        t = (datetime.fromisoformat(row[key].replace("Z", "+00:00")) - origin).total_seconds() / 3600
        if -6 <= t < 0 and row.get("viewers") is not None:
            points.append((t, math.log(max(1, row["viewers"]))))
    if len(points) < 2:
        return 0.0
    x = sum(p[0] for p in points) / len(points)
    y = sum(p[1] for p in points) / len(points)
    return sum((a-x)*(b-y) for a,b in points) / max(1e-9, sum((a-x)**2 for a,b in points))


def components(level, trend, library, bandwidth):
    weights = [math.exp(-0.5*((math.log(a[2][0]/level)/bandwidth)**2 + ((a[1]-trend)/0.5)**2)) for a in library]
    weights = [max(1e-12,w) for w in weights]
    # Water filling caps normalized influence while preserving relative similarity.
    cap = max(0.25,1/len(library))
    remaining = list(range(len(weights)))
    normalized = [0.0]*len(weights)
    mass = 1.0
    while remaining:
        total = sum(weights[i] for i in remaining)
        saturated = [i for i in remaining if mass*weights[i]/total > cap+1e-12]
        if not saturated:
            for i in remaining:
                normalized[i] = mass*weights[i]/total
            break
        for i in saturated:
            normalized[i] = cap
            mass -= cap
        remaining = [i for i in remaining if i not in saturated]
    weights = normalized
    analog = [sum(w*math.log(a[2][h]/a[2][0]) for w,a in zip(weights,library)) for h in range(24)]
    # OLS through the origin in log time: r(h) = b log(h) + c log(h)^2.
    xs = [math.log(h) for h in range(2,25)]
    s2,s3,s4 = [sum(x**k for x in xs) for k in (2,3,4)]
    t1 = sum(x*y for x,y in zip(xs,analog[1:]))
    t2 = sum(x*x*y for x,y in zip(xs,analog[1:]))
    det = s2*s4-s3*s3
    b,c = (t1*s4-t2*s3)/det, (t2*s2-t1*s3)/det
    param = [0.0]+[b*x+c*x*x for x in xs]
    return analog,param


def blend(parts, mix):
    a,p = parts
    wa,wp = mix
    return [wa*x+wp*y for x,y in zip(a,p)]


def fit(library):
    """Choose blend by whole-launch holdouts; retain only held-out residuals."""
    if len(library) < 3:
        return (1.0,(0.8,0.2)), [0.35]*24, None
    best = None
    for bandwidth in (0.5,1.0,2.0):
        parts = [components(a[2][0],a[1],library[:i]+library[i+1:],bandwidth) for i,a in enumerate(library)]
        for mix in ((1.0,0.0),(0.8,0.2),(0.6,0.4),(0.8,0.0),(0.6,0.2)):
            residuals = [[math.log(a[2][h]/a[2][0])-v for h,v in enumerate(blend(p,mix))] for a,p in zip(library,parts)]
            error = sum(abs(r[h]) for r in residuals for h in range(1,24))/(23*len(library))
            candidate = (error,bandwidth,mix,residuals)
            if best is None or candidate[:3] < best[:3]:
                best = candidate
    error,bandwidth,mix,residuals = best
    all_errors = [r[h] for r in residuals for h in range(1,24)]
    mean = sum(all_errors)/len(all_errors)
    pooled = sum((v-mean)**2 for v in all_errors)/(len(all_errors)-1)
    sigmas = [0.10]
    for h in range(1,24):
        lo,hi = max(1,h-2),min(24,h+3)
        values = [r[j] for r in residuals for j in range(lo,hi)]
        # Equal launch weights; shrink local residual SD towards pooled error.
        local_mean = sum(values)/len(values)
        variance = (sum((v-local_mean)**2 for v in values)+12*pooled)/(len(values)-1+12)
        sigmas.append(max(0.10,math.sqrt(variance)))
    return (bandwidth,mix),sigmas,error


def forecast_case(case, model=None):
    first = next((r.get("viewers") for r in case.get("known",[]) if r.get("hour")==1 and r.get("viewers") is not None),None)
    if first is None:
        history = sorted(case.get("history_hourly",[]),key=lambda r:r["from"])
        before = [r for r in history if r["from"] < case["day_start"] and r.get("viewers") is not None]
        first = before[-1]["viewers"] if before else 1
    level = max(1,first)
    library = [a for a in LAUNCHES if a[0] != case.get("game",{}).get("name")]
    config,sigmas,_ = model or fit(library)
    center = blend(components(level,slope(case.get("history_hourly",[]),case["day_start"]),library,config[0]),config[1]) if library else [0.0]*24
    return {"hours":[{"hour":h,"q":[min(1e9,max(1.0,math.exp(min(math.log(1e9),math.log(level)+center[h-1]+z*sigmas[h-1])))) for z in Z]} for h in range(2,25)]}


def main():
    output = Path(os.environ.get("MAKEFUN_OUTPUT_DIR","/output"))
    output.mkdir(parents=True,exist_ok=True)
    for path in sorted(Path(os.environ.get("MAKEFUN_INPUT_DIR","/input")).glob("*.in")):
        result = forecast_case(json.loads(path.read_text()))
        (output/(path.stem+".out")).write_text(json.dumps(result,separators=(",",":"),allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
