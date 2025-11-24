import streamlit as st
import numpy as np
import control
import sympy as sp
import matplotlib.pyplot as plt
from graphviz import Digraph

st.set_page_config(page_title="Bac à sable de régulation", layout="wide")


# =======================================================
#  Conversion TF → SymPy
# =======================================================
def tf_to_sympy(sys):
    """Convertit un TransferFunction python-control en expression SymPy."""
    s = sp.symbols("s")
    num = sum(sys.num[0][i] * s**(len(sys.num[0]) - i - 1)
              for i in range(len(sys.num[0])))
    den = sum(sys.den[0][i] * s**(len(sys.den[0]) - i - 1)
              for i in range(len(sys.den[0])))
    return sp.simplify(num / den)


# =======================================================
#  SCHÉMA BLOC AVEC GRAPHVIZ
# =======================================================
def block_diagram():
    dot = Digraph()
    dot.attr(rankdir="LR", nodesep="1.0", ranksep="1.0")

    dot.node("in", "Entrée")
    dot.node("sum", "Σ")
    dot.node("pid", "Régulateur PID")
    dot.node("sys", "G(s)")
    dot.node("out", "Sortie")

    dot.edge("in", "sum")
    dot.edge("sum", "pid")
    dot.edge("pid", "sys")
    dot.edge("sys", "out")
    dot.edge("out", "sum", label="-", style="dashed")

    return dot


# =======================================================
#  CONSEIL DE RÉGULATEUR
# =======================================================
def conseil_regulateur(sys):
    try:
        poles = control.poles(sys)
    except:
        poles = control.pole(sys)

    info = control.step_info(sys)

    overshoot = info.get("Overshoot", 0)
    settling = info.get("SettlingTime", 0)

    if overshoot < 1 and settling < 2:
        return "P", "Le système est déjà stable et rapide → correcteur P suffisant."
    if overshoot < 10:
        return "PI", "Erreur statique possible, dynamique stable → PI adapté."
    if overshoot > 20:
        return "PD", "Système oscillant → dérivée nécessaire."
    return "PID", "Cas général → PID pour précision + stabilité."


# =======================================================
#  CRÉATION PID
# =======================================================
def create_pid(Kp, Ki, Kd):
    return control.TransferFunction([Kd, Kp, Ki], [1, 0])


# =======================================================
#  ANALYSE SYMBOLIQUE : G(s), int(G), dG/ds
# =======================================================
def symbolic_analysis(num, den):
    s = sp.symbols("s")
    num_poly = sp.Poly(num, s).as_expr()
    den_poly = sp.Poly(den, s).as_expr()
    Gs = sp.simplify(num_poly / den_poly)
    return Gs, sp.simplify(sp.integrate(Gs, s)), sp.simplify(sp.diff(Gs, s))


# =======================================================
#  INTERFACE STREAMLIT
# =======================================================

st.title("🔧 Bac à Sable de Régulation Automatique — PID, Analyse, Symbolique")
st.write("Explore, simule et analyse n'importe quel système linéaire.")


# -------- INPUT SYSTEM --------
st.subheader("📌 Définition du système G(s)")

col1, col2 = st.columns(2)
with col1:
    num_raw = st.text_input("Numérateur (ex: 1 ou 1,0.5)", "1")
with col2:
    den_raw = st.text_input("Dénominateur (ex: 1,2,1)", "1,2,1")

# Convert to list of floats
num = [float(x) for x in num_raw.split(",")]
den = [float(x) for x in den_raw.split(",")]

system = control.TransferFunction(num, den)


# -------- DISPLAY G(s) --------
st.subheader("📘 Fonction de transfert")
Gs_sym = tf_to_sympy(system)
st.latex(r"G(s) = " + sp.latex(Gs_sym))


# -------- SYMBOLIC ANALYSIS --------
st.subheader("🧮 Analyse symbolique")

Gs, integ, deriv = symbolic_analysis(num, den)

st.write("### Expression symbolique")
st.latex(sp.latex(Gs))

st.write("### Intégrale de G(s)")
st.latex(r"\int G(s)\,ds = " + sp.latex(integ))

st.write("### Dérivée de G(s)")
st.latex(r"\frac{d}{ds}G(s) = " + sp.latex(deriv))


# -------- BLOCK DIAGRAM --------
st.subheader("🧱 Schéma bloc du système")
st.graphviz_chart(block_diagram())


# -------- SYSTEM ANALYSIS --------
st.subheader("📊 Analyse du système")

try:
    poles = control.poles(system)
except:
    poles = control.pole(system)

st.write("**Pôles du système :**", poles)

step_info = control.step_info(system)
with st.expander("📄 Détails réponse indicielle (open-loop)"):
    st.json(step_info)

# Step response (open loop)
t, y = control.step_response(system)
plt.figure()
plt.plot(t, y)
plt.grid()
plt.title("Réponse indicielle — Boucle ouverte")
plt.xlabel("Temps (s)")
plt.ylabel("Amplitude")
st.pyplot(plt)


# -------- REGULATOR ADVICE --------
st.subheader("🤖 Conseil automatique du régulateur optimal")

reg_type, explanation = conseil_regulateur(system)
st.write(f"### Régulateur conseillé : **{reg_type}**")
st.info(explanation)


# -------- PID PARAMETERS --------
st.subheader("🎛 Réglage manuel du PID")

Kp = st.slider("Kp", 0.0, 20.0, 1.0)
Ki = st.slider("Ki", 0.0, 20.0, 1.0)
Kd = st.slider("Kd", 0.0, 5.0, 0.1)

pid = create_pid(Kp, Ki, Kd)
closed_loop = control.feedback(pid * system, 1)

# Closed loop step response
t2, y2 = control.step_response(closed_loop)
plt.figure()
plt.plot(t2, y2)
plt.grid()
plt.title("Réponse indicielle — Boucle fermée (PID)")
plt.xlabel("Temps (s)")
plt.ylabel("Amplitude")
st.pyplot(plt)

st.success("Simulation terminée ✔ — Tu peux modifier les gains et explorer.")
