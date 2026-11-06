"""Plotly views with a common polarity scale and explicit time/angle labels."""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from solar_sim.physics import LATITUDES, LONGITUDES, displacement, observation_time

FIELD_LIMIT = 100
COLORS = [[0, "#174a94"], [0.35, "#8cbbdf"], [0.5, "#f8f8f6"],
          [0.65, "#eeafa1"], [1, "#a51f30"]]


def maps_figure(maps, titles, selected=None, scan=None, height=350, limit=FIELD_LIMIT):
    fig = make_subplots(rows=1, cols=len(maps), subplot_titles=titles, horizontal_spacing=0.055)
    for col, values in enumerate(maps, start=1):
        fig.add_trace(go.Heatmap(
            x=LONGITUDES, y=LATITUDES, z=values, coloraxis="coloraxis",
            hovertemplate="Longitude %{x:.0f}°<br>Latitude %{y:.0f}°<br>Bᵣ %{z:.2f} G<extra></extra>",
            hoverongaps=False,
        ), row=1, col=col)
        if selected is not None:
            fig.add_vline(x=selected, line_color="#7953bc", line_width=2, line_dash="dot", row=1, col=col)
        if scan is not None:
            fig.add_vline(x=scan, line_color="#008a77", line_width=2, row=1, col=col)
    fig.update_xaxes(title_text="Carrington longitude (°)", range=[-0.5, 359.5],
                     tickvals=[0, 90, 180, 270, 359])
    fig.update_yaxes(title_text="Latitude (°)", range=[-90, 90], tickvals=[-60, -30, 0, 30, 60])
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=45, b=15),
                      coloraxis=dict(colorscale=COLORS, cmin=-limit, cmax=limit,
                                     colorbar=dict(title="Bᵣ (G)", thickness=12)),
                      plot_bgcolor="#e1e5ea", paper_bgcolor="rgba(0,0,0,0)",
                      uirevision="carrington-map", font=dict(size=12))
    return fig


def add_transport_paths(fig, longitude, reference_time, differential, progress):
    """Draw seam-split paths, so a wrap never looks like a long reverse jump."""
    elapsed = reference_time - observation_time(longitude)
    for lat, color in [(0, "#202020"), (30, "#b27300"), (60, "#6e35a5")]:
        shift = float(displacement(lat, elapsed, differential))
        unwrapped = longitude + np.linspace(0, progress * shift, 100)
        path = unwrapped % 360
        xx, yy = [], []
        for i, point in enumerate(path):
            if i and abs(point - path[i - 1]) > 180:
                xx.append(None)
                yy.append(None)
            xx.append(point)
            yy.append(lat)
        fig.add_trace(go.Scatter(x=xx, y=yy, mode="lines", line=dict(color=color, width=3),
                                showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=[longitude, path[-1]], y=[lat, lat], mode="markers",
                                marker=dict(color=color, size=[8, 11], symbol=["circle-open", "diamond"]),
                                name=f"{lat}° latitude", hovertemplate="%{x:.2f}°, %{y}°<extra></extra>"))
    fig.update_layout(legend=dict(orientation="h", y=-0.25))
    return fig


def coverage_figure(weight):
    fig = go.Figure(go.Heatmap(x=LONGITUDES, y=LATITUDES, z=weight,
                             colorscale=[[0, "#d5d9df"], [0.01, "#d7eee7"], [0.5, "#359b81"], [1, "#173f36"]],
                             zmin=0, zmax=2, colorbar=dict(title="Weight"),
                             hovertemplate="%{x}°, %{y}°<br>Sample weight %{z:.3f}<extra></extra>"))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10),
                      xaxis_title="Carrington longitude (°)", yaxis_title="Latitude (°)")
    return fig


def time_strip(selected, reference_time, current_time):
    times = observation_time(LONGITUDES)
    fig = go.Figure(go.Scatter(x=LONGITUDES, y=times, mode="lines",
                              line=dict(color="#008a77"), name="Column observation time",
                              hovertemplate="%{x:.0f}°<br>Observed at %{y:.5f} d<extra></extra>"))
    fig.add_hline(y=reference_time, line_dash="dash", line_color="#7953bc",
                  annotation_text="Reference time", annotation_position="top left")
    fig.add_hline(y=current_time, line_color="#cc7c15", annotation_text="Observation clock",
                  annotation_position="bottom right")
    fig.add_trace(go.Scatter(x=[selected], y=[observation_time(selected)], mode="markers",
                            marker=dict(size=10, color="#7953bc"), name="Selected column"))
    fig.update_layout(height=240, margin=dict(l=10, r=10, t=20, b=10), showlegend=False,
                      xaxis_title="Selected longitude (°)", yaxis_title="Observation time (days)")
    fig.update_xaxes(range=[0, 359], tickvals=[0, 90, 180, 270, 359])
    return fig
