import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def uncertainty_note(text, level="association"):
    icons   = {"approximation":"📐","association":"🔗","incomplete":"🕳️","synthetic":"🧪"}
    colors  = {"approximation":"#92400E","association":"#1D4ED8","incomplete":"#6B21A8","synthetic":"#065F46"}
    bgs     = {"approximation":"#FEF3C7","association":"#EFF6FF","incomplete":"#F5F3FF","synthetic":"#ECFDF5"}
    borders = {"approximation":"#FCD34D","association":"#BFDBFE","incomplete":"#DDD6FE","synthetic":"#A7F3D0"}
    icon  = icons.get(level, "⚠️")
    color = colors.get(level, "#92400E")
    bg    = bgs.get(level, "#FEF3C7")
    border= borders.get(level, "#FCD34D")
    st.markdown(
        f"<div style='background:{bg};border:1px solid {border};border-radius:4px;"
        f"padding:8px 12px;margin-top:-4px;margin-bottom:16px;'>"
        f"<span style='color:{color};font-size:0.85rem;'>{icon}&nbsp;&nbsp;</span>"
        f"<span style='color:{color};font-family:IBM Plex Mono,monospace;"
        f"font-size:0.7rem;line-height:1.5;'>{text}</span></div>",
        unsafe_allow_html=True,
    )


def score_card(score, ci_low, ci_high, label, sources_used, sources_total, ood_flag, label_coverage):
    bar_pct = int(score * 100)
    cl = int(ci_low * 100)
    ch = int(ci_high * 100)
    bar_color = "#16A34A" if score < 0.35 else "#D97706" if score < 0.65 else "#DC2626"
    dq_note   = "⚠ degraded confidence" if sources_used < sources_total else "✓ full feature set"
    dq_color  = "#D97706" if sources_used < sources_total else "#16A34A"

    # ── Card header ───────────────────────────────────────────────────────────
    ood_badge = (
        "<span style='background:#FEF2F2;color:#DC2626;font-family:IBM Plex Mono,monospace;"
        "font-size:0.62rem;padding:2px 8px;border-radius:3px;border:1px solid #FCA5A5;"
        "margin-left:10px;'>⚠ OUT-OF-DISTRIBUTION</span>"
        if ood_flag else ""
    )
    st.markdown(
        f"<div style='background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;"
        f"padding:18px 22px 6px 22px;margin-bottom:2px;"
        f"box-shadow:0 1px 3px rgba(0,0,0,0.06);'>"
        f"<span style='font-family:IBM Plex Mono,monospace;font-size:0.7rem;"
        f"letter-spacing:0.12em;text-transform:uppercase;color:#64748B;'>{label}</span>"
        f"{ood_badge}</div>",
        unsafe_allow_html=True,
    )

    # ── Bar + score number side by side via st.columns ────────────────────────
    col_bar, col_num = st.columns([4, 1])
    with col_bar:
        st.markdown(
            f"<div style='background:#FFFFFF;border-left:1px solid #E2E8F0;"
            f"border-right:1px solid #E2E8F0;padding:10px 22px 4px 22px;'>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;"
            f"color:#64748B;margin-bottom:6px;'>"
            f"POINT ESTIMATE &nbsp;·&nbsp; "
            f"<span style='color:#6B21A8;'>95% CI {cl}%–{ch}%</span></div>"
            f"<div style='background:#F1F5F9;border-radius:4px;height:26px;"
            f"position:relative;overflow:hidden;border:1px solid #E2E8F0;'>"
            f"<div style='position:absolute;top:0;bottom:0;left:{cl}%;"
            f"width:{ch - cl}%;background:#C4B5FD;opacity:0.4;'></div>"
            f"<div style='position:absolute;top:0;bottom:0;left:0;"
            f"width:{bar_pct}%;background:{bar_color};opacity:0.85;'></div>"
            f"<div style='position:absolute;top:50%;left:{min(bar_pct+2,78)}%;"
            f"transform:translateY(-50%);font-family:IBM Plex Mono,monospace;"
            f"font-size:0.78rem;font-weight:700;color:#0F172A;'>{bar_pct}%</div>"
            f"</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.58rem;"
            f"color:#94A3B8;margin-top:3px;'>0% &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;50%"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
            f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;100%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_num:
        st.markdown(
            f"<div style='background:#FFFFFF;border-right:1px solid #E2E8F0;"
            f"padding:10px 22px 4px 4px;text-align:right;'>"
            f"<div style='font-size:2.2rem;font-weight:700;color:{bar_color};"
            f"line-height:1;font-family:IBM Plex Mono,monospace;'>{bar_pct}%</div>"
            f"<div style='font-family:IBM Plex Mono,monospace;font-size:0.6rem;"
            f"color:#64748B;margin-top:2px;'>P(injury)</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    # ── Metadata row via st.columns ───────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    meta_style = (
        "background:#FFFFFF;border-left:1px solid #E2E8F0;"
        "border-right:1px solid #E2E8F0;padding:8px 22px;"
    )
    label_style = "font-family:IBM Plex Mono,monospace;font-size:0.58rem;color:#94A3B8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;"
    val_style   = "font-family:IBM Plex Mono,monospace;font-size:0.82rem;color:#0F172A;font-weight:600;"
    sub_style   = "font-family:IBM Plex Mono,monospace;font-size:0.62rem;"

    c1.markdown(
        f"<div style='{meta_style}'>"
        f"<div style='{label_style}'>Data sources</div>"
        f"<div style='{val_style}'>{sources_used} / {sources_total}</div>"
        f"<div style='{sub_style}color:{dq_color};'>{dq_note}</div>"
        f"</div>", unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div style='{meta_style}'>"
        f"<div style='{label_style}'>Label coverage</div>"
        f"<div style='{val_style}'>{int(label_coverage * 100)}%</div>"
        f"<div style='{sub_style}color:#64748B;'>est. injuries reported</div>"
        f"</div>", unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div style='{meta_style}'>"
        f"<div style='{label_style}'>Inference type</div>"
        f"<div style='{val_style}color:#D97706;'>association</div>"
        f"<div style='{sub_style}color:#64748B;'>not causal</div>"
        f"</div>", unsafe_allow_html=True,
    )

    # ── Warning footer ────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#FFFBEB;border:1px solid #E2E8F0;"
        "border-top:none;border-left:4px solid #D97706;"
        "border-radius:0 0 10px 10px;padding:8px 22px;margin-bottom:16px;'>"
        "<span style='color:#92400E;font-family:IBM Plex Mono,monospace;"
        "font-size:0.68rem;line-height:1.5;'>"
        "⚠ Conditional association estimate. Does not account for unmeasured confounders. "
        "Not a clinical risk assessment. Must not be used for individual player decisions."
        "</span></div>",
        unsafe_allow_html=True,
    )


def render():
    st.markdown("<h2>08 · ML Layer</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#FFFBEB;border:1px solid #FCD34D;border-left:4px solid #D97706;
                border-radius:6px;padding:14px 18px;margin-bottom:22px;'>
        <div style='color:#92400E;font-family:IBM Plex Mono,monospace;font-size:0.68rem;
                    letter-spacing:0.12em;text-transform:uppercase;margin-bottom:5px;'>
            Design Principle — Uncertainty is not optional
        </div>
        <div style='color:#78350F;font-size:0.83rem;line-height:1.6;'>
            Every output this system produces carries its epistemic context.
            A score without a confidence interval, a data coverage note, and an inference type label
            is an incomplete output. The goal is not to suppress uncertainty — it is to make it impossible to ignore.
        </div>
    </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🤖 Model Design","📦 Score Output Format","📈 Simulated Performance","🔍 Feature Attribution"])

    with tab1:
        st.markdown("<div class='section-header'>Model design decisions</div>", unsafe_allow_html=True)
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("""<div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:20px;'>
                <div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:#1D4ED8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;'>Option A — Binary Classifier</div>
                <div style='color:#334155;font-size:0.83rem;line-height:1.8;'>
                    <strong style='color:#0F172A;'>Task:</strong> Predict P(injury in next 7 days)<br>
                    <strong style='color:#0F172A;'>Model:</strong> Gradient Boosted Trees (XGBoost)<br>
                    <strong style='color:#0F172A;'>Label:</strong> injured_next_7d (binary)<br>
                    <strong style='color:#0F172A;'>Metric:</strong> PR-AUC (imbalanced label)<br>
                    <strong style='color:#0F172A;'>Validation:</strong> Time-series CV only<br>
                    <strong style='color:#0F172A;'>CI method:</strong> Bootstrap (n=200)
                </div>
                <div style='margin-top:14px;background:#FFFFFF;border:1px solid #BFDBFE;border-radius:4px;padding:10px;'>
                    <div style='color:#16A34A;font-family:IBM Plex Mono,monospace;font-size:0.68rem;'>✓ Interpretable via SHAP</div>
                    <div style='color:#16A34A;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>✓ Handles missing features gracefully</div>
                    <div style='color:#D97706;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>⚠ Positive label ~60–70% complete (reporting gap)</div>
                    <div style='color:#D97706;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>⚠ Ignores time-to-event information</div>
                </div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""<div style='background:#F5F3FF;border:1px solid #DDD6FE;border-radius:8px;padding:20px;'>
                <div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:#6B21A8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:14px;'>Option B — Survival Model</div>
                <div style='color:#334155;font-size:0.83rem;line-height:1.8;'>
                    <strong style='color:#0F172A;'>Task:</strong> Time-to-injury event<br>
                    <strong style='color:#0F172A;'>Model:</strong> Cox PH or Random Survival Forest<br>
                    <strong style='color:#0F172A;'>Label:</strong> (event, time) — handles censoring<br>
                    <strong style='color:#0F172A;'>Metric:</strong> C-index (concordance)<br>
                    <strong style='color:#0F172A;'>Validation:</strong> Time-stratified CV<br>
                    <strong style='color:#0F172A;'>CI method:</strong> Breslow estimator
                </div>
                <div style='margin-top:14px;background:#FFFFFF;border:1px solid #DDD6FE;border-radius:4px;padding:10px;'>
                    <div style='color:#16A34A;font-family:IBM Plex Mono,monospace;font-size:0.68rem;'>✓ Handles censored observations correctly</div>
                    <div style='color:#16A34A;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>✓ Richer signal than binary label</div>
                    <div style='color:#D97706;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>⚠ Cox PH assumes proportional hazards — likely violated</div>
                    <div style='color:#D97706;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-top:4px;'>⚠ Still subject to label incompleteness</div>
                </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br><div class='section-header'>Training / inference split — time-aware only</div>", unsafe_allow_html=True)
        st.markdown("""<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:20px;'>
            <div style='width:100%;text-align:center;'>
                <div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:5px;padding:12px;'>
                    <div style='color:#64748B;font-size:0.62rem;text-transform:uppercase;margin-bottom:4px;'>Fold 1</div>
                    <div style='color:#1D4ED8;font-size:0.8rem;'>2021–22 → 2022–23</div>
                    <div style='color:#64748B;font-size:0.68rem;margin-top:4px;'>Train → Val</div></div>
                <div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:5px;padding:12px;'>
                    <div style='color:#64748B;font-size:0.62rem;text-transform:uppercase;margin-bottom:4px;'>Fold 2</div>
                    <div style='color:#1D4ED8;font-size:0.8rem;'>2021–23 → 2023–24</div>
                    <div style='color:#64748B;font-size:0.68rem;margin-top:4px;'>Train → Val</div></div>
                <div style='background:#EFF6FF;border:1px solid #BFDBFE;border-radius:5px;padding:12px;'>
                    <div style='color:#64748B;font-size:0.62rem;text-transform:uppercase;margin-bottom:4px;'>Fold 3</div>
                    <div style='color:#1D4ED8;font-size:0.8rem;'>2021–24 → 2024–25</div>
                    <div style='color:#64748B;font-size:0.68rem;margin-top:4px;'>Train → Val</div></div>
                <div style='background:#F3E8FF;border:2px solid #C4B5FD;border-radius:5px;padding:12px;'>
                    <div style='color:#6B21A8;font-size:0.62rem;text-transform:uppercase;margin-bottom:4px;'>Hold-out</div>
                    <div style='color:#6B21A8;font-size:0.8rem;'>Most recent season</div>
                    <div style='color:#DC2626;font-size:0.68rem;margin-top:4px;'>Final eval ONLY</div></div>
            </div>
            <div style='color:#64748B;font-family:IBM Plex Mono,monospace;font-size:0.68rem;text-align:center;margin-top:12px;'>
                ← No data from the future leaks into any training window. No exceptions. →</div>
        </div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("<div class='section-header'>What every model output must include</div>", unsafe_allow_html=True)
        st.markdown("""<div style='color:#475569;font-size:0.85rem;line-height:1.6;max-width:680px;margin-bottom:20px;'>
            A score alone is not an output. Every prediction leaving the pipeline must carry four pieces of context:
            the confidence interval, the number of sources available at inference time,
            the estimated label coverage in training data, and an explicit inference type declaration.
            Without these, the number is misleading by design.
        </div>""", unsafe_allow_html=True)

        st.markdown("<div class='section-header'>Three simulated scenarios</div>", unsafe_allow_html=True)
        scenarios = [
            dict(score=0.71,ci_low=0.58,ci_high=0.81,label="Player A · High Workload · Full Feature Set",sources_used=6,sources_total=8,ood_flag=False,label_coverage=0.65),
            dict(score=0.38,ci_low=0.21,ci_high=0.55,label="Player B · Moderate Workload · Pitch Data Missing",sources_used=4,sources_total=8,ood_flag=False,label_coverage=0.65),
            dict(score=0.44,ci_low=0.18,ci_high=0.70,label="Player C · Out-of-Distribution (new signing, no history)",sources_used=3,sources_total=8,ood_flag=True,label_coverage=0.65),
        ]
        for s in scenarios:
            score_card(**s)

        uncertainty_note("These are simulated scores. No real model has been trained on this dataset. The CI width and OOD flag demonstrate what a production output should communicate, not real uncertainty estimates.", level="synthetic")

        st.markdown("<br><div class='section-header'>Score object schema (Feature Store output)</div>", unsafe_allow_html=True)
        st.markdown("""
<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;
            padding:20px 24px;font-family:IBM Plex Mono,monospace;font-size:0.75rem;
            line-height:1.8;color:#1E293B;'>
<span style='color:#94A3B8;'>{</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"player_id"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"uuid-xxxx"</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"match_id"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"uuid-yyyy"</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"anchor_ts"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"2024-11-03T20:00:00Z"</span>,<br>
<br>
&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// Point estimate</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"injury_risk_score"</span>:&nbsp;&nbsp;<span style='color:#1D4ED8;'>0.71</span>,<br>
<br>
&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// Uncertainty envelope — REQUIRED, not optional</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"ci_95_low"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#1D4ED8;'>0.58</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"ci_95_high"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#1D4ED8;'>0.81</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"ci_method"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"bootstrap_n200"</span>,<br>
<br>
&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// Data quality context — REQUIRED</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"sources_available"</span>:&nbsp;&nbsp;<span style='color:#1D4ED8;'>6</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"sources_total"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#1D4ED8;'>8</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"missing_sources"</span>:&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#94A3B8;'>&#91;</span><span style='color:#0F766E;'>"pitch_conditions"</span>, <span style='color:#0F766E;'>"gps_workload"</span><span style='color:#94A3B8;'>&#93;</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"label_coverage_est"</span>: <span style='color:#1D4ED8;'>0.65</span>,<br>
<br>
&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// Inference context — REQUIRED</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"inference_type"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"association"</span>,&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// never "causal"</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"ood_flag"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#1D4ED8;'>false</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"model_version"</span>:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"injury_classifier_v1"</span>,<br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"feature_version"</span>:&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"player_workload_v1"</span>,<br>
<br>
&nbsp;&nbsp;<span style='color:#64748B;font-style:italic;'>// Hard constraint</span><br>
&nbsp;&nbsp;<span style='color:#6B21A8;'>"use_restriction"</span>:&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#0F766E;'>"research_and_pipeline_design_only"</span><br>
<span style='color:#94A3B8;'>}</span>
</div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='section-header'>Simulated model performance (illustrative only)</div>", unsafe_allow_html=True)
        uncertainty_note("All values below are synthetic — generated from a random seed, not a trained model. They illustrate output format, not real performance.", level="synthetic")

        np.random.seed(42); n=500
        true_labels = np.random.choice([0,1],n,p=[0.88,0.12])
        scores = np.where(true_labels==1,np.random.beta(4,2,n),np.random.beta(1.5,5,n))
        from sklearn.metrics import roc_curve, precision_recall_curve, auc
        fpr,tpr,_ = roc_curve(true_labels,scores); roc_auc=auc(fpr,tpr)
        prec,rec,_ = precision_recall_curve(true_labels,scores); pr_auc=auc(rec,prec)

        c1,c2,c3=st.columns(3)
        c1.markdown(f"""<div class='metric-card'><h4>AUC-ROC</h4><div class='value'>{roc_auc:.3f}</div>
            <div class='sub'>synthetic · not real</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:#5a4020;margin-top:6px;'>⚠ real dataset too small to estimate</div></div>""", unsafe_allow_html=True)
        c2.markdown(f"""<div class='metric-card'><h4>PR-AUC</h4><div class='value'>{pr_auc:.3f}</div>
            <div class='sub'>baseline ~0.12 (class freq)</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:#5a4020;margin-top:6px;'>⚠ label incompleteness biases down</div></div>""", unsafe_allow_html=True)
        c3.markdown(f"""<div class='metric-card'><h4>Label Coverage</h4><div class='value'>~65%</div>
            <div class='sub'>est. injuries reported</div>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.62rem;color:#5a4020;margin-top:6px;'>⚠ true positive rate underestimated</div></div>""", unsafe_allow_html=True)

        fig = make_subplots(rows=1,cols=2,subplot_titles=["ROC Curve (synthetic)","Precision-Recall (synthetic)"])
        fig.add_trace(go.Scatter(x=fpr,y=tpr,mode="lines",line=dict(color="#1D4ED8",width=2),name=f"ROC AUC={roc_auc:.3f}"),row=1,col=1)
        fig.add_trace(go.Scatter(x=[0,1],y=[0,1],mode="lines",line=dict(color="#CBD5E1",dash="dot"),showlegend=False),row=1,col=1)
        fig.add_trace(go.Scatter(x=rec,y=prec,mode="lines",line=dict(color="#16A34A",width=2),name=f"PR AUC={pr_auc:.3f}"),row=1,col=2)
        fig.add_hline(y=0.12,line=dict(color="#CBD5E1",dash="dot"),annotation_text="random baseline",row=1,col=2)
        fig.update_layout(template="plotly_white",paper_bgcolor="#F8FAFC",plot_bgcolor="#F1F5F9",height=300,
            margin=dict(t=30,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color="#0F172A",
            legend=dict(bgcolor="#FFFFFF",bordercolor="#E2E8F0"))
        fig.update_xaxes(gridcolor="#E2E8F0"); fig.update_yaxes(gridcolor="#E2E8F0")
        st.plotly_chart(fig, use_container_width=True)
        uncertainty_note("A real model trained on 88 injury records would have extremely wide confidence intervals and should not be deployed. Minimum viable training set is estimated at 500+ labeled events.", level="synthetic")

    with tab4:
        st.markdown("<div class='section-header'>SHAP feature attribution — illustrative, synthetic data</div>", unsafe_allow_html=True)
        feats = {"workload_14d":0.28,"congestion_tier":0.22,"days_since_last_match":0.17,
                 "workload_30d":0.13,"age":0.09,"competition_tier":0.06,"temperature_c":0.03,"surface_type_enc":0.02}
        sf = sorted(feats.items(),key=lambda x:x[1]); names,vals=zip(*sf)
        fig2 = go.Figure(go.Bar(x=vals,y=names,orientation="h",
            marker_color=["#6B21A8" if v>0.15 else "#A855F7" if v>0.06 else "#DDD6FE" for v in vals]))
        fig2.update_layout(template="plotly_white",paper_bgcolor="#F8FAFC",plot_bgcolor="#F1F5F9",height=300,
            margin=dict(t=10,b=10,l=10,r=10),font_family="IBM Plex Mono",font_color="#0F172A",
            xaxis=dict(gridcolor="#E2E8F0",title="Mean |SHAP value| (synthetic)",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')),yaxis=dict(gridcolor="#E2E8F0",tickfont=dict(color='#334155',size=11),title_font=dict(color='#334155')))
        st.plotly_chart(fig2, use_container_width=True)
        uncertainty_note("SHAP values are hand-crafted for illustration. On real data these rankings would shift with wide standard errors. High SHAP importance reflects association in observed data — not causal effect.", level="synthetic")

        st.markdown("""<div style='background:#F8FAFC;border:1px solid #E2E8F0;border-radius:6px;padding:16px 20px;margin-top:4px;'>
            <div style='font-family:IBM Plex Mono,monospace;font-size:0.68rem;color:#6B21A8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;'>How SHAP is used in this system</div>
            <div style='width:100%;'>
                <div><div style='color:#16A34A;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-bottom:6px;'>✓ Permitted uses</div>
                <ul style='color:#15803D;font-size:0.8rem;line-height:1.8;padding-left:16px;margin:0;'>
                    <li>Model auditing and debugging</li><li>Feature engineering iteration</li>
                    <li>Detecting data leakage</li><li>Communicating what the model learned</li></ul></div>
                <div><div style='color:#DC2626;font-family:IBM Plex Mono,monospace;font-size:0.68rem;margin-bottom:6px;'>✗ Not permitted uses</div>
                <ul style='color:#B91C1C;font-size:0.8rem;line-height:1.8;padding-left:16px;margin:0;'>
                    <li>Concluding causation from importance</li><li>Individual player decisions</li>
                    <li>Policy recommendations without expert review</li>
                    <li>Any external communication without disclaimer</li></ul></div>
            </div>
        </div>""", unsafe_allow_html=True)