# Visual Reports

On-demand visual reporting for swarm activity. Generates professional charts, diagrams, and dashboards.

## Quick Start

```python
from lib.visual_reporter import VisualReporter

reporter = VisualReporter()

# Generate reports
reporter.generate_report("swarm_health")           # HTML dashboard
reporter.generate_report("orchestration_flow")     # Mermaid diagram
reporter.generate_report("last_24h_activity")      # Plotly timeline
reporter.generate_report("agent_hierarchy")        # Mermaid org chart
reporter.generate_report("task_dag")               # Mermaid flowchart
reporter.generate_report("cost_analysis")          # Plotly pie chart
reporter.generate_report("latency_analysis")       # Plotly bar chart
```

## Report Types

| Type | Output | Description |
|------|--------|-------------|
| `swarm_health` | HTML Dashboard | Node status, tasks, cost tracking |
| `orchestration_flow` | Mermaid Diagram | Swarm data flow |
| `agent_hierarchy` | Mermaid Diagram | Agent relationships |
| `task_dag` | Mermaid Diagram | Task execution flow |
| `last_24h_activity` | Plotly Chart | Timeline with cost overlay |
| `cost_analysis` | Plotly Chart | Cost breakdown by model |
| `latency_analysis` | Plotly Chart | Latency comparison |

## Output Location

Reports saved to: `~/.openclaw/reports/YYYY-MM-DD_HH-MM_report-name.html`

All reports are self-contained HTML with embedded CSS/JS.
