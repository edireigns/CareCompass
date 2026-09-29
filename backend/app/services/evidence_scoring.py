"""Available-evidence preference scores; normalization caps are prototype assumptions."""
import math
from app.schemas.hospital import RankingWeights

def explain_score(hospital, weights:RankingWeights, distance_miles=None):
    def value(relation,field):
        obj=getattr(hospital,relation,None)
        return getattr(obj,field,None) if obj is not None else None
    definitions=[
        ('quality','CMS overall rating',value('quality','cms_overall_rating'),'stars',5,False,'Stars ÷ 5 × 100'),
        ('wait_time','ED visit duration (historical)',value('wait_time','er_wait_minutes'),'minutes',600,True,'100 × (1 − min(minutes, 600) ÷ 600)'),
        ('distance','Straight-line distance',distance_miles,'miles',50,True,'100 × (1 − min(miles, 50) ÷ 50)'),
        ('satisfaction','Patients rating the hospital 9–10',value('experience','overall_satisfaction'),'%',100,False,'Reported percentage'),
        ('readmission','Hospital-wide readmissions',value('outcomes','readmission_rate'),'%',25,True,'100 × (1 − min(rate, 25) ÷ 25)'),
    ]
    total=sum(weights.model_dump().values())
    components=[]
    available_weight=0.0
    for key,label,raw,unit,cap,invert,formula in definitions:
        weight=getattr(weights,key)
        available=raw is not None and math.isfinite(raw) and raw>=0
        if key=='quality': available=available and 1<=raw<=5
        if key in {'satisfaction','readmission'}: available=available and raw<=100
        score=(100*(1-min(raw,cap)/cap) if invert else 100*raw/cap) if available else None
        if available: available_weight+=weight
        components.append(dict(key=key,label=label,value=raw if available else None,unit=unit,available=available,requested_weight=weight,score=score,formula=formula,effective_weight=0.0,contribution=None))
    for component in components:
        if component['available'] and available_weight>0:
            fraction=component['requested_weight']/available_weight
            component['effective_weight']=fraction
            component['contribution']=component['score']*fraction
    coverage=available_weight/total if total>0 else 0
    overall=round(sum(c['contribution'] or 0 for c in components),1) if available_weight>0 else None
    return dict(overall_score=overall,coverage_pct=round(coverage*100,1),sufficient_data=coverage>=.5,components=components)

def compute_overall_score(hospital,weights:RankingWeights,distance_miles=None):
    return explain_score(hospital,weights,distance_miles)['overall_score']

def ranking_key(summary):
    explanation=summary.score_explanation
    return (bool(explanation and explanation.sufficient_data),summary.overall_score if summary.overall_score is not None else -1)
