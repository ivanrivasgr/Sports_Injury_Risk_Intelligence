import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from data.seed_data import get_injuries_df, get_weather_df


@st.cache_data
def load_data():
    return get_injuries_df(), get_weather_df()


DARK = "#F8FAFC"; BG = "#F1F5F9"; CARD = "#FFFFFF"; BORD = "#E2E8F0"
TEXT = "#475569"; HIGH = "#0F172A"; BLUE = "#1D4ED8"; GRN  = "#16A34A"
RED  = "#DC2626"; ORG  = "#D97706"; PRP  = "#6B21A8"


def section_header(label):
    st.markdown(
        f"<div style='font-family:IBM Plex Mono,monospace; font-size:0.68rem; "
        f"letter-spacing:0.12em; text-transform:uppercase; color:{BLUE}; "
        f"border-bottom:1px solid {BORD}; padding-bottom:6px; margin-bottom:14px;'>{label}</div>",
        unsafe_allow_html=True)


def uncertainty_note(text, level="approximation"):
    icons   = {"approximation":"📐","association":"🔗","incomplete":"🕳️","synthetic":"🧪"}
    colors  = {"approximation":"#92400E","association":"#1D4ED8","incomplete":"#6B21A8","synthetic":"#065F46"}
    bgs     = {"approximation":"#FEF3C7","association":"#EFF6FF","incomplete":"#F5F3FF","synthetic":"#ECFDF5"}
    borders = {"approximation":"#FCD34D","association":"#BFDBFE","incomplete":"#DDD6FE","synthetic":"#A7F3D0"}
    icon = icons.get(level,"⚠️"); color = colors.get(level,"#92400E")
    bg = bgs.get(level,"#FEF3C7"); border = borders.get(level,"#FCD34D")
    st.markdown(
        f"<div style='background:{bg};border:1px solid {border};border-radius:4px;"
        f"padding:8px 12px;margin-top:-6px;margin-bottom:14px;'>"
        f"<span style='color:{color};font-size:0.85rem;'>{icon}&nbsp;&nbsp;</span>"
        f"<span style='color:{color};font-family:IBM Plex Mono,monospace;"
        f"font-size:0.7rem;line-height:1.5;'>{text}</span></div>",
        unsafe_allow_html=True)


def kpi_card(title, value, sub, note, color=BLUE):
    return f"""<div style='background:{CARD}; border:1px solid {BORD}; border-top:3px solid {color}; border-radius:8px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,0.04);'>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.6rem; letter-spacing:0.12em; text-transform:uppercase; color:#94A3B8; margin-bottom:5px;'>{title}</div>
        <div style='font-size:1.8rem; font-weight:700; color:{color}; line-height:1;'>{value}</div>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.65rem; color:#64748B; margin-top:4px;'>{sub}</div>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.62rem; color:#92400E; margin-top:6px; border-top:1px solid #F1F5F9; padding-top:5px;'>⚠ {note}</div>
    </div>"""


def page_disclaimer():
    st.markdown(f"""
    <div style='background:#FFFBEB; border:1px solid #FCD34D; border-left:4px solid {ORG};
                border-radius:6px; padding:14px 18px; margin-bottom:22px;
                padding-left:0;'>
        <div style='font-size:1.1rem; margin-top:2px;'>⚠️</div>
        <div>
            <div style='color:#92400E; font-family:IBM Plex Mono,monospace; font-size:0.68rem;
                        letter-spacing:0.12em; text-transform:uppercase; margin-bottom:5px;'>
                Data Engineering & ML Project — Not a Medical or Causal Analysis
            </div>
            <div style='color:#78350F; font-size:0.8rem; line-height:1.6;'>
                Source: <strong>Transfermarkt</strong> public records + Real Madrid press communications.
                <strong>~30–40% of real injuries are never publicly reported.</strong>
                Venue is approximated from the last match before each report date —
                the actual moment of injury is unobservable.
                Every number is a description of <em>reported, observable data</em>, not ground truth.
                <strong>Association ≠ causation.</strong>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)


def render():
    df, _ = load_data()

    st.markdown(f"""<div style='margin-bottom:24px;'>
        <div style='font-family:IBM Plex Mono,monospace; font-size:0.6rem;
                    letter-spacing:0.18em; color:#94A3B8; text-transform:uppercase;'>
            Real Data · Transfermarkt + Press Reports · 2021–2025</div>
        <h1 style='font-size:2rem; font-weight:700; color:#0D1B2A; margin:6px 0 4px;'>
            Real Madrid Injury Dashboard <span style='color:{BLUE};'>2021–2025</span></h1>
        <p style='color:#64748B; font-size:0.85rem; max-width:660px; margin:0;'>
            Gold-layer output of the data pipeline. 88 documented events across 4 seasons.</p>
    </div>""", unsafe_allow_html=True)

    page_disclaimer()

    with st.expander("🔧 Filters", expanded=False):
        c1, c2, c3 = st.columns(3)
        seasons   = c1.multiselect("Season",   sorted(df["season"].unique()), default=sorted(df["season"].unique()))
        positions = c2.multiselect("Position", sorted(df["position"].unique()), default=sorted(df["position"].unique()))
        venues    = c3.multiselect("Last Match Venue", df["last_match_venue"].unique(), default=list(df["last_match_venue"].unique()))

    d = df[df["season"].isin(seasons) & df["position"].isin(positions) & df["last_match_venue"].isin(venues)].copy()
    if d.empty:
        st.warning("No data matches current filters."); return

    # KPIs
    c1,c2,c3,c4,c5 = st.columns(5)
    kpis = [
        ("Documented Injuries", str(len(d)), "events in dataset", "est. 30–40% more unreported", BLUE),
        ("Seasons", str(d["season"].nunique()), "2021–22 to 2024–25", "no pre-2021 data here", TEXT),
        ("Players", str(d["player_name"].nunique()), "first-team", "squad changed each season", PRP),
        ("% Muscular", f"{d['is_muscular'].mean():.0%}", "of documented", "type from press reports — imprecise", ORG),
        ("Avg Days Missed", f"{d['days_missed'].mean():.0f}", "per injury", "return dates often unpublished", RED),
    ]
    for col,(t,v,s,n,c) in zip([c1,c2,c3,c4,c5],kpis):
        col.markdown(kpi_card(t,v,s,n,c), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Row 1
    cl, cr = st.columns([3,2])
    with cl:
        section_header("Injuries per Season (documented only)")
        by_s = d.groupby(["season","is_muscular"]).size().reset_index(name="n")
        by_s["type"] = by_s["is_muscular"].map({1:"Muscular",0:"Other"})
        fig = go.Figure()
        for t,col in [("Muscular",ORG),("Other",BLUE)]:
            sub = by_s[by_s["type"]==t]
            fig.add_trace(go.Bar(x=sub["season"],y=sub["n"],name=t,marker_color=col,opacity=0.85))
        fig.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,barmode="stack",
            height=250,margin=dict(t=10,b=10,l=10,r=10),legend=dict(bgcolor=CARD,bordercolor=BORD,font=dict(color="#0F172A",size=11)),
            font_family="IBM Plex Mono",font_color=TEXT,xaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,title="# injuries",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig, use_container_width=True)
        uncertainty_note("The 2024–25 spike partly reflects improved data collection for recent seasons, not necessarily a true increase in injury rate. Earlier seasons are likely under-represented in public sources.", level="incomplete")

    with cr:
        section_header("By Injury Type (as reported in press)")
        tc = d["injury_type"].value_counts().head(8)
        fig2 = go.Figure(go.Bar(x=tc.values,y=tc.index,orientation="h",
            marker_color=[BLUE if i<3 else "#93C5FD" for i in range(len(tc))]))
        fig2.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,
            height=250,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,
            xaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig2, use_container_width=True)
        uncertainty_note("Injury type labels from Transfermarkt/press — clinical specificity varies. 'Muscle injury' is a broad category that may mask more specific diagnoses.", level="approximation")

    # Row 2
    cl2, cr2 = st.columns([2,3])
    with cl2:
        section_header("Most Affected Players (documented injuries)")
        pa = d.groupby("player_name").agg(injuries=("injury_type","count"),days_missed=("days_missed","sum"),muscular_pct=("is_muscular","mean")).sort_values("injuries",ascending=False).head(12).reset_index()
        fig3 = go.Figure(go.Bar(y=pa["player_name"],x=pa["injuries"],orientation="h",
            marker_color=[RED if v>=4 else ORG if v>=3 else BLUE for v in pa["injuries"]],
            hovertemplate="%{y}: %{x} documented injuries<extra></extra>"))
        fig3.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,
            height=370,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,
            xaxis=dict(gridcolor=BORD,title="documented injuries",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,autorange="reversed",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig3, use_container_width=True)
        uncertainty_note("High count ≠ 'injury-prone'. Players with more media coverage and longer tenure have more complete records. This ranking reflects data availability as much as injury frequency.", level="incomplete")

    with cr2:
        section_header("Days Missed per Player (bubble = injury count)")
        fig4 = go.Figure(go.Scatter(x=pa["injuries"],y=pa["days_missed"],mode="markers+text",
            text=pa["player_name"].str.split().str[-1],textposition="top center",textfont=dict(size=9,color=TEXT),
            marker=dict(size=pa["injuries"]*7+10,color=pa["muscular_pct"],
                colorscale=[[0,"#EFF6FF"],[0.5,"#D97706"],[1.0,"#DC2626"]],
                colorbar=dict(title="Muscular %",thickness=10,tickfont=dict(size=8,color=TEXT)),
                line=dict(color=BORD,width=1),opacity=0.85),
            hovertemplate="<b>%{text}</b><br>Documented injuries: %{x}<br>Documented days missed: %{y}<extra></extra>"))
        fig4.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,
            height=370,margin=dict(t=10,b=30,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,
            xaxis=dict(gridcolor=BORD,title="documented injuries",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,title="documented days missed",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig4, use_container_width=True)
        uncertainty_note("Days missed derived from published return dates. Many return dates arrive late or never — this metric likely underestimates true absence duration.", level="approximation")

    # Row 3: Heatmap
    section_header("Injury Calendar — Monthly Distribution (documented events only)")
    mnames = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly = d.groupby(["season","month"]).size().reset_index(name="n")
    pivot = monthly.pivot(index="season",columns="month",values="n").fillna(0)
    pivot.columns = [mnames[c-1] for c in pivot.columns]
    for m in mnames:
        if m not in pivot.columns: pivot[m]=0
    pivot = pivot[mnames]
    fig5 = go.Figure(go.Heatmap(z=pivot.values,x=pivot.columns.tolist(),y=pivot.index.tolist(),
        colorscale=[[0,"#EFF6FF"],[0.3,"#BFDBFE"],[0.6,"#D97706"],[1.0,"#DC2626"]],
        hovertemplate="Season:%{y} Month:%{x} Documented injuries:%{z}<extra></extra>",
        colorbar=dict(thickness=12,tickfont=dict(size=8,color=TEXT))))
    fig5.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,
        height=195,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,
        xaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
    st.plotly_chart(fig5, use_container_width=True)
    uncertainty_note("Oct–Nov peak is an observed pattern — not an established cause. It could also reflect reporting delay: injuries sustained earlier may be announced weeks later. Causal direction cannot be established from this data.", level="association")

    # Row 4: Donuts + Position
    c1,c2,c3 = st.columns(3)
    with c1:
        section_header("By Last Match Venue ⚠ Approximation")
        vc = d["last_match_venue"].value_counts()
        fig6 = go.Figure(go.Pie(labels=vc.index,values=vc.values,hole=0.6,marker_colors=[BLUE,ORG],textfont=dict(family="IBM Plex Mono",size=10)))
        fig6.update_layout(template="plotly_white",paper_bgcolor=DARK,height=210,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,legend=dict(bgcolor=CARD,bordercolor=BORD,font=dict(color="#0F172A",size=11)),annotations=[dict(text="venue*",x=0.5,y=0.5,font=dict(color=TEXT,size=9),showarrow=False)])
        st.plotly_chart(fig6, use_container_width=True)
        uncertainty_note("Venue = last match before injury report. The actual injury moment (training, travel, match) is unknown. Do NOT read this as 'injuries at Bernabéu vs away'.", level="approximation")

    with c2:
        section_header("By Competition (last match before report)")
        cc = d["competition"].value_counts()
        fig7 = go.Figure(go.Pie(labels=cc.index,values=cc.values,hole=0.6,marker_colors=[BLUE,PRP,GRN,ORG],textfont=dict(family="IBM Plex Mono",size=10)))
        fig7.update_layout(template="plotly_white",paper_bgcolor=DARK,height=210,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,legend=dict(bgcolor=CARD,bordercolor=BORD,font=dict(color="#0F172A",size=11)))
        st.plotly_chart(fig7, use_container_width=True)
        uncertainty_note("Competition of last match — not necessarily where the injury occurred. LaLiga over-representation partly reflects its larger share of total fixtures.", level="approximation")

    with c3:
        section_header("By Position (not per-player normalized)")
        pos_order = ["GK","CB","RB","LB","CM","AM","RW","LW","ST"]
        pc = d["position"].value_counts().reindex(pos_order).dropna()
        fig8 = go.Figure(go.Bar(x=pc.index,y=pc.values,marker_color=[RED if v==pc.max() else BLUE if v>pc.median() else "#BFDBFE" for v in pc.values]))
        fig8.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,height=210,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,xaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig8, use_container_width=True)
        uncertainty_note("Raw counts reflect squad size at each position. A squad with 5 CMs will naturally show more CM injuries than one with 2 GKs. Exposure-normalized rates would require full appearances data.", level="association")

    # Row 5: Severity + Age scatter
    cl3, cr3 = st.columns(2)
    with cl3:
        section_header("Severity Distribution (Days Missed — published return dates only)")
        d2 = d[d["days_missed"]>0].copy()
        d2["severity_cat"] = pd.cut(d2["days_missed"],bins=[0,7,21,60,300],labels=["Minor (≤7d)","Moderate (8–21d)","Significant (22–60d)","Severe (>60d)"])
        sc = d2["severity_cat"].value_counts().sort_index()
        fig9 = go.Figure(go.Bar(x=sc.index,y=sc.values,marker_color=[GRN,ORG,RED,"#8b0000"],opacity=0.85))
        fig9.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,height=240,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,xaxis=dict(gridcolor=BORD,tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,title="# injuries",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig9, use_container_width=True)
        n_zero = (d["days_missed"]==0).sum()
        uncertainty_note(f"{n_zero} records excluded (return date unpublished). Minor injuries are most likely to be excluded — the chart probably overstates the proportion of severe injuries.", level="incomplete")

    with cr3:
        section_header("Age at Injury vs Days Missed (OLS trend — illustrative only)")
        xv = d["age_at_injury"].values; yv = d["days_missed"].values
        z = np.polyfit(xv, yv, 1); p = np.poly1d(z)
        xs = np.linspace(xv.min(), xv.max(), 60)
        fig10 = go.Figure()
        fig10.add_trace(go.Scatter(x=xv,y=yv,mode="markers",
            marker=dict(color=d["is_muscular"].map({1:ORG,0:BLUE}),size=7,opacity=0.65,line=dict(color=BORD,width=0.5)),
            hovertemplate="Age: %{x}<br>Days missed: %{y}<extra></extra>",showlegend=False))
        fig10.add_trace(go.Scatter(x=xs,y=p(xs),mode="lines",
            line=dict(color=RED,dash="dot",width=1.5),name=f"OLS slope={z[0]:.1f} d/yr"))
        fig10.update_layout(template="plotly_white",paper_bgcolor=DARK,plot_bgcolor=BG,height=240,margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color=TEXT,xaxis=dict(gridcolor=BORD,title="Age at injury (approx.)",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor=BORD,title="Days missed",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),legend=dict(bgcolor=CARD,bordercolor=BORD,font=dict(color="#0F172A",size=11)))
        st.plotly_chart(fig10, use_container_width=True)
        uncertainty_note(f"OLS on n={len(d)} points — no significance test, no confounders controlled, age is approximate. Slope of {z[0]:.1f} d/yr is a descriptive statistic, not a causal estimate of ageing effects.", level="association")

    # Raw table
    with st.expander("📋 Raw Gold-Layer Data — injuries table"):
        cols = ["player_name","season","injury_type","date_start","date_end","days_missed","last_match_venue","competition","position","is_muscular","age_at_injury"]
        st.dataframe(d[cols].sort_values(["season","date_start"],ascending=[False,False]),use_container_width=True,hide_index=True)
        uncertainty_note("last_match_venue = venue of last match before report (approximation). days_missed=0 = return date unpublished. injury_type = press label, not clinical diagnosis.", level="approximation")

    st.markdown("---")
    st.markdown(f"""<div style='background:{CARD}; border:1px solid {BORD}; border-radius:8px; padding:18px 24px; width:100%;'>
        <div><div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{BLUE};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;'>Data Sources</div>
        <div style='color:{TEXT};font-size:0.8rem;line-height:1.8;'>Transfermarkt.us — injury records<br>Real Madrid press communications<br>FBRef — match logs<br>Open-Meteo — historical weather</div></div>
        <div><div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{ORG};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;'>What this data cannot tell you</div>
        <div style='color:{TEXT};font-size:0.8rem;line-height:1.8;'>✗ Why injuries happened<br>✗ Where exactly injuries occurred<br>✗ The ~30–40% unreported<br>✗ Any causal relationship</div></div>
        <div><div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:{GRN};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;'>What this data can tell you</div>
        <div style='color:{TEXT};font-size:0.8rem;line-height:1.8;'>✓ Patterns in reported events<br>✓ Players with more reports<br>✓ Seasonal report distribution<br>✓ How the pipeline processes data</div></div>
    </div>""", unsafe_allow_html=True)
