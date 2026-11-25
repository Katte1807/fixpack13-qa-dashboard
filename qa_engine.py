"""Motor de métricas y planeación FixPack 13. Sin dependencias de Streamlit."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from collections import defaultdict
import math
import re
import unicodedata
import pandas as pd

TARGET=1774
AUTOMATED_TARGET=110
START=date(2026,11,30)  # fecha de referencia, no confirmación de disponibilidad UAT
CAPACITY={'Nicolas':15,'Zaira':15,'Julian':15,'Tatiana':15,'Paola':15,'Edgar':15,'Adriana':7}
HOLIDAYS={date(2026,12,8),date(2026,12,25),date(2027,1,1)}
PAOLA_ABSENCES={date(2026,12,3),date(2026,12,7)}
ADRIANA_VAC_START=date(2026,12,23)
ADRIANA_VAC_RETURN=date(2027,1,18)


def norm(value):
    if pd.isna(value):return ''
    s=str(value).strip()
    return ''.join(c for c in unicodedata.normalize('NFKD',s.casefold()) if not unicodedata.combining(c))


def nonempty(value):
    if pd.isna(value):return ''
    return str(value).strip()


def canonical_person(s):
    key=norm(s)
    return {norm(n):n for n in CAPACITY}.get(key, nonempty(s))


def load_cases(source:Path):
    """Lee SOLAMENTE los primeros 1.774 casos con Numero de caso válido de PLAN GENERAL."""
    data=pd.read_excel(source,sheet_name='PLAN GENERAL',dtype={'BUGS':str,'Numero de caso':str})
    data.columns=[str(c).strip() for c in data.columns]
    required=['Numero de caso','Nombre del Caso','Modulo','SubModulo / servicio','GHERKIN',
              'TIPO DE PRUEBA','RESPONSABLE QA','ESTADO','BUGS','RESPONSABLE BANCO','RESPONSABLE DF']
    missing=[c for c in required if c not in data.columns]
    if missing:raise ValueError(f'PLAN GENERAL no contiene las columnas: {", ".join(missing)}')
    optional=['FECHA EJECUCIÓN','OBSERVACIONES ERROR','SEVERIDAD','ESTADO BUG']
    for c in optional:
        if c not in data:data[c]=pd.NA
    data=data[data['Numero de caso'].notna() & data['Numero de caso'].astype(str).str.strip().ne('')].head(TARGET).copy()
    for col in required+optional:
        if col!='FECHA EJECUCIÓN':data[col]=data[col].map(nonempty)
    data['FECHA EJECUCIÓN']=pd.to_datetime(data['FECHA EJECUCIÓN'],errors='coerce').dt.normalize()
    data['RESPONSABLE QA']=data['RESPONSABLE QA'].map(canonical_person)
    data['Estado QA']=data['ESTADO'].map(norm).map({'exitoso':'Exitoso','exito':'Exitoso','aprobado':'Exitoso','fallido':'Fallido','bloqueado':'Bloqueado'}).fillna('Pendiente')
    data['Tipo QA']=data['TIPO DE PRUEBA'].map(norm).map({'funcional':'Funcional','upf':'UPF','batch':'BATCH','bathc':'BATCH','automatizacion':'Automatizado','automatizado':'Automatizado'}).fillna('Sin clasificar')
    data['ID de caso']=data['Numero de caso'].astype(str).str.replace(r'\.0$','',regex=True)
    return data


def bugs_from_cases(cases):
    records=[]
    for _,row in cases.iterrows():
        raw=row['BUGS']
        if not raw:continue
        ids=[s.strip().upper() for s in re.split(r'[,;\n]+',raw) if s.strip()]
        for bug in set(ids):
            records.append({'Bug ID':bug,'Caso':row['ID de caso'],'Modulo':row['Modulo'],
                'Estado QA':row['Estado QA'],'Severidad':row['SEVERIDAD'],
                'Estado bug':row['ESTADO BUG'],'Banco':row['RESPONSABLE BANCO'],
                'DF':row['RESPONSABLE DF'],'Observación':row['OBSERVACIONES ERROR']})
    raw=pd.DataFrame(records)
    if raw.empty:return raw,pd.DataFrame(columns=['Bug ID','Casos afectados','Bloqueados','Fallidos','Módulos afectados'])
    gb=raw.groupby('Bug ID')
    agg=gb.agg(**{'Casos afectados':('Caso','nunique'),
                   'Bloqueados':('Estado QA',lambda x:int((x=='Bloqueado').sum())),
                   'Fallidos':('Estado QA',lambda x:int((x=='Fallido').sum())),
                   'Módulos afectados':('Modulo',lambda x:', '.join(sorted(set(x))))}).reset_index()
    return raw,agg.sort_values(['Bloqueados','Casos afectados'],ascending=False)


def metrics(cases,cut:date,objective:int=TARGET):
    state=cases['Estado QA'];dt=cases['FECHA EJECUCIÓN']
    effective=dt.isna() | dt.le(pd.Timestamp(cut))
    success=int((state.eq('Exitoso') & effective).sum())
    failed=int((state.eq('Fallido') & effective).sum())
    blocked=int((state.eq('Bloqueado') & effective).sum())
    executed=success+failed
    raw_bugs,bug_summary=bugs_from_cases(cases[effective])
    issue=cases[effective & state.isin(['Fallido','Bloqueado'])]
    return {'objetivo':objective,'inventario_actual':len(cases),'ejecutados':executed,'exitosos':success,
      'fallidos':failed,'bloqueados':blocked,'pendientes_objetivo':max(0,objective-executed-blocked),
      'avance_pct':100*executed/objective if objective else 0,
      'efectividad_pct':100*success/executed if executed else None,
      'bugs_unicos':len(bug_summary),'incidencias_sin_bug':int(issue['BUGS'].eq('').sum()),
      'resultados_sin_fecha':int((state.isin(['Exitoso','Fallido']) & dt.isna()).sum()),
      'resultado_futuro':int((state.isin(['Exitoso','Fallido']) & dt.gt(pd.Timestamp(cut))).sum()),
      'sin_responsable':int(cases['RESPONSABLE QA'].eq('').sum()),
      'automatizados_en_fuente':int(cases['Tipo QA'].eq('Automatizado').sum()),
      'duplicados':int(cases['ID de caso'].duplicated().sum())}


def is_workday(day:date):return day.weekday()<5 and day not in HOLIDAYS


def plan_schedule(start=START,total=TARGET,automation=AUTOMATED_TARGET,retest_pct=.2,reserve_days=3):
    """Planeación equilibrada; los analistas se apoyan al terminar su cola.
    Automatización Nicolás en el primer día hábil; 15 manuales desde el segundo.
    """
    left_manual=max(0,int(total)-min(int(total),int(automation)))
    auto=min(int(total),int(automation))
    left_retest=math.ceil(left_manual*retest_pct)
    phase='Ejecución base';buffer=int(reserve_days);d=start;workday=0;rows=[]
    for _ in range(1800):
        if not is_workday(d):d+=timedelta(days=1);continue
        workday+=1
        for person,cap_base in CAPACITY.items():
            cap=cap_base
            if person=='Paola' and d in PAOLA_ABSENCES:cap=0
            if person=='Adriana' and ADRIANA_VAC_START<=d<ADRIANA_VAC_RETURN:cap=0
            automated=auto if workday==1 and person=='Nicolas' else 0
            if automated:cap=0
            manual=retest=0
            if phase=='Ejecución base':
                manual=min(cap,left_manual);left_manual-=manual
            elif phase=='Retests':
                retest=min(cap,left_retest);left_retest-=retest
            rows.append({'Fecha':pd.Timestamp(d),'Día hábil':workday,'Fase':phase,'Tester':person,
                         'Casos planeados':manual+automated,'Manuales':manual,'Automatizados':automated,
                         'Retests':retest,'Capacidad disponible':cap})
        if phase=='Ejecución base' and left_manual==0:phase='Retests' if left_retest else 'Reserva por defectos'
        elif phase=='Retests' and left_retest==0:phase='Reserva por defectos'
        elif phase=='Reserva por defectos':
            buffer-=1
            if buffer<=0:break
        d+=timedelta(days=1)
    schedule=pd.DataFrame(rows)
    daily=schedule.groupby(['Fecha','Día hábil','Fase'],as_index=False)[['Casos planeados','Manuales','Automatizados','Retests']].sum()
    daily['Esperado acumulado']=daily['Casos planeados'].cumsum()
    base=daily[daily['Fase']=='Ejecución base']
    return schedule,daily,{'fecha_inicio':start,'fin_base':base['Fecha'].max().date(),'fin_total':daily['Fecha'].max().date(),
        'dias_base':len(base),'dias_retest':int((daily['Fase']=='Retests').sum()),
        'dias_reserva':int((daily['Fase']=='Reserva por defectos').sum()),
        'dias_totales':len(daily),'retests_estimados':math.ceil((total-automation)*retest_pct)}


def daily_tracking(cases,daily,cut):
    valid=cases['FECHA EJECUCIÓN'].notna() & cases['FECHA EJECUCIÓN'].le(pd.Timestamp(cut)) & cases['Estado QA'].isin(['Exitoso','Fallido'])
    observed=cases[valid].groupby('FECHA EJECUCIÓN')['Estado QA'].value_counts().unstack(fill_value=0)
    for col in ['Exitoso','Fallido']:
        if col not in observed:observed[col]=0
    base=daily[daily['Fase']=='Ejecución base'].set_index('Fecha')[['Casos planeados']]
    dates=base.index.union(observed.index).sort_values()
    output=pd.DataFrame(index=dates).join(base).join(observed[['Exitoso','Fallido']]).fillna(0)
    output=output.loc[output.index<=pd.Timestamp(cut)]
    output['Ejecutados']=output['Exitoso']+output['Fallido']
    output['Plan acumulado']=output['Casos planeados'].cumsum()
    output['Real acumulado']=output['Ejecutados'].cumsum()
    output['Brecha acumulada']=output['Real acumulado']-output['Plan acumulado']
    output['Cumplimiento diario %']=(100*output['Ejecutados']/output['Casos planeados'].replace(0,float('nan'))).fillna(0)
    return output.reset_index().rename(columns={'index':'Fecha','Casos planeados':'Planeado','Exitoso':'Exitosos','Fallido':'Fallidos'})
