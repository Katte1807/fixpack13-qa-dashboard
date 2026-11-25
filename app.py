"""FixPack 13 · Dashboard oficial provisional QA · fuente Excel local PLAN GENERAL."""
from datetime import date
from pathlib import Path
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from qa_engine import (TARGET,AUTOMATED_TARGET,START,CAPACITY,load_cases,metrics,
                       bugs_from_cases,plan_schedule,daily_tracking)

st.set_page_config(page_title='FixPack 13 | Control QA',page_icon='📊',layout='wide',initial_sidebar_state='expanded')
NAVY='#062B61'; BLUE='#155BB0'; GOLD='#F6B500'; GREEN='#16854D'; RED='#D22F3A'; ORANGE='#A6670C'
ROOT=Path(__file__).resolve().parent
SOURCE=Path(os.environ.get('QA_EXCEL_PATH',str(ROOT/'data'/'Seguimiento_FixPack13.xlsx'))).expanduser()
st.markdown(f'''<style>
[data-testid="stAppViewContainer"]{{background-color:#F5F8FC}}
[data-testid="stSidebar"]{{background-color:#EAF1F9}}
.block-container{{max-width:1550px;padding-top:1.2rem;padding-bottom:4rem}}
h1,h2,h3{{color:{NAVY}}}
.hero{{background:linear-gradient(115deg,#072C61,#145A9F);padding:25px 30px;border-radius:15px;color:white;margin-bottom:18px}}
.hero h1{{color:white!important;font-size:2.05rem;margin:6px 0}}
.hero p{{color:#D8E8FA;margin:0}}
.eyebrow{{letter-spacing:1.2px;color:#FFD556;font-size:.77rem;font-weight:800}}
.kpi{{background:#fff;border:1px solid #DEE8F4;border-radius:13px;padding:16px 16px;min-height:118px}}
.kpi .label{{font-size:.82rem;color:#586B83;font-weight:650}}
.kpi .number{{font-size:1.8rem;font-weight:800;margin:5px 0}}
.kpi .hint{{font-size:.75rem;color:#61758F}}
.flag{{background:white;padding:12px;border-left:5px solid {GOLD};border-radius:9px;margin-top:9px}}
</style>''',unsafe_allow_html=True)

def number(v):return f'{int(round(v)):,}'.replace(',','.')
def tile(label,value,hint='',color=NAVY):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="number" style="color:{color}">{value}</div><div class="hint">{hint}</div></div>',unsafe_allow_html=True)

def chart_style(fig,height=340):
    fig.update_layout(height=height,margin=dict(l=8,r=10,t=30,b=5),paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='white',font=dict(color=NAVY),legend=dict(orientation='h',y=1.13))
    return fig

st.sidebar.markdown('### 📊 FixPack 13')
st.sidebar.caption('Versión v1.4 · GitHub + Streamlit Cloud · 1.774 casos')
if st.sidebar.button('↻ Actualizar vista',use_container_width=True):st.cache_data.clear();st.rerun()
st.sidebar.caption(f'Fuente GitHub/local: data/{SOURCE.name} · primeros 1.774 casos')
if not SOURCE.is_file():
    st.error(f'No se encontró el Excel de seguimiento: {SOURCE}. Verifica que esté versionado en data/.')
    st.stop()
try:cases=load_cases(SOURCE)
except Exception as exc:
    st.error(f'No se pudo leer PLAN GENERAL: {exc}')
    st.stop()

with st.sidebar.expander('⚙️ Parámetros de planeación',expanded=False):
    target=st.number_input('Casos objetivo',min_value=1,value=TARGET,step=1)
    automated=AUTOMATED_TARGET
    st.caption(f'Automatización planificada: **{automated} casos**, fijos y asignados a Nicolás el primer día hábil. Se ignoran para esta meta las etiquetas de automatización incorrectas del archivo.')
    retest=st.slider('Reserva para retests manuales',0,40,20,5)
    reserve=st.number_input('Días hábiles de reserva',min_value=0,max_value=20,value=3)
    planned_start=st.date_input('Fecha de inicio de pruebas (editable)',value=START,format='DD/MM/YYYY')
    environment_confirmed=st.checkbox('Ambiente UAT confirmado',value=False)
    st.caption('Capacidad fija: Nicolás, Zaira, Julián, Tatiana, Paola y Edgar = 15 manuales/día; Adriana = 7/día. Nicolás: 110 automatizados en el primer día hábil y 15 manuales/día desde el segundo.')
with st.sidebar.expander('🔎 Filtros desplegables',expanded=True):
    cut=st.date_input('Fecha de corte',value=date.today())
    owner_options=sorted(set(cases['RESPONSABLE QA'])-set(['']))
    owner=st.selectbox('Analista',['Todos']+owner_options)
    module=st.selectbox('Módulo',['Todos']+sorted(set(cases['Modulo'])-set([''])))
    kind=st.selectbox('Tipo de prueba',['Todos']+sorted(set(cases['Tipo QA'])-set([''])))
    state=st.selectbox('Resultado',['Todos','Pendiente','Exitoso','Fallido','Bloqueado'])

schedule,daily,estimate=plan_schedule(planned_start,int(target),int(automated),retest/100,int(reserve))
summary=metrics(cases,cut,int(target))
base=daily[daily['Fase']=='Ejecución base']
expected=float(base.loc[base['Fecha'].le(pd.Timestamp(cut)),'Casos planeados'].sum()) if environment_confirmed else None
if environment_confirmed and expected:
    compliance=100*summary['ejecutados']/expected
    sem='🟢 Al día' if compliance>=95 else ('🟡 Atención' if compliance>=85 else '🔴 Atrasado')
else:compliance=None;sem='⚪ Pendiente de inicio UAT'

filtered=cases.copy()
if owner!='Todos':filtered=filtered[filtered['RESPONSABLE QA'].eq(owner)]
if module!='Todos':filtered=filtered[filtered['Modulo'].eq(module)]
if kind!='Todos':filtered=filtered[filtered['Tipo QA'].eq(kind)]
if state!='Todos':filtered=filtered[filtered['Estado QA'].eq(state)]

st.markdown('''<div class="hero"><div class="eyebrow">BANCO DE BOGOTÁ · CALIDAD Y ASEGURAMIENTO</div>
<h1>FixPack 13 | Seguimiento de Pruebas QA</h1>
<p>Resumen ejecutivo · Avance diario · Calidad · Bugs y bloqueos · Planeación UAT</p></div>''',unsafe_allow_html=True)
if not environment_confirmed:st.info('**El ambiente UAT aún no está confirmado.** La fecha mostrada es una simulación; la duración en días hábiles es la referencia de planeación.')
if summary['inventario_actual']!=target:
    st.caption(f"Control de selección: se han leído {number(summary['inventario_actual'])} registros iniciales, con una meta de {number(target)}. La fuente original permanece intacta.")

st.markdown('### Resumen para comité')
a=st.columns(6,gap='small')
with a[0]:tile('Meta de pruebas',number(target),'Línea base provisional')
with a[1]:tile('Ejecutados',number(summary['ejecutados']),f"{summary['avance_pct']:.1f}% del objetivo",BLUE)
with a[2]:tile('Exitosos',number(summary['exitosos']),'Resultados satisfactorios',GREEN)
with a[3]:tile('Fallidos',number(summary['fallidos']),'Requieren seguimiento',RED)
with a[4]:tile('Bloqueados',number(summary['bloqueados']),'Impedimentos activos',ORANGE)
with a[5]:tile('Bugs únicos',number(summary['bugs_unicos']),'IDs asociados a casos',RED if summary['bugs_unicos'] else NAVY)

b=st.columns(4,gap='small')
with b[0]:tile('Cumplimiento al corte',f'{compliance:.1f}%' if compliance is not None else '—',sem)
with b[1]:tile('Efectividad',f"{summary['efectividad_pct']:.1f}%" if summary['efectividad_pct'] is not None else '—','Exitosos / ejecutados')
with b[2]:tile('Duración ejecución',f"{estimate['dias_base']} días",f"Cierre base: {estimate['fin_base']:%d/%m/%Y}")
with b[3]:tile('Con contingencia',f"{estimate['dias_totales']} días",f"Cierre: {estimate['fin_total']:%d/%m/%Y}")

left,right=st.columns([1.15,1],gap='large')
with left:
    st.markdown('#### Estado de avance')
    st.progress(min(1,summary['avance_pct']/100),text=f"Avance real: {summary['avance_pct']:.1f}% · {number(summary['ejecutados'])} ejecutados")
    if expected is not None:
        st.progress(min(1,expected/target),text=f'Esperados a la fecha: {number(expected)} casos')
        st.markdown(f'**Brecha frente al plan:** {summary["ejecutados"]-expected:+.0f} casos · **Estado:** {sem}')
    else:st.caption('La comparación con el plan se activa una vez confirmada la disponibilidad UAT.')
    if summary['incidencias_sin_bug']:st.warning(f"{number(summary['incidencias_sin_bug'])} casos fallidos o bloqueados no tienen BUG asociado.")
    if summary['resultados_sin_fecha']:st.warning(f"{number(summary['resultados_sin_fecha'])} resultados no tienen FECHA EJECUCIÓN. Se muestran en KPI, no en tendencia diaria.")
with right:
    st.markdown('#### Resultados sobre la meta')
    remaining=max(0,target-summary['ejecutados']-summary['bloqueados'])
    fig=go.Figure(go.Pie(labels=['Exitosos','Fallidos','Bloqueados','Sin ejecutar'],
        values=[summary['exitosos'],summary['fallidos'],summary['bloqueados'],remaining],
        hole=.7,sort=False,textinfo='none',marker_colors=[GREEN,RED,GOLD,'#DCE6F1']))
    fig.update_layout(height=230,margin=dict(l=0,r=0,t=2,b=0),paper_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h',y=-.14),
       annotations=[dict(text=f'<b>{summary["avance_pct"]:.1f}%</b>',showarrow=False,font=dict(size=25,color=NAVY))])
    st.plotly_chart(fig,use_container_width=True)

st.markdown('### Análisis y trazabilidad')
tabs=st.tabs(['🚨 Bugs y bloqueos','📆 Avance diario','👥 Analistas','🧩 Funcionalidades','🗓️ Planeación y Gantt','📋 Casos de prueba'])
with tabs[0]:
    issues=filtered[filtered['Estado QA'].isin(['Fallido','Bloqueado'])].copy()
    st.markdown('#### Casos que requieren acción')
    c=st.columns(3)
    c[0].metric('Bloqueados con filtro',int(issues['Estado QA'].eq('Bloqueado').sum()))
    c[1].metric('Fallidos con filtro',int(issues['Estado QA'].eq('Fallido').sum()))
    c[2].metric('Sin bug informado',int(issues['BUGS'].eq('').sum()))
    show=['ID de caso','Nombre del Caso','Modulo','SubModulo / servicio','RESPONSABLE QA','Estado QA','BUGS','RESPONSABLE BANCO','RESPONSABLE DF','OBSERVACIONES ERROR']
    if issues.empty:st.info('No hay casos fallidos o bloqueados registrados con los filtros actuales.')
    else:st.dataframe(issues[show],hide_index=True,use_container_width=True,height=300)
    raw,aggregated=bugs_from_cases(filtered)
    st.markdown('#### Bugs únicos: impacto y casos asociados')
    if aggregated.empty:st.info('No hay identificadores en BUGS. La hoja contiene la columna para asociarlos cuando se reporten.')
    else:
        st.dataframe(aggregated,hide_index=True,use_container_width=True)
        st.markdown('**Relación bug ↔ caso**')
        st.dataframe(raw,hide_index=True,use_container_width=True,height=300)
    st.caption('Registro único: BUGS admite varios ID separados por comas o punto y coma. Cada bug puede afectar varios casos; se contabiliza una sola vez. Añade SEVERIDAD, ESTADO BUG y OBSERVACIONES ERROR en la misma hoja PLAN GENERAL.')

with tabs[1]:
    st.markdown('#### Seguimiento diario y acumulado')
    if not environment_confirmed:st.caption('Curva del plan simulada hasta confirmar inicio del ambiente; la ejecución diaria exige fechas reales en el Excel.')
    track=daily_tracking(filtered,daily,cut)
    if track.empty:st.info('Aún no hay fechas del plan dentro del corte seleccionado.')
    else:
        f=go.Figure()
        f.add_scatter(x=track['Fecha'],y=track['Plan acumulado'],name='Esperado',line=dict(color=BLUE,dash='dash',width=3))
        f.add_scatter(x=track['Fecha'],y=track['Real acumulado'],name='Real con fecha',line=dict(color=GREEN,width=4))
        st.plotly_chart(chart_style(f),use_container_width=True)
        st.dataframe(track,hide_index=True,use_container_width=True)
        st.download_button('Descargar avance diario CSV',track.to_csv(index=False).encode('utf-8-sig'),'avance_diario.csv','text/csv')
    st.caption('Exitosos y fallidos cuentan como ejecutados; bloqueados no. Los resultados sin fecha solo aparecen en KPI.')

with tabs[2]:
    st.markdown('#### Planeación vs. ejecución por analista')
    base_person=schedule[(schedule['Fase']=='Ejecución base') & (schedule['Fecha'].le(pd.Timestamp(cut)))].groupby('Tester')['Casos planeados'].sum()
    valid=filtered[filtered['FECHA EJECUCIÓN'].isna() | filtered['FECHA EJECUCIÓN'].le(pd.Timestamp(cut))]
    counts=valid.groupby('RESPONSABLE QA')['Estado QA'].value_counts().unstack(fill_value=0)
    ptable=pd.DataFrame(index=list(CAPACITY))
    ptable['Plan al corte']=base_person
    for col in ['Exitoso','Fallido','Bloqueado']:
        ptable[col]=counts[col] if col in counts else 0
    ptable=ptable.fillna(0)
    ptable['Ejecutados']=ptable['Exitoso']+ptable['Fallido']
    ptable['Brecha']=ptable['Ejecutados']-ptable['Plan al corte']
    ptable['Cumplimiento %']=ptable.apply(lambda r:100*r['Ejecutados']/r['Plan al corte'] if r['Plan al corte'] and environment_confirmed else None,axis=1)
    if owner!='Todos':ptable=ptable.loc[ptable.index==owner]
    st.dataframe(ptable.reset_index().rename(columns={'index':'Analista'}),hide_index=True,use_container_width=True)
    graph=go.Figure()
    graph.add_bar(x=ptable.index,y=ptable['Plan al corte'],name='Planeado',marker_color=BLUE)
    graph.add_bar(x=ptable.index,y=ptable['Ejecutados'],name='Ejecutado',marker_color=GREEN)
    graph.update_layout(barmode='group')
    st.plotly_chart(chart_style(graph),use_container_width=True)
    st.caption('El calendario está basado en capacidad compartida; reasignar casos reales exige actualizar RESPONSABLE QA en el libro.')

with tabs[3]:
    st.markdown('#### Cobertura por módulo y servicio')
    working=filtered.copy()
    working['Ejecutado']=working['Estado QA'].isin(['Exitoso','Fallido']).astype(int)
    working['Bloqueado']=(working['Estado QA']=='Bloqueado').astype(int)
    working['Fallido']=(working['Estado QA']=='Fallido').astype(int)
    bymod=working.groupby(['Modulo','SubModulo / servicio'],dropna=False).agg(
        Casos=('ID de caso','size'),Ejecutados=('Ejecutado','sum'),Fallidos=('Fallido','sum'),Bloqueados=('Bloqueado','sum')).reset_index()
    bymod['Avance %']=(100*bymod['Ejecutados']/bymod['Casos']).round(1)
    st.dataframe(bymod.sort_values(['Bloqueados','Fallidos','Casos'],ascending=False),hide_index=True,use_container_width=True,height=390)
    bytype=working.groupby('Tipo QA').size().rename('Casos en archivo').reset_index()
    st.markdown('**Tipos de prueba en el Excel provisional**')
    st.dataframe(bytype,hide_index=True,use_container_width=True)
    st.caption(f'La meta operativa de automatización es {automated}; no se iguala automáticamente al número de filas etiquetadas como Automatizado en esta versión provisional.')

with tabs[4]:
    st.markdown('#### Cronograma con contingencia')
    x=st.columns(4)
    x[0].metric('Inicio supuesto',planned_start.strftime('%d/%m/%Y'))
    x[1].metric('Fin ejecución base',estimate['fin_base'].strftime('%d/%m/%Y'))
    x[2].metric('Fin con holgura',estimate['fin_total'].strftime('%d/%m/%Y'))
    x[3].metric('Retests estimados',estimate['retests_estimados'])
    st.caption('Cambiar la fecha de inicio en el panel lateral recalcula automáticamente todo el cronograma. Festivos excluidos: 08/12/2026, 25/12/2026 y 01/01/2027. Paola sin disponibilidad: 03/12 y 07/12 de 2026. Adriana: 7 casos diarios, vacaciones desde 23/12/2026 y regreso 18/01/2027.')
    st.markdown('**Capacidad diaria por analista**')
    st.dataframe(pd.DataFrame([{'Analista':name,'Casos manuales/día':cap,'Consideración':('Automatizados día 1: 110; manuales desde día 2' if name=='Nicolas' else 'Vacaciones del 23/12 al 17/01' if name=='Adriana' else 'Ausente el 03/12 y el 07/12' if name=='Paola' else 'Capacidad estándar')} for name,cap in CAPACITY.items()]),hide_index=True,use_container_width=True)
    st.markdown('**Planeación semanal por fase**')
    week=daily.copy()
    week['Semana del']=week['Fecha'].dt.to_period('W-SUN').apply(lambda x:x.start_time.date())
    weekly=week.groupby(['Semana del','Fase'],as_index=False)[['Casos planeados','Manuales','Automatizados','Retests']].sum()
    st.dataframe(weekly,hide_index=True,use_container_width=True)
    shown=schedule[schedule['Casos planeados']>0].copy()
    if shown.empty:st.info('No existen jornadas de ejecución para la meta seleccionada.')
    else:
        shown['Fin visual']=shown['Fecha']+pd.Timedelta(days=1)
        fig=px.timeline(shown,x_start='Fecha',x_end='Fin visual',y='Tester',color='Tester',hover_data=['Casos planeados','Manuales','Automatizados'])
        fig.update_yaxes(autorange='reversed')
        fig.update_layout(showlegend=False)
        st.plotly_chart(chart_style(fig,max(370,25*len(CAPACITY)+170)),use_container_width=True)
    st.dataframe(daily,hide_index=True,use_container_width=True,height=340)
    st.download_button('Descargar planeación CSV',daily.to_csv(index=False).encode('utf-8-sig'),'planeacion_fixpack13.csv','text/csv')

with tabs[5]:
    st.markdown(f'#### Casos del Excel local · {len(filtered):,} filas filtradas')
    st.dataframe(filtered[['ID de caso','Nombre del Caso','Modulo','SubModulo / servicio','Tipo QA','RESPONSABLE QA','Estado QA','FECHA EJECUCIÓN','BUGS','OBSERVACIONES ERROR']],hide_index=True,use_container_width=True,height=450)
    st.download_button('Descargar casos filtrados CSV',filtered.to_csv(index=False).encode('utf-8-sig'),'casos_fixpack13.csv','text/csv')

with st.expander('ℹ️ Reglas de medición y publicación'):
    st.markdown('''- Se lee **PLAN GENERAL** directamente del Excel versionado en `data/`; no hay carga manual.
- **Meta oficial:** 1.774. Se leen **solo los primeros 1.774 registros válidos de PLAN GENERAL** (orden del Excel), aunque el archivo de origen tenga más; no se modifica la fuente.
- **Exitoso** y **Fallido** cuentan como ejecutados; **Bloqueado** no cuenta como ejecutado.
- Los resultados sin fecha aparecen en KPI, pero no en el gráfico diario.
- El campo **BUGS** agrupa bugs únicos y permite vincularlos con varios casos.
- **Automatización del cronograma = 110 casos fijos**, ejecutados por Nicolás en el primer día hábil; las etiquetas adicionales del Excel se conservan, pero no modifican esta meta.
- La **fecha de inicio es editable** y modifica todas las fechas y duraciones del cronograma. Paola se excluye el 3 y el 7 de diciembre de 2026, Adriana tiene 7 casos/día y está de vacaciones desde el 23/12/2026 hasta el 17/01/2027.
- Los festivos excluidos son 08/12/2026, 25/12/2026 y 01/01/2027. No se descuentan otros festivos.
- Los valores de capacidad, distribución y retests son hipótesis de planeación, no ejecución real.
- El Excel `data/Seguimiento_FixPack13.xlsx` **se incluye en el repositorio público por decisión del responsable del proyecto**; cualquier usuario podrá descargarlo y consultar su historial de cambios. Verifica que su contenido pueda publicarse.''')
