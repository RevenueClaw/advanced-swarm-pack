#!/usr/bin/env python3
"""
Visual Reporter - On-demand visual reports for swarm activity.

Generates professional visualizations including:
- Mermaid diagrams (flowcharts, DAGs, hierarchies)
- HTML status dashboards (self-contained)
- Timeline/activity charts
- Plotly charts (cost, latency, token usage)

Author: RockClaw
Version: 1.0.0
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import hashlib


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    title: str
    report_type: str
    timestamp: str
    data_sources: List[str]
    

class VisualReporter:
    """
    Main interface for generating visual swarm reports.
    
    Usage:
        reporter = VisualReporter()
        path = reporter.generate_report("swarm_health")
        path = reporter.generate_report("orchestration_flow")
    """
    
    def __init__(self, reports_dir: Optional[Path] = None):
        self.reports_dir = reports_dir or Path.home() / ".openclaw/reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        # Color scheme (professional dark theme)
        self.colors = {
            "primary": "#3b82f6",      # Blue
            "success": "#22c55e",      # Green
            "warning": "#f59e0b",      # Amber
            "danger": "#ef4444",       # Red
            "neutral": "#6b7280",      # Gray
            "bg_dark": "#111827",      # Dark bg
            "bg_card": "#1f2937",      # Card bg
            "text": "#f9fafb",         # Light text
            "text_muted": "#9ca3af"    # Muted text
        }
    
    def generate_report(self, report_type: str, **kwargs) -> Path:
        """
        Generate a visual report of the specified type.
        
        Args:
            report_type: Type of report (swarm_health, orchestration_flow, etc.)
            **kwargs: Additional parameters specific to report type
            
        Returns:
            Path to generated HTML file
        """
        timestamp = datetime.now()
        report_id = f"{timestamp.strftime('%Y-%m-%d_%H-%M')}_{report_type}"
        
        generators = {
            "orchestration_flow": self._generate_orchestration_flow,
            "swarm_health": self._generate_swarm_health,
            "last_24h_activity": self._generate_activity_timeline,
            "cost_analysis": self._generate_cost_analysis,
            "latency_analysis": self._generate_latency_analysis,
            "agent_hierarchy": self._generate_agent_hierarchy,
            "task_dag": self._generate_task_dag,
        }
        
        if report_type not in generators:
            raise ValueError(f"Unknown report type: {report_type}. "
                           f"Available: {list(generators.keys())}")
        
        html_content = generators[report_type](report_id, timestamp, **kwargs)
        
        # Save report
        output_path = self.reports_dir / f"{report_id}.html"
        with open(output_path, "w") as f:
            f.write(html_content)
        
        # Print SCP command for easy download
        self._print_scp_command(output_path)
        
        return output_path
    
    def _print_scp_command(self, report_path: Path):
        """Print SCP command to download report to local machine."""
        # Get hostname and user for SCP
        import socket
        hostname = socket.gethostname()
        username = os.getenv('USER', 'rock')
        remote_path = report_path.expanduser().resolve()
        
        # Determine local Downloads folder
        local_path = f"~/Downloads/{report_path.name}"
        
        # Build SCP commands for both directions
        scp_from = f"scp {username}@{hostname}:{remote_path} {local_path}"
        
        print("\n" + "=" * 60)
        print("📋 DOWNLOAD COMMAND (copy-paste to local terminal):")
        print("=" * 60)
        print(f"\n{scp_from}")
        print(f"\n# Then open with:")
        print(f"open ~/Downloads/{report_path.name}")
        print("=" * 60)
    
    def _generate_orchestration_flow(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate Mermaid flowchart of orchestration flow."""
        mermaid_code = """
flowchart TB
    subgraph Leader["🎯 Leader Node (Rock 5B)"]
        A[Task Orchestrator] --> B[Supervisor Agent]
        B --> C[Task Queue]
    end
    
    subgraph Workers["👷 Worker Nodes"]
        D[GPU Worker<br/>Omen - CUDA]
        E[Light Worker<br/>Pi 5 - Scripts]
    end
    
    subgraph Storage["💾 Storage"]
        F[(Long-term Memory)]
        G[(Version Registry)]
        H[(Cost Logs)]
    end
    
    C -->|Heavy Compute| D
    C -->|Light Tasks| E
    D -->|Results| A
    E -->|Results| A
    A -->|Persist| F
    B -->|Track| G
    D -->|Log| H
    E -->|Log| H
    
    style Leader fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#fff
    style Workers fill:#22c55e,stroke:#16a34a,stroke-width:2px,color:#fff
    style Storage fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#fff
"""
        return self._wrap_mermaid_html(report_id, "Swarm Orchestration Flow", mermaid_code, timestamp)
    
    def _generate_swarm_health(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate HTML dashboard of swarm health."""
        # Simulated data - in production would read from actual sources
        nodes_data = [
            {"name": "rock-5b-leader", "status": "healthy", "cpu": 45, "ram": 62, "uptime": "10d 4h", "tasks": 12},
            {"name": "omen-gpu", "status": "healthy", "cpu": 32, "ram": 58, "uptime": "10d 4h", "tasks": 4},
            {"name": "openclaw-pi", "status": "healthy", "cpu": 28, "ram": 45, "uptime": "10d 4h", "tasks": 8},
        ]
        
        recent_tasks = [
            {"name": "income-automation-audit", "status": "completed", "duration": "8m 12s"},
            {"name": "session_health_monitor", "status": "running", "duration": "2m 30s"},
            {"name": "config_backup", "status": "completed", "duration": "15s"},
        ]
        
        cost_data = {"daily": "$1.24", "monthly": "$42.18", "budget_remaining": "$57.82"}
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Swarm Health Dashboard - {timestamp.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            color: #f9fafb;
            min-height: 100vh;
            padding: 2rem;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
            background: linear-gradient(90deg, #3b82f6, #22c55e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .header .timestamp {{
            color: #9ca3af;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 1.5rem;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .card {{
            background: rgba(31, 41, 55, 0.8);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid rgba(75, 85, 99, 0.4);
            backdrop-filter: blur(10px);
        }}
        .card h2 {{
            font-size: 1.25rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .card h2 .icon {{
            font-size: 1.5rem;
        }}
        .node {{
            background: rgba(17, 24, 39, 0.8);
            border-radius: 8px;
            padding: 1rem;
            margin-bottom: 1rem;
            border-left: 4px solid #22c55e;
        }}
        .node.warning {{
            border-left-color: #f59e0b;
        }}
        .node.danger {{
            border-left-color: #ef4444;
        }}
        .node-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }}
        .node-name {{
            font-weight: 600;
            font-size: 1.1rem;
        }}
        .status-badge {{
            background: #22c55e;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .status-badge.warning {{
            background: #f59e0b;
        }}
        .status-badge.danger {{
            background: #ef4444;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 0.75rem;
            margin-top: 0.75rem;
        }}
        .metric {{
            text-align: center;
        }}
        .metric-value {{
            font-size: 1.25rem;
            font-weight: 700;
            color: #3b82f6;
        }}
        .metric-label {{
            font-size: 0.75rem;
            color: #9ca3af;
            text-transform: uppercase;
        }}
        .task {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.75rem;
            background: rgba(17, 24, 39, 0.5);
            border-radius: 6px;
            margin-bottom: 0.5rem;
        }}
        .task-status {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}
        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        .status-dot.completed {{
            background: #22c55e;
        }}
        .status-dot.running {{
            background: #3b82f6;
            animation: pulse 1.5s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        .cost-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            text-align: center;
        }}
        .cost-item {{
            background: rgba(17, 24, 39, 0.8);
            padding: 1.5rem;
            border-radius: 8px;
        }}
        .cost-value {{
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }}
        .cost-value.positive {{
            color: #22c55e;
        }}
        .cost-value.warning {{
            color: #f59e0b;
        }}
        .cost-value.danger {{
            color: #ef4444;
        }}
        .cost-label {{
            color: #9ca3af;
            font-size: 0.875rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🦑 Swarm Health Dashboard</h1>
        <div class="timestamp">{timestamp.strftime('%Y-%m-%d %H:%M:%S EDT')}</div>
    </div>
    
    <div class="grid">
        <div class="card">
            <h2><span class="icon">🖥️</span> Node Status</h2>
            {''.join([
                f'<div class="node">'
                f'<div class="node-header">'
                f'<span class="node-name">{n["name"]}</span>'
                f'<span class="status-badge">{n["status"]}</span>'
                f'</div>'
                f'<div class="metrics">'
                f'<div class="metric"><div class="metric-value">{n["cpu"]}%</div><div class="metric-label">CPU</div></div>'
                f'<div class="metric"><div class="metric-value">{n["ram"]}%</div><div class="metric-label">RAM</div></div>'
                f'<div class="metric"><div class="metric-value">{n["uptime"]}</div><div class="metric-label">Uptime</div></div>'
                f'<div class="metric"><div class="metric-value">{n["tasks"]}</div><div class="metric-label">Tasks</div></div>'
                f'</div></div>'
                for n in nodes_data
            ])}
        </div>
        
        <div class="card">
            <h2><span class="icon">⚡</span> Recent Tasks</h2>
            {''.join([
                f'<div class="task">'
                f'<span>{t["name"]}</span>'
                f'<div class="task-status">'
                f'<span class="status-dot {t["status"]}"></span>'
                f'<span>{t["status"]} • {t["duration"]}</span>'
                f'</div></div>'
                for t in recent_tasks
            ])}
        </div>
        
        <div class="card" style="grid-column: span 2;">
            <h2><span class="icon">💰</span> Cost Tracking</h2>
            <div class="cost-grid">
                <div class="cost-item">
                    <div class="cost-value positive">{cost_data['daily']}</div>
                    <div class="cost-label">Today</div>
                </div>
                <div class="cost-item">
                    <div class="cost-value warning">{cost_data['monthly']}</div>
                    <div class="cost-label">This Month</div>
                </div>
                <div class="cost-item">
                    <div class="cost-value">{cost_data['budget_remaining']}</div>
                    <div class="cost-label">Budget Remaining</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _generate_activity_timeline(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate timeline chart of last 24h activity."""
        # Sample hourly data
        hours = [(timestamp - timedelta(hours=i)).strftime('%H:%M') for i in range(24, 0, -1)]
        tasks = [3, 5, 2, 1, 0, 0, 1, 4, 7, 9, 12, 8, 6, 5, 4, 6, 8, 10, 7, 5, 3, 2, 4, 5]
        costs = [0.12, 0.35, 0.08, 0.05, 0, 0, 0.06, 0.28, 0.52, 0.89, 1.24, 0.76, 0.58, 0.41, 0.33, 0.48, 0.67, 0.94, 0.62, 0.38, 0.21, 0.15, 0.29, 0.42]
        
        # Create self-contained Plotly chart
        plotly_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Activity Timeline - {timestamp.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ margin: 0; background: #111827; font-family: sans-serif; }}
        #chart {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var trace1 = {{
            x: {json.dumps(hours)},
            y: {json.dumps(tasks)},
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Tasks Executed',
            line: {{ color: '#3b82f6', width: 3 }},
            marker: {{ size: 8, color: '#3b82f6' }}
        }};
        var trace2 = {{
            x: {json.dumps(hours)},
            y: {json.dumps(costs)},
            type: 'scatter',
            mode: 'lines',
            name: 'Cost ($)',
            yaxis: 'y2',
            line: {{ color: '#22c55e', width: 2, dash: 'dash' }}
        }};
        var layout = {{
            title: {{
                text: '24-Hour Swarm Activity',
                font: {{ color: '#f9fafb', size: 24 }}
            }},
            paper_bgcolor: '#111827',
            plot_bgcolor: '#1f2937',
            font: {{ color: '#f9fafb' }},
            xaxis: {{
                title: 'Hour',
                gridcolor: '#374151',
                tickfont: {{ color: '#9ca3af' }}
            }},
            yaxis: {{
                title: 'Tasks',
                gridcolor: '#374151',
                tickfont: {{ color: '#9ca3af' }}
            }},
            yaxis2: {{
                title: 'Cost ($)',
                overlaying: 'y',
                side: 'right',
                tickfont: {{ color: '#22c55e' }}
            }},
            legend: {{ font: {{ color: '#f9fafb' }} }},
            margin: {{ t: 80, r: 80 }}
        }};
        Plotly.newPlot('chart', [trace1, trace2], layout, {{responsive: true}});
    </script>
</body>
</html>"""
        return plotly_html
    
    def _generate_cost_analysis(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate cost breakdown with Plotly pie chart."""
        data = {
            "models": ["kimi-k2.5", "gpt-4o", "o1-preview", "ollama-local"],
            "costs": [28.45, 12.30, 1.43, 0.00],
            "requests": [485, 123, 12, 89]
        }
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Cost Analysis - {timestamp.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ margin: 0; padding: 2rem; background: #111827; font-family: sans-serif; }}
        #chart {{ width: 100%; height: 70vh; }}
        .summary {{ color: #f9fafb; font-size: 1.2rem; margin-top: 1rem; text-align: center; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <div class="summary">Total Spend: ${'%.2f' % sum(data['costs'])} | Budget Remaining: ${'%.2f' % (100 - sum(data['costs']))}</div>
    <script>
        var data = [{{
            values: {data['costs']},
            labels: {json.dumps(data['models'])},
            type: 'pie',
            hole: 0.4,
            marker: {{
                colors: ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444']
            }},
            textinfo: 'label+percent',
            textposition: 'outside'
        }}];
        var layout = {{
            title: {{
                text: 'Cost Breakdown by Model',
                font: {{ color: '#f9fafb', size: 24 }}
            }},
            paper_bgcolor: '#111827',
            font: {{ color: '#f9fafb' }},
            showlegend: true,
            legend: {{ font: {{ color: '#9ca3af' }} }}
        }};
        Plotly.newPlot('chart', data, layout);
    </script>
</body>
</html>"""
    
    def _generate_latency_analysis(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate latency comparison bar chart."""
        models = ["kimi-k2.5", "gpt-4o", "llama3:8b", "phi3:medium"]
        avg_latency = [850, 1200, 3500, 2800]
        p95_latency = [1200, 1800, 5200, 4100]
        
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Latency Analysis - {timestamp.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        body {{ margin: 0; background: #111827; font-family: sans-serif; }}
        #chart {{ width: 100%; height: 100vh; }}
    </style>
</head>
<body>
    <div id="chart"></div>
    <script>
        var trace1 = {{
            x: {json.dumps(models)},
            y: {avg_latency},
            name: 'Avg Latency',
            type: 'bar',
            marker: {{ color: '#3b82f6' }}
        }};
        var trace2 = {{
            x: {json.dumps(models)},
            y: {p95_latency},
            name: 'P95 Latency',
            type: 'bar',
            marker: {{ color: '#f59e0b' }}
        }};
        var layout = {{
            title: {{
                text: 'Model Latency Comparison (ms)',
                font: {{ color: '#f9fafb', size: 24 }}
            }},
            paper_bgcolor: '#111827',
            plot_bgcolor: '#1f2937',
            font: {{ color: '#f9fafb' }},
            barmode: 'group',
            yaxis: {{
                title: 'Milliseconds',
                gridcolor: '#374151'
            }},
            legend: {{ font: {{ color: '#f9fafb' }} }}
        }};
        Plotly.newPlot('chart', [trace1, trace2], layout, {{responsive: true}});
    </script>
</body>
</html>"""
    
    def _generate_agent_hierarchy(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate Mermaid diagram of agent hierarchy."""
        mermaid_code = """
graph TD
    A[🎯 Swarm Leader<br/>Rock 5B] --> B[📋 Supervisor Agent]
    A --> C[💰 Cost Monitor]
    A --> D[🏥 Health Monitor]
    
    B --> E[🤖 Task Workers]
    B --> F[💾 Memory Manager]
    B --> G[🔄 Version Manager]
    
    E --> H[⚡ GPU Worker<br/>Heavy inference]
    E --> I[🔧 Light Worker<br/>Quick scripts]
    
    style A fill:#3b82f6,stroke:#2563eb,color:#fff
    style B fill:#22c55e,stroke:#16a34a,color:#fff
    style E fill:#f59e0b,stroke:#d97706,color:#fff
    style C fill:#8b5cf6,stroke:#7c3aed,color:#fff
    style D fill:#ef4444,stroke:#dc2626,color:#fff
"""
        return self._wrap_mermaid_html(report_id, "Agent Hierarchy", mermaid_code, timestamp)
    
    def _generate_task_dag(self, report_id: str, timestamp: datetime, **kwargs) -> str:
        """Generate Mermaid diagram of task dependencies."""
        mermaid_code = """
flowchart LR
    subgraph Input["📥 Input"]
        A["User Query"]
    end
    
    subgraph Processing["⚙️ Processing"]
        B["Preference Check"] --> C["Uncertainty Assess"]
        C --> D{"Debate?"}
        D -->|Yes| E[Multi-Agent Debate]
        D -->|No| F[Direct Execution]
        E --> F
    end
    
    subgraph Execution["🚀 Execution"]
        F --> G[Task Decomposition]
        G --> H[Worker Assignment]
        H --> I[Parallel Execution]
    end
    
    subgraph Output["📤 Output"]
        I --> J[Result Synthesis]
        J --> K[Feedback Capture]
        K --> L["User Response"]
    end
    
    A --> B
    
    style Input fill:#3b82f6,color:#fff
    style Processing fill:#f59e0b,color:#fff
    style Execution fill:#22c55e,color:#fff
    style Output fill:#8b5cf6,color:#fff
"""
        return self._wrap_mermaid_html(report_id, "Task Execution DAG", mermaid_code, timestamp)
    
    def _wrap_mermaid_html(self, report_id: str, title: str, mermaid_code: str, timestamp: datetime) -> str:
        """Wrap Mermaid code in full HTML page."""
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title} - {timestamp.strftime('%Y-%m-%d')}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 2rem;
            background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            min-height: 100vh;
        }}
        .header {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            color: #f9fafb;
            margin: 0 0 0.5rem 0;
        }}
        .header .timestamp {{
            color: #9ca3af;
        }}
        .mermaid-container {{
            background: rgba(31, 41, 55, 0.8);
            border-radius: 12px;
            padding: 2rem;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 60vh;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{title}</h1>
        <div class="timestamp">{timestamp.strftime('%Y-%m-%d %H:%M:%S EDT')}</div>
    </div>
    <div class="mermaid-container">
        <pre class="mermaid">
{mermaid_code.strip()}
        </pre>
    </div>
    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                primaryColor: '#3b82f6',
                primaryTextColor: '#f9fafb',
                primaryBorderColor: '#2563eb',
                lineColor: '#9ca3af',
                secondaryColor: '#1f2937',
                tertiaryColor: '#374151'
            }}
        }});
    </script>
</body>
</html>"""


# Verification test
if __name__ == "__main__":
    import tempfile
    
    print("=" * 60)
    print("VISUAL REPORTER - VERIFICATION TEST")
    print("=" * 60)
    
    test_dir = Path(tempfile.mkdtemp())
    reporter = VisualReporter(reports_dir=test_dir)
    
    print(f"\n[1] Test orchestration_flow report...")
    path1 = reporter.generate_report("orchestration_flow")
    assert path1.exists()
    assert "mermaid" in path1.read_text()
    print(f"    ✓ Created: {path1.name}")
    
    print(f"\n[2] Test swarm_health report...")
    path2 = reporter.generate_report("swarm_health")
    assert path2.exists()
    assert "Swarm Health Dashboard" in path2.read_text()
    print(f"    ✓ Created: {path2.name}")
    
    print(f"\n[3] Test activity timeline report...")
    path3 = reporter.generate_report("last_24h_activity")
    assert path3.exists()
    assert "plotly" in path3.read_text()
    print(f"    ✓ Created: {path3.name}")
    
    print(f"\n[4] Test agent hierarchy report...")
    path4 = reporter.generate_report("agent_hierarchy")
    assert path4.exists()
    print(f"    ✓ Created: {path4.name}")
    
    print(f"\n[5] Test task DAG report...")
    path5 = reporter.generate_report("task_dag")
    assert path5.exists()
    print(f"    ✓ Created: {path5.name}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print(f"\nReports saved to: {test_dir}")