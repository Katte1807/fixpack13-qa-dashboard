from pathlib import Path
from qa_engine import load_cases, metrics, plan_schedule
from datetime import date

def test_first_1774():
    f=Path(__file__).resolve().parents[1]/'data'/'Seguimiento_FixPack13.xlsx'
    cases=load_cases(f)
    assert len(cases)==1774
    assert int(cases['Estado QA'].eq('Pendiente').sum())==1774
    assert metrics(cases,date(2026,11,30))['ejecutados']==0

def test_schedule():
    _,_,estimate=plan_schedule()
    assert estimate['dias_base']>=1
    assert estimate['dias_totales']>=estimate['dias_base']
