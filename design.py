"""Life Quest design system ("Warm glow" with Inter Tight).

All custom styling lives here. Screens call apply_styles() once (app.py does it)
and use the small HTML helpers below instead of writing their own <style> blocks.
Rules and rationale: docs/design.md
"""
import html
from datetime import date

import streamlit as st

# Keep these in sync with .streamlit/config.toml.
INK = "#2B2330"
MUTED = "#7A6E7E"
PAGE = "#FFF9F4"
SURFACE = "#FFFFFF"
ACTION = "#D4551F"       # buttons, checks: white text passes contrast
GLOW = "#FF8A4C"         # bright orange for fills and highlights, never for text
GROWTH = "#7CC394"       # sprout / success green
LINE = "#F1E4DA"

# One soft colour per pillar: (background, strong) — strong is used for heatmaps and dots.
PILLAR_COLORS = {
    "Adventure": ("#DDEEFB", "#5B9FD6"),
    "Finance": ("#FFF1C9", "#D9A521"),
    "Fitness": ("#FFE3D1", "#FF8A4C"),
    "Health": ("#DDF2E3", "#4FAA72"),
    "Languages": ("#E7E3FA", "#8A78E0"),
    "Personal Growth": ("#F9E1EC", "#D9739F"),
    "Social": ("#FFE0E0", "#E86A6A"),
}
DEFAULT_PILLAR = ("#FFF1E6", GLOW)

HERO_GRADIENTS = {
    "peach": "linear-gradient(140deg,#FFB27F 0%,#FFD0A3 55%,#F9C4DA 100%)",
    "lilac": "linear-gradient(140deg,#CFC3F7 0%,#F4C6DD 100%)",
    "mint": "linear-gradient(140deg,#BFE6CB 0%,#F3F0C4 100%)",
}

_CSS = """
<style>
/* ---------- Page ---------- */
.stMainBlockContainer {max-width:720px; padding-top:2.25rem; padding-bottom:128px;}
h1 {letter-spacing:-0.025em; line-height:1.05 !important;}
[data-testid="stCaptionContainer"] {color:%(muted)s;}

/* ---------- Surfaces: tiles, expanders, bordered containers ---------- */
div[data-testid="stMetric"], div[data-testid="stExpander"] details {
  background:%(surface)s; border:0; border-radius:22px;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45);
}
div[data-testid="stMetric"] {padding:14px 16px;}
div[data-testid="stMetricValue"] {font-weight:600;}
div[data-testid="stExpander"] details summary {padding:14px 16px;}
div[data-testid="stForm"] {background:%(surface)s; border:0; border-radius:24px; padding:20px;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45);}
div[data-testid="stDataFrame"] {border-radius:18px; overflow:hidden; border:1px solid %(line)s;}

/* ---------- Inputs and buttons ---------- */
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"] {
  background:%(surface)s !important; border:1px solid %(line)s !important; border-radius:14px !important;}
div.stButton > button, div.stFormSubmitButton > button {min-height:46px; font-weight:600; padding:0 22px;}
div.stButton > button[kind="secondary"], div.stFormSubmitButton > button[kind="secondary"] {
  background:%(surface)s; border:1px solid %(line)s;}

/* ---------- Tabs as pills ---------- */
div[data-baseweb="tab-list"] {gap:6px; background:%(surface)s; padding:4px; border-radius:999px; width:fit-content;}
button[data-baseweb="tab"] {border-radius:999px; padding:6px 14px; height:auto;}
button[data-baseweb="tab"][aria-selected="true"] {background:#FFE6D4;}
div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {display:none;}

/* ---------- Quest rows ---------- */
@keyframes quest-enter {from {opacity:0; transform:translateY(8px);} to {opacity:1; transform:none;}}
div[class*="st-key-quest_row_"], div[class*="st-key-team_row_"] {
  background:%(surface)s; border-radius:18px; padding:10px 14px;
  box-shadow:0 6px 16px -12px rgba(43,35,48,.45);
  animation:quest-enter .35s ease-out both; transition:opacity .2s ease, transform .2s ease;}
div[class*="st-key-quest_row_"]:hover {box-shadow:0 10px 22px -14px rgba(212,85,31,.55);}
div[class*="st-key-quest_row_"]:has(input:checked:not(:disabled)) {opacity:.4; transform:translateY(-4px); pointer-events:none;}
div[class*="st-key-quest_row_"] label {width:100%%; cursor:pointer;}
div[class*="st-key-quest_row_"] [data-testid="stMarkdownContainer"] p {font-weight:500; line-height:1.45;}


.lq-team-matrix,.lq-duel-scoreboard {background:%(surface)s;border-radius:22px;padding:20px;margin:12px 0 22px;box-shadow:0 8px 22px -16px rgba(43,35,48,.45);}
.lq-team-matrix table {width:100%%;border-collapse:collapse;font-size:14px;}
.lq-team-matrix th,.lq-team-matrix td {padding:10px 5px;border-bottom:1px solid %(line)s;text-align:center;}
.lq-team-matrix th:first-child {text-align:left;overflow-wrap:anywhere;}
.lq-quest-legend {font-size:13px;margin-bottom:14px;color:%(ink)s;}
.lq-participation {display:inline-flex;width:25px;height:25px;border-radius:7px;align-items:center;justify-content:center;}
.lq-participation.yes {background:#CDEBD8;color:#245B38;font-weight:700;}.lq-participation.no {background:#F5F0EC;color:#655767;}
.lq-duel-players {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;}
.lq-duel-player {display:flex;flex-direction:column;align-items:center;text-align:center;gap:6px;background:#FFF2E4;border-radius:18px;padding:14px 6px;min-width:0;}
.lq-duel-player strong {overflow-wrap:anywhere;}.lq-duel-player .medal {font-size:28px;}.lq-duel-player small {color:#44364B;}
.lq-podium .p {min-height:170px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;}
.lq-podium .p.first {min-height:230px;}.lq-podium .p:last-child:not(.first) {min-height:150px;}
.st-key-competition_rules [data-testid="stCaptionContainer"] p {color:%(ink)s;}

@media(max-width:480px) {
 .st-key-bottom_navigation {border-radius:22px !important;}
 .st-key-bottom_navigation [role="radiogroup"] {grid-template-columns:repeat(3,minmax(0,1fr)) !important;}
 .stMainBlockContainer {padding-bottom:140px !important;}
}
/* ---------- Floating bottom navigation ---------- */
.st-key-bottom_navigation {
  position:fixed; z-index:1000; left:50%%; transform:translateX(-50%%);
  bottom:calc(14px + env(safe-area-inset-bottom, 0px));
  width:min(680px, calc(100%% - 24px)); background:%(surface)s; border-radius:999px;
  padding:6px; box-shadow:0 14px 34px -14px rgba(43,35,48,.45);}
.st-key-bottom_navigation [data-testid="stElementContainer"], .st-key-bottom_navigation [data-testid="stRadio"] {width:100%% !important;}
.st-key-bottom_navigation [role="radiogroup"] {width:100%% !important; display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:2px;
  overflow:visible;}
.st-key-bottom_navigation [role="radiogroup"]::-webkit-scrollbar {display:none;}
.st-key-bottom_navigation [role="radiogroup"] > div {width:100%%; min-width:0;}
.st-key-bottom_navigation [role="radiogroup"] label {width:100%%; white-space:normal; justify-content:center; text-align:center; min-width:0; border-radius:24px; padding:8px 3px; margin:0;
  color:#55444F; font-weight:400; box-shadow:none; transition:background .2s ease;}
.st-key-bottom_navigation [role="radiogroup"] label > div:last-child {width:100%%; display:flex; justify-content:center; text-align:center;}
.st-key-bottom_navigation [role="radiogroup"] label [data-testid="stMarkdownContainer"] {width:100%%; text-align:center;}
.st-key-bottom_navigation [role="radiogroup"] label p {color:#55444F; font-weight:400; text-align:center; font-size:13px; line-height:1.3; overflow-wrap:anywhere;}
div[class*="st-key-pillar_link_"] button p {font-size:1.15rem; font-weight:600;}
div[class*="st-key-pillar_link_"] button {padding-left:0;}
.st-key-bottom_navigation [role="radiogroup"] label:has(input:checked) {background:#FFF1E6; color:#55444F; box-shadow:none;}
.st-key-bottom_navigation [role="radiogroup"] label:has(input:checked) p {color:#55444F;}
.st-key-bottom_navigation [data-testid="stRadioOption"] > div > div:first-child,
.st-key-bottom_navigation label > div:first-child:not(:last-child) {display:none !important;}

/* ---------- Onboarding choices ---------- */
.st-key-onboarding div[data-testid="stRadio"] label,
.st-key-onboarding div[data-testid="stCheckbox"] {background:%(surface)s; border-radius:18px; padding:12px 16px; margin:6px 0;
  box-shadow:0 6px 16px -12px rgba(43,35,48,.45);}

.st-key-onboarding {max-width:720px; margin:0 auto;}
.st-key-onboarding [class*="st-key-pickcard_"] {background:%(surface)s; border-radius:18px; padding:12px 16px 10px; height:100%%;
  box-shadow:0 6px 16px -12px rgba(43,35,48,.45); transition:transform .22s cubic-bezier(.2,.9,.3,1), box-shadow .22s ease, background .2s ease;}
.st-key-onboarding [class*="st-key-pickcard_"]:hover {transform:translateY(-3px); box-shadow:0 14px 28px -16px rgba(212,85,31,.55);}
.st-key-onboarding [class*="st-key-pickcard_"]:has(input:checked) {background:#FFF1E6; box-shadow:inset 0 0 0 2px %(action)s;}
.st-key-onboarding [class*="st-key-pickcard_"] div[data-testid="stCheckbox"] {background:none; box-shadow:none; padding:0; margin:0; transform:none !important;}
.st-key-onboarding [class*="st-key-pickcard_"] [data-testid="stCaptionContainer"] {margin:-6px 0 0 28px;}

/* No "loading" fade: keep the page fully visible while Streamlit reruns after a click */
[data-stale="true"] {opacity:1 !important; transition:none !important;}

/* ---------- Custom blocks (helpers below) ---------- */
.lq-eyebrow {font-size:12px; letter-spacing:.14em; text-transform:uppercase; color:%(muted)s; font-weight:600;}
.lq-top {display:flex; justify-content:space-between; align-items:flex-end; gap:12px; margin-bottom:4px;}
.lq-hi {color:%(muted)s; font-size:15px;}
.lq-name {font-size:2.6rem; font-weight:300; letter-spacing:-.025em; line-height:1.05;}
.lq-xp {background:%(surface)s; border-radius:999px; padding:7px 13px; font-weight:600; font-size:14px; white-space:nowrap;
  box-shadow:0 6px 16px -8px rgba(255,138,76,.6);}
.lq-hero {position:relative; overflow:hidden; border-radius:28px; padding:22px 22px 24px; margin:10px 0 18px;
  color:%(ink)s; min-height:150px;}
.lq-hero .lq-tag {display:inline-block; font-size:12px; font-weight:600; background:rgba(255,255,255,.55);
  border-radius:999px; padding:5px 11px; margin-bottom:10px;}
.lq-hero h3 {margin:0; font-size:1.7rem; font-weight:600; line-height:1.1; max-width:13ch; letter-spacing:-.015em; padding:0;}
.lq-hero p {margin:8px 0 0; max-width:30ch; font-size:15px;}
.lq-sprout {position:absolute; right:-10px; bottom:-22px; width:128px; height:128px; border-radius:50%%;
  background:radial-gradient(circle at 34%% 30%%, #E4F7D8, %(growth)s 72%%);}
.lq-sprout::before, .lq-sprout::after {content:""; position:absolute; top:46px; width:8px; height:11px; border-radius:50%%; background:%(ink)s;}
.lq-sprout::before {left:40px;} .lq-sprout::after {left:64px;}
.lq-sprout i {position:absolute; left:50px; top:-18px; width:22px; height:28px; border-radius:22px 0 22px 0; background:%(growth)s;
  transform:rotate(-12deg); filter:brightness(.92);}
.lq-pillar {display:flex; align-items:center; gap:12px; margin:22px 0 8px;}
.lq-pillar .lq-ico {width:42px; height:42px; border-radius:14px; display:grid; place-items:center; font-size:20px; flex:none;}
.lq-pillar b {font-size:1.2rem; font-weight:600; display:block; line-height:1.2;}
.lq-pillar span {color:%(muted)s; font-size:13px;}
.lq-heat {background:%(surface)s; border-radius:22px; padding:16px; box-shadow:0 8px 22px -16px rgba(43,35,48,.45); margin-bottom:14px;}
.lq-heat .grid, .lq-heat .days {max-width:380px;}
.lq-heat .grid {display:grid; grid-template-columns:repeat(7, 1fr); gap:6px; margin-top:10px;}
.lq-heat .grid i {aspect-ratio:1; border-radius:8px; display:block;}
.lq-heat .days {display:grid; grid-template-columns:repeat(7, 1fr); gap:6px; font-size:11px; color:%(muted)s; text-align:center; margin-top:6px;}
.lq-heat .legend {display:flex; align-items:center; gap:4px; justify-content:flex-end; font-size:11px; color:%(muted)s; margin-top:10px;}
.lq-heat .legend i {width:12px; height:12px; border-radius:4px; display:inline-block;}

/* ---------- General white card: st.container(key="card_<name>") ---------- */
div[class*="st-key-card_"] {background:%(surface)s; border-radius:22px; padding:20px 22px;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45);}
div[class*="st-key-card_"] h3 {padding-top:0;}

/* ---------- Leaderboard ---------- */
.lq-podium {display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; align-items:end; margin:8px 0 18px;}
.lq-podium .p {background:%(surface)s; border-radius:22px; padding:16px 12px; text-align:center;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45); min-width:0;}
.lq-podium .p.first {background:linear-gradient(160deg,#FFD0A3,#FFB27F); padding-block:24px;}
.lq-podium .medal {font-size:28px; line-height:1;}
.lq-podium .who {font-weight:600; font-size:14px; max-width:100%%; margin-top:8px; overflow-wrap:anywhere; white-space:normal; line-height:1.2;}
.lq-podium .pts {font-size:1.6rem; font-weight:300; letter-spacing:-.02em;}
.lq-podium small, .lq-rank small {color:%(muted)s; font-size:12px;}
.lq-rank {display:grid; grid-template-columns:2.2rem minmax(0,1fr) auto; gap:12px; align-items:center;
  background:%(surface)s; border-radius:18px; padding:12px 16px; margin-bottom:8px; box-shadow:0 6px 16px -12px rgba(43,35,48,.45);}
.lq-rank .n {font-weight:600; color:%(muted)s; font-variant-numeric:tabular-nums;}
.lq-rank .who {font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}
.lq-rank .pts {font-weight:600; font-variant-numeric:tabular-nums; text-align:right;}
.lq-rank.me, .lq-podium .p.me {outline:2px solid %(glow)s; outline-offset:-2px;}

/* ---------- Squad ranking (compact) ---------- */
.lq-ranking {background:%(surface)s; border-radius:22px; padding:14px 16px; margin:4px 0 16px;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45); animation:lq-up .45s ease-out both;}
.lq-ranking .row {display:grid; grid-template-columns:1.8rem minmax(0,1fr) auto; gap:10px; align-items:center;
  padding:8px 6px; border-radius:14px; transition:background .2s ease;}
.lq-ranking .row + .row {border-top:1px solid %(line)s;}
.lq-ranking .row:hover {background:#FFF4EC;}
.lq-ranking .row.me {background:#FFF1E6;}
.lq-ranking .n {font-size:18px; text-align:center; color:%(muted)s; font-weight:600;}
.lq-ranking .who {display:flex; align-items:center; gap:8px; min-width:0; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.lq-ranking .who i {width:26px; height:26px; border-radius:50%%; display:grid; place-items:center; font-style:normal; font-size:11px;
  font-weight:600; background:#FFE6D4; flex:none;}
.lq-ranking .pts {text-align:right; font-weight:600; font-variant-numeric:tabular-nums; line-height:1.2;}
.lq-ranking .pts small {display:block; font-weight:400; font-size:11px; color:%(muted)s;}

/* Quests-per-pillar rows: 1-5 buttons fill their half evenly */
.st-key-card_quests_shown [data-testid="stButtonGroup"] {width:100%%;}
.st-key-card_quests_shown [data-testid="stButtonGroup"] > div {display:flex; width:100%%;}
.st-key-card_quests_shown [data-testid="stButtonGroup"] button {flex:1 1 0; justify-content:center;}
.st-key-card_quests_shown [data-testid="stHorizontalBlock"] {margin-bottom:-4px;}

/* ---------- Adaptivity hint under a quest ---------- */
.lq-trend {display:block; font-size:12.5px; font-weight:600; margin:-6px 0 0 30px;}
.lq-trend.up {color:#3E9B63;}
.lq-trend.down {color:%(action)s;}

/* ---------- Recap: quests per pillar ---------- */
.lq-bars {background:%(surface)s; border-radius:22px; padding:16px 18px; display:grid; gap:12px;
  box-shadow:0 8px 22px -16px rgba(43,35,48,.45); animation:lq-up .45s ease-out both;}
.lq-bars .row {display:grid; grid-template-columns:minmax(0,10rem) minmax(0,1fr) 2rem; gap:12px; align-items:center;}
.lq-bars .name {font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.lq-bars .track {height:12px; border-radius:999px; background:#F3ECE7; overflow:hidden;}
.lq-bars .track i {display:block; height:100%%; border-radius:999px; transform-origin:left; animation:lq-fill .8s cubic-bezier(.2,.9,.3,1) both;}
.lq-bars .n {text-align:right; font-weight:600; font-variant-numeric:tabular-nums;}

/* ---------- People ---------- */
.lq-avatar {width:64px; height:64px; border-radius:50%%; padding:3px; background:var(--ring); flex:none;
  transition:transform .3s cubic-bezier(.2,1.4,.4,1);}
.lq-avatar > img, .lq-avatar > span {width:100%%; height:100%%; border-radius:50%%; display:grid; place-items:center; object-fit:cover;
  background:#FFF1E6; color:%(ink)s; font-weight:600; border:2px solid %(surface)s; box-sizing:border-box;}
.lq-avatar:hover {transform:rotate(-6deg) scale(1.06);}
.lq-top .who {display:flex; align-items:center; gap:14px;}
.lq-rings {display:flex; gap:10px; flex-wrap:wrap; margin:4px 0 8px;}
.lq-profile {display:flex; gap:16px; align-items:center;}
.lq-profile b {font-size:1.4rem; font-weight:600; display:block;}
.lq-profile span {color:%(muted)s;}
.lq-chips {display:flex; flex-wrap:wrap; gap:8px; margin:6px 0 12px;}
.lq-chip {display:inline-flex; align-items:center; gap:8px; background:%(surface)s; border-radius:999px; padding:4px 12px 4px 4px;
  box-shadow:0 4px 12px -8px rgba(43,35,48,.45); font-size:14px; font-weight:500;}
.lq-chip i {width:26px; height:26px; border-radius:50%%; display:grid; place-items:center; font-style:normal; font-size:12px; font-weight:600;
  background:#FFE6D4;}

/* ---------- Desktop ---------- */
@media (min-width:960px) {
  .stMainBlockContainer {max-width:1080px; padding-bottom:4rem;}
  .st-key-bottom_navigation {position:sticky; top:12px; left:auto; bottom:auto; transform:none;
    width:fit-content; max-width:100%%; margin:0 auto 10px;}
  .lq-hero {min-height:130px; padding:22px 26px;}
  .st-key-bottom_navigation [role="radiogroup"] label p {font-size:14px;}
  .lq-hero h3 {font-size:2rem; max-width:18ch;}
  .lq-hero p {max-width:46ch;}
  .lq-sprout {width:150px; height:150px; right:24px;}
}

/* ---------- Loading screen ---------- */
.lq-splash {position:fixed; inset:0; z-index:999999; background:%(page)s; display:grid; place-items:center;
  pointer-events:none; animation:lq-fade-out .45s ease 1.5s forwards;}
.lq-splash .in {display:grid; justify-items:center; gap:14px;}
.lq-splash .lq-logo {width:96px; height:96px; animation:lq-pop .6s cubic-bezier(.2,1.4,.4,1) both;}
.lq-splash .stem {stroke-dasharray:16; stroke-dashoffset:16; animation:lq-draw .45s ease .35s forwards;}
.lq-splash .leaf {transform-box:fill-box; transform:scale(0); animation:lq-grow .45s cubic-bezier(.2,1.5,.4,1) .65s forwards;}
.lq-splash .leaf.l {transform-origin:100%% 100%%;}
.lq-splash .leaf.r {transform-origin:0%% 100%%; animation-delay:.8s;}
.lq-splash .word {font-size:1.5rem; font-weight:300; letter-spacing:-.01em; opacity:0; animation:lq-up .5s ease .9s forwards;}
.lq-splash .dots {display:flex; gap:6px;}
.lq-splash .dots i {width:7px; height:7px; border-radius:50%%; background:%(glow)s; animation:lq-dot 1s ease-in-out infinite;}
.lq-splash .dots i:nth-child(2) {animation-delay:.15s;} .lq-splash .dots i:nth-child(3) {animation-delay:.3s;}
@keyframes lq-fade-out {to {opacity:0; visibility:hidden;}}
@keyframes lq-pop {from {transform:scale(.4); opacity:0;} to {transform:none; opacity:1;}}
@keyframes lq-draw {to {stroke-dashoffset:0;}}
@keyframes lq-grow {to {transform:scale(1);}}
@keyframes lq-up {from {opacity:0; transform:translateY(8px);} to {opacity:1; transform:none;}}
@keyframes lq-dot {0%%,100%% {transform:translateY(0); opacity:.4;} 50%% {transform:translateY(-6px); opacity:1;}}

/* ---------- Brand ---------- */
.lq-brand {display:flex; align-items:center; gap:8px;}
.lq-brand .lq-logo {width:26px; height:26px; transition:transform .35s cubic-bezier(.2,1.4,.4,1);}
.lq-brand:hover .lq-logo {transform:rotate(-12deg) scale(1.12);}

/* ---------- Daily goal progress (inside the hero) ---------- */
.lq-goal {position:relative; z-index:1; margin-top:14px; max-width:320px;}
.lq-goal .bar {height:10px; border-radius:999px; background:rgba(255,255,255,.55); overflow:hidden;}
.lq-goal .bar i {display:block; height:100%%; border-radius:999px; background:%(ink)s; transform-origin:left;
  animation:lq-fill .9s cubic-bezier(.2,.9,.3,1) .2s both;}
.lq-goal span {display:block; font-size:13px; font-weight:600; margin-top:6px;}
@keyframes lq-fill {from {transform:scaleX(0);} to {transform:scaleX(1);}}

/* ---------- Entrance: content rises in, staggered ---------- */
.lq-hero, .lq-heat, .lq-podium .p, .lq-rank, div[data-testid="stMetric"], div[class*="st-key-card_"], .lq-pillar {
  animation:lq-up .45s ease-out both;}
.lq-podium .p:nth-child(2) {animation-delay:.08s;} .lq-podium .p:nth-child(3) {animation-delay:.16s;}
.lq-rank:nth-of-type(2) {animation-delay:.05s;} .lq-rank:nth-of-type(3) {animation-delay:.1s;}
[data-testid="stColumn"]:nth-child(2) div[data-testid="stMetric"] {animation-delay:.06s;}
[data-testid="stColumn"]:nth-child(3) div[data-testid="stMetric"] {animation-delay:.12s;}

/* ---------- Hover: main options lift toward the cursor ---------- */
div[class*="st-key-quest_row_"], div[data-testid="stMetric"], div[data-testid="stExpander"] details,
div[class*="st-key-card_"], .lq-podium .p, .lq-rank, .lq-chip, .lq-heat,
.st-key-onboarding div[data-testid="stRadio"] label, .st-key-onboarding div[data-testid="stCheckbox"] {
  transition:transform .22s cubic-bezier(.2,.9,.3,1), box-shadow .22s ease, background .2s ease;}
div[class*="st-key-quest_row_"]:hover, div[data-testid="stMetric"]:hover, div[data-testid="stExpander"] details:hover,
.lq-podium .p:hover, .lq-rank:hover, .lq-chip:hover,
.st-key-onboarding div[data-testid="stRadio"] label:hover, .st-key-onboarding div[data-testid="stCheckbox"]:hover {
  transform:translateY(-3px); box-shadow:0 14px 28px -16px rgba(212,85,31,.55);}
.lq-podium .p.first:hover {transform:translateY(-5px) scale(1.02);}
div.stButton > button, div.stFormSubmitButton > button {transition:transform .18s ease, box-shadow .18s ease, background .18s ease;}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {transform:translateY(-2px); box-shadow:0 10px 20px -12px rgba(212,85,31,.7);}
div.stButton > button:active, div.stFormSubmitButton > button:active {transform:scale(.97);}
.st-key-bottom_navigation [role="radiogroup"] label {transition:background .2s ease, color .2s ease;}
.st-key-bottom_navigation [role="radiogroup"] label:hover {background:#FFF7F0; transform:none; box-shadow:none;}
.st-key-bottom_navigation [role="radiogroup"] label:has(input:checked):hover,
.st-key-bottom_navigation [role="radiogroup"] label:active {background:#FFF1E6; transform:none; box-shadow:none;}
.st-key-bottom_navigation [role="radiogroup"] label[data-focus-visible="true"] {outline:2px solid #E8CFC0; outline-offset:2px;}
.lq-pillar .lq-ico {transition:transform .3s cubic-bezier(.2,1.4,.4,1);}
.lq-pillar:hover .lq-ico {transform:rotate(-8deg) scale(1.1);}
.lq-heat .grid i {transition:transform .15s ease;}
.lq-heat .grid i:hover {transform:scale(1.15);}

/* ---------- Idle life: the sprout breathes and sways ---------- */
.lq-sprout {animation:lq-bob 3.4s ease-in-out infinite;}
.lq-sprout i {transform-origin:bottom right; animation:lq-sway 2.8s ease-in-out infinite;}
.lq-hero:hover .lq-sprout {animation-duration:1.6s;}
@keyframes lq-bob {0%%,100%% {transform:translateY(0);} 50%% {transform:translateY(-6px);}}
@keyframes lq-sway {0%%,100%% {transform:rotate(-12deg);} 50%% {transform:rotate(4deg);}}

/* ---------- Stat rows: st.container(key="stat_row_<name>") keeps tiles side by side on phones ---------- */
@media (max-width:640px) {
  div[class*="st-key-stat_row"] [data-testid="stHorizontalBlock"] {flex-wrap:nowrap !important; gap:8px;}
  div[class*="st-key-stat_row"] [data-testid="stColumn"] {min-width:0 !important; width:auto !important; flex:1 1 0 !important;}
  div[class*="st-key-stat_row"] div[data-testid="stMetric"] {padding:10px 12px;}
  div[class*="st-key-stat_row"] div[data-testid="stMetricValue"] {font-size:1.6rem;}
  div[class*="st-key-stat_row"] div[data-testid="stMetricDelta"] {display:none;}
  div[class*="st-key-stat_row"] [data-testid="stMetricLabel"] p {font-size:12px; white-space:normal;}
}

@media (max-width:640px) {
  .stMainBlockContainer {padding-top:1.25rem;}
  .lq-name {font-size:2.1rem;}
  .lq-hero h3 {font-size:1.45rem;}
  .lq-sprout {width:104px; height:104px;}
}
@media (prefers-reduced-motion:reduce) {
  *, *::before, *::after {animation:none !important; transition:none !important;}
  div[class*="st-key-quest_row_"], .lq-podium .p, .lq-rank, div[data-testid="stMetric"] {transform:none !important;}
  .lq-splash {display:none;}
  .lq-goal .bar i {transform:none;}
}
</style>
""" % {"muted": MUTED, "surface": SURFACE, "line": LINE, "action": ACTION, "ink": INK, "growth": GROWTH, "glow": GLOW, "page": PAGE}


def apply_styles() -> None:
    """Inject the shared styles. Call once per run, before rendering any screen."""
    st.markdown(_CSS, unsafe_allow_html=True)


def pillar_colors(category: str) -> tuple[str, str]:
    return PILLAR_COLORS.get(category, DEFAULT_PILLAR)


def greeting(hello: str, name: str, xp: int, photo: str | None = None, ring: str = "peach") -> None:
    """Top of a main screen: avatar, small 'Hello,' line, big light name, XP pill."""
    st.markdown(
        f'<div class="lq-top"><div class="who">{avatar_html(name, photo, ring, size=58)}<div><div class="lq-hi">{html.escape(hello)}</div>'
        f'<div class="lq-name">{html.escape(name)}</div></div></div>'
        f'<span><span class="lq-xp">🌱 {int(xp)} XP</span></span></div>',
        unsafe_allow_html=True,
    )


def hero(tag: str, title: str, body: str = "", variant: str = "peach", sprout: bool = True,
         progress: tuple[int, int, str] | None = None) -> None:
    """Gradient focus card. Use at most one per screen.

    progress: optional (done, goal, label) shown as an animated bar, e.g. the daily quest goal.
    """
    gradient = HERO_GRADIENTS.get(variant, HERO_GRADIENTS["peach"])
    body_html = f"<p>{html.escape(body)}</p>" if body else ""
    sprout_html = '<div class="lq-sprout" aria-hidden="true"><i></i></div>' if sprout else ""
    goal_html = ""
    if progress:
        done, goal, label = progress
        pct = 0 if goal <= 0 else min(100, round(100 * done / goal))
        goal_html = (f'<div class="lq-goal" role="progressbar" aria-valuemin="0" aria-valuemax="{int(goal)}" '
                     f'aria-valuenow="{min(int(done), int(goal))}"><div class="bar"><i style="width:{pct}%"></i></div>'
                     f'<span>{html.escape(label)}</span></div>')
    st.markdown(
        f'<div class="lq-hero" style="background:{gradient}"><span class="lq-tag">{html.escape(tag)}</span>'
        f'<h3>{html.escape(title)}</h3>{body_html}{goal_html}{sprout_html}</div>',
        unsafe_allow_html=True,
    )


def pillar_header(category: str, icon: str, label: str, caption: str = "") -> None:
    """Section header for a pillar: coloured icon tile, name, optional caption."""
    bg, _ = pillar_colors(category)
    cap = f"<span>{html.escape(caption)}</span>" if caption else ""
    st.markdown(
        f'<div class="lq-pillar"><div class="lq-ico" style="background:{bg}">{icon}</div>'
        f'<div><b>{html.escape(label)}</b>{cap}</div></div>',
        unsafe_allow_html=True,
    )


def heatmap(category: str, activity: list[dict], title: str, less: str = "Less", more: str = "More",
            weekdays: tuple[str, ...] = ("M", "T", "W", "T", "F", "S", "S")) -> None:
    """Two-week activity grid (7 columns) coloured in the pillar's strong colour.

    activity: list of {"Date": date, "Quests": int}, oldest first (pillar_statistics output).
    """
    _, strong = pillar_colors(category)
    shades = ["#F3ECE7", strong + "40", strong + "90", strong]

    def level(n: int) -> int:
        return 0 if n <= 0 else 1 if n == 1 else 2 if n == 2 else 3

    cells = "".join(
        f'<i style="background:{shades[level(d["Quests"])]}" '
        f'title="{_fmt(d["Date"])}: {int(d["Quests"])}"></i>'
        for d in activity
    )
    first = activity[0]["Date"] if activity else date.today()
    labels = "".join(f"<span>{html.escape(weekdays[(first.weekday() + i) % 7])}</span>" for i in range(7))
    legend = "".join(f'<i style="background:{c}"></i>' for c in shades)
    st.markdown(
        f'<div class="lq-heat"><div class="lq-eyebrow">{html.escape(title)}</div>'
        f'<div class="grid">{cells}</div><div class="days">{labels}</div>'
        f'<div class="legend">{html.escape(less)} {legend} {html.escape(more)}</div></div>',
        unsafe_allow_html=True,
    )


def _fmt(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else html.escape(str(value))


def initials(name: str) -> str:
    parts = [p for p in str(name or "").split() if p]
    return html.escape("".join(p[0] for p in parts[:2]).upper() or "?")


# Avatar ring styles available to everyone.
AVATAR_RINGS = {
    "peach": "linear-gradient(140deg,#FFB27F,#F9C4DA)",
    "lilac": "linear-gradient(140deg,#B9A8F2,#F7B7D2)",
    "mint": "linear-gradient(140deg,#7CC394,#F3F0C4)",
    "ocean": "linear-gradient(140deg,#8FC7E8,#B9A8F2)",
    "gold": "linear-gradient(140deg,#F2D16B,#FF8A4C)",
    "sunset": "conic-gradient(from 200deg,#FF8A4C,#F7B7D2,#B9A8F2,#7CC394,#FF8A4C)",
}


def avatar_html(name: str, photo: str | None = None, ring: str = "peach", size: int = 64) -> str:
    """Round avatar: the user's photo (a data: URL) or initials, inside a gradient ring."""
    ring_bg = AVATAR_RINGS.get(ring, AVATAR_RINGS["peach"])
    if photo and photo.startswith("data:image/"):
        inner = f'<img src="{html.escape(photo, quote=True)}" alt="">'
    else:
        inner = f'<span>{initials(name)}</span>'
    return (f'<div class="lq-avatar" style="--ring:{ring_bg}; width:{size}px; height:{size}px; '
            f'font-size:{round(size * 0.4)}px">{inner}</div>')


def profile_card(name: str, line: str, photo: str | None = None, ring: str = "peach") -> None:
    """Avatar, name and one muted line (XP · city)."""
    st.markdown(
        f'<div class="lq-profile">{avatar_html(name, photo, ring)}'
        f'<div><b>{html.escape(name)}</b><span>{html.escape(line)}</span></div></div>',
        unsafe_allow_html=True,
    )


def member_chips(names: list[str]) -> None:
    chips = "".join(f'<span class="lq-chip"><i>{initials(n)}</i>{html.escape(n)}</span>' for n in names)
    st.markdown(f'<div class="lq-chips">{chips}</div>', unsafe_allow_html=True)


def leaderboard(rows: list[dict], me: str, xp_label: str = "XP", quests_label: str = "quests") -> None:
    """Podium for the top three, then ranked rows. rows: name, points, quests (already sorted)."""
    def is_me(r):
        return r.get("is_me", bool(me) and r["name"] == me)

    top = rows[:3]
    order = [1, 0, 2] if len(top) == 3 else list(range(len(top)))  # 2nd, 1st, 3rd on the podium
    medals = ["🥇", "🥈", "🥉"]
    cards = "".join(
        f'<div class="p{" first" if i == 0 else ""}{" me" if is_me(top[i]) else ""}">'
        f'<div class="medal">{medals[i]}</div>{avatar_html(top[i]["name"],top[i].get("photo"),size=48)}<div class="who">{html.escape(top[i]["name"])}</div>'
        f'<div class="pts">{int(top[i]["points"])} {html.escape(xp_label)}</div>'
        f'<small>{int(top[i]["quests"])} {html.escape(quests_label)}</small></div>'
        for i in order
    )
    style = f' style="grid-template-columns:repeat({len(top)}, minmax(0,1fr))"' if len(top) < 3 else ""
    out = f'<div class="lq-podium"{style}>{cards}</div>' if top else ""
    for n, r in enumerate(rows[3:], 4):
        out += (f'<div class="lq-rank{" me" if is_me(r) else ""}"><span class="n">{n}</span>'
                f'<span class="who">{html.escape(r["name"])}<br><small>{int(r["quests"])} {html.escape(quests_label)}</small></span>'
                f'<span class="pts">{int(r["points"])} {html.escape(xp_label)}</span></div>')
    st.markdown(out, unsafe_allow_html=True)


LOGO_SVG = (
    '<svg class="lq-logo" viewBox="0 0 48 48" aria-hidden="true">'
    '<defs><linearGradient id="lq-logo-bg" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#FFB27F"/><stop offset="1" stop-color="#F9C4DA"/></linearGradient></defs>'
    '<circle cx="24" cy="24" r="24" fill="url(#lq-logo-bg)"/>'
    '<path class="stem" d="M24 37 V22" stroke="#3E9B63" stroke-width="3" stroke-linecap="round" fill="none"/>'
    '<path class="leaf l" d="M24 25 C16 25 12.5 19.5 13.5 13.5 C20 13.5 24 18 24 25Z" fill="#7CC394"/>'
    '<path class="leaf r" d="M24 22 C24.5 14 30.5 10.5 36 11 C36.5 18 31 22.5 24 22Z" fill="#5DB27E"/>'
    '</svg>'
)


def brand(label: str = "Life Quest") -> None:
    """Small logo + wordmark eyebrow for the top of a screen."""
    st.markdown(f'<div class="lq-brand">{LOGO_SVG}<span class="lq-eyebrow">{html.escape(label)}</span></div>',
                unsafe_allow_html=True)


def splash() -> None:
    """Animated loading screen (sprout grows, then fades). Shown once per browser session by app.py."""
    st.markdown(
        f'<div class="lq-splash" aria-hidden="true"><div class="in">{LOGO_SVG}'
        '<div class="word">Life Quest</div><div class="dots"><i></i><i></i><i></i></div></div></div>',
        unsafe_allow_html=True,
    )


def squad_ranking(rows: list[dict], me: str, title: str, xp_label: str = "XP", quests_label: str = "quests") -> None:
    """Compact weekly ranking for one squad. rows: name, points, quests (any order)."""
    rows = sorted(rows, key=lambda r: (-int(r["points"]), -int(r["quests"]), r["name"]))
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    out = f'<div class="lq-ranking"><div class="lq-eyebrow">{html.escape(title)}</div>'
    for n, r in enumerate(rows, 1):
        mine = " me" if r.get("is_me",bool(me and r["name"]==me)) else ""
        badge = medals.get(n, str(n)) if int(r["points"]) > 0 else "·"
        out += (f'<div class="row{mine}"><span class="n">{badge}</span>'
                f'<span class="who"><i>{initials(r["name"])}</i>{html.escape(r["name"])}</span>'
                f'<span class="pts">{int(r["points"])} {html.escape(xp_label)}'
                f'<small>{int(r["quests"])} {html.escape(quests_label)}</small></span></div>')
    st.markdown(out + "</div>", unsafe_allow_html=True)


def pillar_bars(items: list[tuple[str, str, int]]) -> None:
    """Horizontal bars: items are (category, label with icon, count), largest first."""
    top = max((count for _, _, count in items), default=0) or 1
    rows = "".join(
        f'<div class="row"><span class="name">{html.escape(label)}</span>'
        f'<span class="track"><i style="width:{round(100 * count / top)}%; background:{pillar_colors(category)[1]}"></i></span>'
        f'<span class="n">{int(count)}</span></div>'
        for category, label, count in items
    )
    st.markdown(f'<div class="lq-bars">{rows}</div>', unsafe_allow_html=True)


def participation_matrix(squad, titles, heading, member_label, confirmed_label, pending_label):
    """Names down the rows, shared quests across columns; accessible status in each cell."""
    quests=squad.get('quests',[])
    legend=''.join(f'<div><b>Q{i+1}</b> · {html.escape(title)}</div>' for i,title in enumerate(titles))
    headers=''.join(f'<th scope="col" title="{html.escape(title,quote=True)}">Q{i+1}</th>' for i,title in enumerate(titles))
    rows=''
    for member in squad.get('members',[]):
        cells=''
        for quest in quests:
            done=member['id'] in quest.get('confirmed',[])
            label=confirmed_label if done else pending_label
            cells+=f'<td><span class="lq-participation {"yes" if done else "no"}" role="img" aria-label="{html.escape(label,quote=True)}" title="{html.escape(label,quote=True)}">{"✓" if done else "—"}</span></td>'
        rows+=f'<tr><th scope="row">{html.escape(member["name"])}</th>{cells}</tr>'
    st.markdown(f'<div class="lq-team-matrix"><h3>{html.escape(heading)}</h3><div class="lq-quest-legend">{legend}</div><table><thead><tr><th scope="col">{html.escape(member_label)}</th>{headers}</tr></thead><tbody>{rows}</tbody></table></div>',unsafe_allow_html=True)


def duel_scoreboard(rows, title, result_label, xp_label):
    cards=''
    for row in rows:
        medal='🥇' if row['place']==1 else '🥈'
        cards+=(f'<div class="lq-duel-player"><span class="medal">{medal}</span>{avatar_html(row["name"],size=40)}'
                f'<strong>{html.escape(row["name"])}</strong><span>{int(row["points"])} XP</span>'
                f'<small>{html.escape(result_label)}: {html.escape(str(row["result"]))}</small></div>')
    st.markdown(f'<div class="lq-duel-scoreboard"><h3>{html.escape(title)}</h3><div class="lq-duel-players">{cards}</div><p>{html.escape(xp_label)}</p></div>',unsafe_allow_html=True)
