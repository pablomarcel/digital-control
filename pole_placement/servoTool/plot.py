from __future__ import annotations

def plot_matplotlib(y, savefig=None, show=False, title='Servo Response'):
    import matplotlib.pyplot as plt
    k = list(range(len(y)))
    plt.figure(figsize=(8, 4.5))
    plt.scatter(k, y, s=60)
    ymin = min(0.0, min(y) - 0.1) if y else 0.0
    ymax = max(1.05, max(y) + 0.1) if y else 1.05
    plt.ylim(ymin, ymax)
    plt.title(title); plt.xlabel('k'); plt.ylabel('value')
    plt.grid(True, alpha=0.3)
    if savefig: plt.savefig(savefig, dpi=200, bbox_inches='tight')
    if show: plt.show()
    plt.close()

def plot_plotly(y, html, open_after=False, title='Servo Response'):
    import plotly.graph_objects as go  # type: ignore
    import webbrowser, os
    k = list(range(len(y)))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=k, y=y, mode='markers', name='y(k)'))
    fig.update_layout(title=title, xaxis_title='k', yaxis_title='value', template='plotly_white')
    fig.write_html(html, include_plotlyjs='cdn', full_html=True)
    if open_after:
        try: webbrowser.open('file://' + os.path.abspath(html))
        except Exception: pass
