import jinja2

template = jinja2.Template("""
{% for plot in plots %}
{% if plot.path %}
\begin{figure}[H]
    \centering
    \includegraphics[width=0.8\textwidth]{ {{- plot.path -}} }
    \caption{ {{ plot.caption }} }
\end{figure}
{% endif %}
{% endfor %}
""")

print(template.render(plots=[{"path": "", "caption": "Simulated Curve"}]))
