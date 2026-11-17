"""Graphiques Plotly : radar, barres par bloc, carte de similarité.

Propriétaire : P4 (Application). Chaque fonction prend des données du contrat de sortie
et renvoie une figure ; la page affiche en plus la valeur en texte (accessibilité).
"""
import numpy as np
import plotly.graph_objects as go


def radar(block_scores: dict[str, float]) -> go.Figure:
    """Radar des scores de bloc (0 à 1)."""
    names, values = list(block_scores), list(block_scores.values())
    fig = go.Figure(go.Scatterpolar(r=values + values[:1], theta=names + names[:1],
                                    fill="toself", name="Profil"))
    fig.update_layout(polar={"radialaxis": {"range": [0, 1]}}, showlegend=False,
                      margin={"t": 30, "b": 30})
    return fig


def block_bars(block_scores: dict[str, float]) -> go.Figure:
    """Barres horizontales des scores de bloc, valeur écrite sur chaque barre."""
    names, values = list(block_scores), list(block_scores.values())
    fig = go.Figure(go.Bar(x=values, y=names, orientation="h",
                           text=[f"{v:.2f}" for v in values], textposition="auto"))
    fig.update_layout(xaxis={"range": [0, 1], "title": "Score de bloc"},
                      yaxis={"autorange": "reversed"}, margin={"t": 30, "b": 30})
    return fig


def similarity_heatmap(matrix: dict, labels: dict[str, str] | None = None) -> go.Figure:
    """Carte de similarité segments x compétences (contrat : rows, cols, values)."""
    values = np.array(matrix["values"], dtype=float)
    cols = [(labels or {}).get(c, c) for c in matrix["cols"]]
    fig = go.Figure(go.Heatmap(z=values, x=cols, y=matrix["rows"], zmin=0, zmax=1,
                               colorscale="Blues", colorbar={"title": "cosinus"}))
    fig.update_layout(xaxis={"tickangle": -45}, yaxis={"autorange": "reversed"},
                      margin={"t": 30})
    return fig
