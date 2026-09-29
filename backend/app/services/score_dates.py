"""Attach dates only to the precise evidence used by a score component."""
from app.services.freshness_service import parse_date, reporting_status

MEASURE_IDS = {'wait_time':('OP_18b',), 'satisfaction':('H_HSP_RATING_9_10',), 'readmission':('Hybrid_HWR','READM_30_HOSP_WIDE')}

def attach_score_dates(explanation, measures, presence=None):
    contributing=[]
    for component in explanation.components:
        if not component.available or component.requested_weight <= 0:
            component.date_status='not_used'
            continue
        if component.key=='distance':
            component.date_status='calculated'
            component.source_note='Calculated from your selected location and cached hospital coordinates; not a clinical reporting period.'
            continue
        if component.key=='quality':
            component.date_status='release_only' if presence and presence.present and presence.release_date else 'unknown'
            component.source_url='https://data.cms.gov/provider-data/dataset/xubh-q36u'
            component.release_date=presence.release_date if presence and presence.present else None
            component.source_note='CMS overall rating combines multiple reporting windows. The directory release date is not its clinical reporting period.'
        else:
            matches=[m for m in measures if m.measure_id in MEASURE_IDS.get(component.key,()) and abs(m.value-component.value)<0.00001]
            if len(matches)==1:
                record=matches[0]
                component.measure_id=record.measure_id
                component.period_start=record.period_start
                component.period_end=record.period_end
                component.source_url=record.source_url
                component.date_status=reporting_status(record.period_end)
            else:
                component.date_status='unknown'
                component.source_note='The stored summary cannot be tied unambiguously to a reporting period.'
        contributing.append(component)
    dates=[parse_date(c.period_end) for c in contributing if parse_date(c.period_end)]
    older=sum(c.date_status=='older_period' for c in contributing)
    unknown=sum(c.date_status in {'unknown','release_only','future_period'} for c in contributing)
    if not contributing:
        summary='No clinical measures contribute to this score.'
    else:
        summary=f"{older} contributing measure{'s' if older!=1 else ''} over 2 years old" if older else 'No dated contributing measures over 2 years old'
        if dates:
            low,high=min(dates).isoformat(),max(dates).isoformat()
            summary+=f' · Reporting periods end {low}' + (f' to {high}' if low!=high else '')
        if unknown: summary+=f" · {unknown} reporting period{'s' if unknown!=1 else ''} unknown"
    return dict(summary=summary,older_measure_count=older,unknown_period_count=unknown,oldest_period_end=min(dates).isoformat() if dates else None,newest_period_end=max(dates).isoformat() if dates else None)
