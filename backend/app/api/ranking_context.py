"""One validated set of ranking preferences for every hospital view."""
from dataclasses import dataclass
from fastapi import Query, HTTPException
from app.schemas.hospital import RankingWeights

@dataclass
class RankingContext:
    weights: RankingWeights
    lat: float | None
    lon: float | None

def ranking_context(quality:float=Query(.35,ge=0,le=1),wait_time:float=Query(.25,ge=0,le=1),distance:float=Query(.20,ge=0,le=1),satisfaction:float=Query(.10,ge=0,le=1),readmission:float=Query(.10,ge=0,le=1),lat:float|None=Query(None,ge=-90,le=90),lon:float|None=Query(None,ge=-180,le=180)):
    if (lat is None)!=(lon is None): raise HTTPException(422,'Provide both latitude and longitude.')
    if lat is None: distance=0
    if quality+wait_time+distance+satisfaction+readmission<=0: raise HTTPException(422,'Choose a nonzero priority; distance also needs a location.')
    return RankingContext(RankingWeights(quality=quality,wait_time=wait_time,distance=distance,satisfaction=satisfaction,readmission=readmission),lat,lon)
