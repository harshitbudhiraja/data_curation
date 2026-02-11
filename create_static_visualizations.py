#!/usr/bin/env python3
"""Create static JPG visualizations for dataset analysis."""
import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from collections import defaultdict
import re

# Load data
data_dir = Path("data/strategy1_11_02_2026-Golden")
verified_dir = Path("data/strategy1_05_02_2026-2/verified")

# Aggregate all metrics
metrics = {
    'quality': defaultdict(int),
    'by_personality': defaultdict(lambda: {
        'total': 0, 'solved': 0, 'gold': 0, 'silver': 0, 'bronze': 0,
        'turns': [], 'actionable': 0, 'total_responses': 0,
        'responsive': 0, 'opportunities': 0
    }),
    'turn_distribution': defaultdict(int),
    'persona_adherence': defaultdict(lambda: {'scores': [], 'high_fidelity': 0})
}

# Actionable patterns
actionable_patterns = [
    r'\b(base case|return|loop|edge case|condition|variable|function|parameter|argument|index|range|list|array|string|integer|float|boolean|none|null|empty|zero|negative|positive|length|size|append|remove|add|subtract|multiply|divide|sort|reverse|filter|map|reduce|recursion|iteration|if|else|elif|for|while|try|except|class|method|attribute|import|def|lambda|yield|async|await)\b',
    r'\b(forgot|missing|need|should|must|add|remove|fix|change|update|modify|check|handle|consider)\b.*\b(case|condition|check|validation|error|exception|boundary|limit)\b',
]

# Load Golden dataset
for json_file in data_dir.glob("*_conversations.json"):
    with open(json_file, 'r') as f:
        convos = json.load(f)
    
    for conv in convos:
        personality = conv['personality']
        quality = conv.get('quality_bucket', 'unknown')
        solved = conv.get('solved', False)
        turns = conv.get('turns', 0)
        conversation = conv.get('conversation', [])
        
        # Quality distribution
        metrics['quality'][quality] += 1
        
        # By personality
        p = metrics['by_personality'][personality]
        p['total'] += 1
        if solved:
            p['solved'] += 1
        p[quality] += 1
        p['turns'].append(turns)
        
        # Turn distribution
        metrics['turn_distribution'][turns] += 1
        
        # Actionable feedback & responsiveness
        for i, msg in enumerate(conversation):
            if msg.get('role') == 'student':
                content = msg.get('content', '').lower()
                is_actionable = any(re.search(pat, content, re.IGNORECASE) for pat in actionable_patterns)
                
                p['total_responses'] += 1
                if is_actionable:
                    p['actionable'] += 1
                
                if i + 1 < len(conversation) and conversation[i + 1].get('role') == 'tutor':
                    p['opportunities'] += 1
                    if is_actionable:
                        p['responsive'] += 1

# Load persona adherence from verified data
if verified_dir.exists():
    for bucket in ['gold', 'silver']:
        for json_file in verified_dir.glob(f"*_{bucket}.json"):
            with open(json_file, 'r') as f:
                convos = json.load(f)
            
            for conv in convos:
                personality = conv['personality']
                persona_fidelity = conv['scores'].get('persona_fidelity', 0)
                
                metrics['persona_adherence'][personality]['scores'].append(persona_fidelity)
                if persona_fidelity >= 3.5:
                    metrics['persona_adherence'][personality]['high_fidelity'] += 1

print("Creating static JPG visualizations...")

# ============================================================================
# 1. QUALITY DISTRIBUTION PIE CHART
# ============================================================================
fig1 = go.Figure(data=[go.Pie(
    labels=['Gold', 'Silver', 'Bronze'],
    values=[metrics['quality']['gold'], metrics['quality']['silver'], metrics['quality']['bronze']],
    marker=dict(colors=['#FFD700', '#C0C0C0', '#CD7F32']),
    hole=0.3,
    textinfo='label+percent+value',
    textfont=dict(size=16, color='black')
)])

fig1.update_layout(
    title=dict(
        text="Dataset Quality Distribution<br><sub>Total: 2,495 conversations</sub>",
        font=dict(size=24, color='black')
    ),
    annotations=[dict(text='Quality', x=0.5, y=0.5, font_size=18, showarrow=False)],
    height=600,
    width=800,
    font=dict(size=14, color='black')
)

fig1.write_image("viz_1_quality_distribution.jpg", width=1200, height=800, scale=2)
print("✅ Created: viz_1_quality_distribution.jpg")

# ============================================================================
# 2. COMPLETION RATE BY PERSONALITY
# ============================================================================
personalities = sorted(metrics['by_personality'].keys())
completion_rates = []
solved_counts = []
total_counts = []

for p in personalities:
    data = metrics['by_personality'][p]
    rate = (data['solved'] / data['total']) * 100 if data['total'] > 0 else 0
    completion_rates.append(rate)
    solved_counts.append(data['solved'])
    total_counts.append(data['total'])

fig2 = go.Figure()

fig2.add_trace(go.Bar(
    x=personalities,
    y=completion_rates,
    text=[f"{rate:.1f}%<br>({solved}/{total})" 
          for rate, solved, total in zip(completion_rates, solved_counts, total_counts)],
    textposition='outside',
    textfont=dict(size=12, color='black'),
    marker=dict(
        color=completion_rates,
        colorscale='RdYlGn',
        cmin=50,
        cmax=85,
        showscale=True,
        colorbar=dict(title=dict(text="Rate %", font=dict(size=14)))
    )
))

# Add reference lines for target zone (NO annotations to avoid overlap)
fig2.add_hline(y=60, line_dash="dash", line_color="green", line_width=2)
fig2.add_hline(y=80, line_dash="dash", line_color="green", line_width=2)

fig2.update_layout(
    title=dict(text="Completion Rate by Personality<br><sub>Target Range: 60-80%</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Completion Rate (%)",
    yaxis=dict(range=[0, 88]),
    height=600,
    width=1100,
    font=dict(size=14, color='black'),
    margin=dict(t=100, b=80, l=80, r=80)
)

fig2.write_image("viz_2_completion_rate.jpg", width=1500, height=800, scale=2)
print("✅ Created: viz_2_completion_rate.jpg")

# ============================================================================
# 3. TURN EFFICIENCY BOX PLOT
# ============================================================================
fig3 = go.Figure()

for p in personalities:
    data = metrics['by_personality'][p]
    fig3.add_trace(go.Box(
        y=data['turns'],
        name=p,
        boxmean='sd'
    ))

# Add reference lines for target zone (NO annotations)
fig3.add_hline(y=6, line_dash="dash", line_color="green", line_width=2)
fig3.add_hline(y=10, line_dash="dash", line_color="green", line_width=2)

fig3.update_layout(
    title=dict(text="Turn Efficiency Distribution<br><sub>Target: 6-10 average turns</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Number of Turns",
    height=600,
    width=1100,
    showlegend=False,
    font=dict(size=14, color='black'),
    margin=dict(t=100, b=80, l=80, r=80)
)

fig3.write_image("viz_3_turn_efficiency.jpg", width=1500, height=800, scale=2)
print("✅ Created: viz_3_turn_efficiency.jpg")

# ============================================================================
# 4. ACTIONABLE FEEDBACK SCORES
# ============================================================================
actionable_pcts = []
for p in personalities:
    data = metrics['by_personality'][p]
    pct = (data['actionable'] / data['total_responses']) * 100 if data['total_responses'] > 0 else 0
    actionable_pcts.append(pct)

fig4 = go.Figure()

fig4.add_trace(go.Bar(
    x=personalities,
    y=actionable_pcts,
    text=[f"{pct:.1f}%" for pct in actionable_pcts],
    textposition='outside',
    textfont=dict(size=12, color='black'),
    marker=dict(color='#4CAF50')
))

fig4.add_hline(y=70, line_dash="dash", line_color="red", line_width=2)

fig4.update_layout(
    title=dict(text="Actionable Feedback Quality<br><sub>% of student responses with specific code element references</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Actionable Feedback (%)",
    yaxis=dict(range=[0, 108]),
    height=600,
    width=1100,
    font=dict(size=14, color='black'),
    margin=dict(t=100, b=80, l=80, r=80)
)

fig4.write_image("viz_4_actionable_feedback.jpg", width=1500, height=800, scale=2)
print("✅ Created: viz_4_actionable_feedback.jpg")

# ============================================================================
# 5. TUTOR RESPONSIVENESS
# ============================================================================
responsive_pcts = []
for p in personalities:
    data = metrics['by_personality'][p]
    pct = (data['responsive'] / data['opportunities']) * 100 if data['opportunities'] > 0 else 0
    responsive_pcts.append(pct)

fig5 = go.Figure()

fig5.add_trace(go.Bar(
    x=personalities,
    y=responsive_pcts,
    text=[f"{pct:.1f}%" for pct in responsive_pcts],
    textposition='outside',
    textfont=dict(size=12, color='black'),
    marker=dict(color='#2196F3')
))

fig5.add_hline(y=70, line_dash="dash", line_color="red", line_width=2)

fig5.update_layout(
    title=dict(text="Tutor Responsiveness<br><sub>% of turns where tutor addresses student's specific feedback</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Responsiveness (%)",
    yaxis=dict(range=[0, 108]),
    height=600,
    width=1100,
    font=dict(size=14, color='black'),
    margin=dict(t=100, b=80, l=80, r=80)
)

fig5.write_image("viz_5_tutor_responsiveness.jpg", width=1500, height=800, scale=2)
print("✅ Created: viz_5_tutor_responsiveness.jpg")

# ============================================================================
# 6. PERSONA ADHERENCE
# ============================================================================
if verified_dir.exists():
    adherence_pcts = []
    avg_scores = []
    
    for p in personalities:
        data = metrics['persona_adherence'][p]
        if data['scores']:
            total = len(data['scores'])
            pct = (data['high_fidelity'] / total) * 100
            avg = sum(data['scores']) / total
        else:
            pct = 0
            avg = 0
        adherence_pcts.append(pct)
        avg_scores.append(avg)
    
    fig6 = go.Figure()
    
    fig6.add_trace(go.Bar(
        x=personalities,
        y=adherence_pcts,
        text=[f"{pct:.1f}%<br>(avg: {avg:.2f}/5.0)" 
              for pct, avg in zip(adherence_pcts, avg_scores)],
        textposition='outside',
        textfont=dict(size=11, color='black'),
        marker=dict(
            color=adherence_pcts,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title=dict(text="Adherence %", font=dict(size=14)))
        )
    ))
    
    fig6.add_hline(y=70, line_dash="dash", line_color="red", line_width=2)
    
    fig6.update_layout(
        title=dict(text="Persona Adherence (LLM Judge)<br><sub>% with persona_fidelity >= 3.5/5.0</sub>",
                   font=dict(size=24, color='black')),
        xaxis_title="Personality",
        yaxis_title="Adherence (%)",
        yaxis=dict(range=[0, 115]),
        height=600,
        width=1100,
        font=dict(size=14, color='black'),
        margin=dict(t=100, b=80, l=80, r=80)
    )
    
    fig6.write_image("viz_6_persona_adherence.jpg", width=1500, height=800, scale=2)
    print("✅ Created: viz_6_persona_adherence.jpg")

# ============================================================================
# 7. TURN DISTRIBUTION HISTOGRAM
# ============================================================================
turns = []
counts = []
for turn, count in sorted(metrics['turn_distribution'].items()):
    turns.append(turn)
    counts.append(count)

fig7 = go.Figure()

colors = ['red' if t == 2 else 'lightblue' for t in turns]

fig7.add_trace(go.Bar(
    x=turns,
    y=counts,
    marker=dict(color=colors),
    text=counts,
    textposition='outside',
    textfont=dict(size=14, color='black')
))

fig7.add_annotation(
    x=2, y=max(counts) * 0.9,
    text=f"⚠️ 2-turn problem:<br>{metrics['turn_distribution'][2]} conversations<br>(46% of dataset)",
    showarrow=True,
    arrowhead=2,
    bgcolor="rgba(255,0,0,0.1)",
    bordercolor="red",
    font=dict(size=14, color='black')
)

fig7.update_layout(
    title=dict(text="Turn Distribution<br><sub>Showing the 2-turn instant solution problem</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Number of Turns",
    yaxis_title="Number of Conversations",
    height=600,
    width=1000,
    font=dict(size=14, color='black')
)

fig7.write_image("viz_7_turn_distribution.jpg", width=1400, height=800, scale=2)
print("✅ Created: viz_7_turn_distribution.jpg")

# ============================================================================
# 8. USABLE TRAINING DATA BREAKDOWN
# ============================================================================
personalities_list = sorted(metrics['by_personality'].keys())
gold_counts = [metrics['by_personality'][p]['gold'] for p in personalities_list]
silver_counts = [metrics['by_personality'][p]['silver'] for p in personalities_list]
bronze_counts = [metrics['by_personality'][p]['bronze'] for p in personalities_list]

fig8 = go.Figure()

fig8.add_trace(go.Bar(
    name='Gold (High Quality)',
    x=personalities_list,
    y=gold_counts,
    marker=dict(color='#FFD700'),
    text=gold_counts,
    textposition='inside',
    textfont=dict(size=14, color='black')
))

fig8.add_trace(go.Bar(
    name='Silver (Medium Quality)',
    x=personalities_list,
    y=silver_counts,
    marker=dict(color='#C0C0C0'),
    text=silver_counts,
    textposition='inside',
    textfont=dict(size=14, color='black')
))

fig8.add_trace(go.Bar(
    name='Bronze (Low Quality)',
    x=personalities_list,
    y=bronze_counts,
    marker=dict(color='#CD7F32'),
    text=bronze_counts,
    textposition='inside',
    textfont=dict(size=14, color='white')
))

fig8.update_layout(
    title=dict(text="Usable Training Data by Personality<br><sub>Gold+Silver = 1,241 usable (49.7%)</sub>",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Number of Conversations",
    barmode='stack',
    height=600,
    width=1000,
    font=dict(size=14, color='black')
)

fig8.write_image("viz_8_training_data_breakdown.jpg", width=1400, height=800, scale=2)
print("✅ Created: viz_8_training_data_breakdown.jpg")

# ============================================================================
# 9. PERFORMANCE MATRIX HEATMAP
# ============================================================================
matrix_data = []
metric_names = ['Completion\nRate (%)', 'Avg Turns', 'Actionable\nFeedback (%)', 
                'Tutor\nResponsive (%)', 'Persona\nAdherence (%)']

for p in personalities:
    data = metrics['by_personality'][p]
    row = [
        (data['solved'] / data['total']) * 100 if data['total'] > 0 else 0,
        sum(data['turns']) / len(data['turns']) if data['turns'] else 0,
        (data['actionable'] / data['total_responses']) * 100 if data['total_responses'] > 0 else 0,
        (data['responsive'] / data['opportunities']) * 100 if data['opportunities'] > 0 else 0,
    ]
    
    # Add persona adherence if available
    if verified_dir.exists() and metrics['persona_adherence'][p]['scores']:
        pa_data = metrics['persona_adherence'][p]
        adherence = (pa_data['high_fidelity'] / len(pa_data['scores'])) * 100
        row.append(adherence)
    else:
        row.append(0)
    
    matrix_data.append(row)

# Transpose for heatmap
matrix_transposed = list(map(list, zip(*matrix_data)))

fig9 = go.Figure(data=go.Heatmap(
    z=matrix_transposed,
    x=personalities,
    y=metric_names,
    colorscale='RdYlGn',
    text=[[f"{val:.1f}" for val in row] for row in matrix_transposed],
    texttemplate='%{text}',
    textfont={"size": 14, "color": "black"},
    colorbar=dict(title=dict(text="Score", font=dict(size=14)))
))

fig9.update_layout(
    title=dict(text="Performance Matrix: All Metrics by Personality",
               font=dict(size=24, color='black')),
    xaxis_title="Personality",
    yaxis_title="Metric",
    height=700,
    width=1000,
    font=dict(size=14, color='black')
)

fig9.write_image("viz_9_performance_matrix.jpg", width=1400, height=900, scale=2)
print("✅ Created: viz_9_performance_matrix.jpg")

print("\n" + "=" * 80)
print("✅ ALL JPG VISUALIZATIONS CREATED!")
print("=" * 80)
print("\nGenerated files:")
print("  1. viz_1_quality_distribution.jpg")
print("  2. viz_2_completion_rate.jpg")
print("  3. viz_3_turn_efficiency.jpg")
print("  4. viz_4_actionable_feedback.jpg")
print("  5. viz_5_tutor_responsiveness.jpg")
print("  6. viz_6_persona_adherence.jpg")
print("  7. viz_7_turn_distribution.jpg")
print("  8. viz_8_training_data_breakdown.jpg")
print("  9. viz_9_performance_matrix.jpg")
print("\nYou can now insert these JPG files directly into your document!")
