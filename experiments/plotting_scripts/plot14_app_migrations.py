"""
Plot 14: Application Migrations & Restructuring Severity per Event.

Visualizes the number of application migrations triggered after each simulation
event, the systemic severity/magnitude of each restructuring (% of active apps
reconfigured), and the cumulative migration overhead over the scenario.

Key Features:
- Primary Y-axis (Left): Number of migrated applications per event (discrete stem/lollipop plot).
- Marker Size: Restructuring Severity (% of active system reconfigured, 0% to 100%).
- Marker Color: Event Category (Infra Failure/Hazard, Infra Recovery, User Mobility, App Config).
- Secondary Y-axis (Right): Cumulative migrations over time (total migration load & churn velocity).
- Status Shading: Visual indicators for Disconnected (purple hatch) and Infeasible (red hatch) periods.
- Peak Annotations: Callouts detailing top radical restructuring events (step, apps moved, % system, trigger).
- Executive KPI Box: Scenario totals, churn frequency, and maximum single-step shift.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plot_utils import (configure_matplotlib, ensure_output_dir, SCENARIO_LABELS,
                        EVENT_MIGRATION_CATEGORIES, load_migration_data)


def plot_app_migrations(sim_dir, scenario_key, output_dir, max_steps=None):
    """
    Generate the Application Migrations & Restructuring Severity plot for a scenario.
    Outputs both high-resolution PNG (300 DPI) and publication-quality PDF.
    """
    configure_matplotlib()
    ensure_output_dir(output_dir)
    label = SCENARIO_LABELS.get(scenario_key, scenario_key)
    
    data = load_migration_data(sim_dir, max_steps)
    steps = data['steps']
    cum = data['cum_migs']
    total_migs = int(cum[-1]) if len(cum) > 0 else 0
    
    fig, ax1 = plt.subplots(figsize=(14, 6.8))
    ax2 = ax1.twinx()
    
    # -------------------------------------------------------------------------
    # Secondary Axis (Right): Cumulative Migrations
    # -------------------------------------------------------------------------
    ax2.step(steps, cum, color='#455A64', linewidth=1.8, linestyle='--',
             label='Cumulative Migrations', where='post', alpha=0.85, zorder=2)
    ax2.fill_between(steps, 0, cum, step='post', color='#B0BEC5', alpha=0.15, zorder=1)
    ax2.set_ylabel('Cumulative Migrations', fontsize=12, color='#37474F', fontweight='bold')
    ax2.tick_params(axis='y', labelcolor='#37474F')
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax2.grid(False)
    
    # -------------------------------------------------------------------------
    # Primary Axis (Left): Migrations per Event
    # -------------------------------------------------------------------------
    mig_mask = data['mig_counts'] > 0
    mig_steps = steps[mig_mask]
    migs = data['mig_counts'][mig_mask]
    pcts = data['mig_pcts'][mig_mask]
    colors = [data['cat_colors'][i] for i in range(len(steps)) if mig_mask[i]]
    actions = [data['actions'][i] for i in range(len(steps)) if mig_mask[i]]
    
    # Draw vertical stems (lollipop style)
    for s, m, c in zip(mig_steps, migs, colors):
        ax1.plot([s, s], [0, m], color=c, alpha=0.45, linewidth=1.2, zorder=3)
        
    # Marker sizes scaled by restructuring percentage (% of active apps)
    # Range: 25 pt^2 (<=5% minor tweak) to 165 pt^2 (>85% mass migration)
    sizes = 25 + (pcts / 100.0) * 140
    
    # Group scatter points by category for clean legend
    scatter_handles = []
    for cat_key, cat_data in EVENT_MIGRATION_CATEGORIES.items():
        cat_mask = [c == cat_data['color'] for c in colors]
        if any(cat_mask):
            xs = mig_steps[cat_mask]
            ys = migs[cat_mask]
            szs = sizes[cat_mask]
            sc = ax1.scatter(xs, ys, s=szs, color=cat_data['color'], alpha=0.85,
                             edgecolors='white', linewidth=0.7, zorder=4,
                             label=cat_data['label'])
            scatter_handles.append(sc)
            
    # -------------------------------------------------------------------------
    # Status Shading (Infeasible & Disconnected)
    # -------------------------------------------------------------------------
    infeasible_mask = np.array([s == 'Infeasible' for s in data['solver_status']])
    disconnected_mask = np.array([s == 'Disconnected' for s in data['solver_status']])
    
    def shade_mask(ax, mask, color, hatch, lbl):
        if not np.any(mask):
            return None
        in_block = False
        start = None
        h = None
        for i, val in enumerate(mask):
            if val and not in_block:
                in_block = True
                start = steps[i]
            elif not val and in_block:
                in_block = False
                h = ax.axvspan(start, steps[i-1], color=color, alpha=0.35, hatch=hatch, zorder=1)
        if in_block:
            h = ax.axvspan(start, steps[-1], color=color, alpha=0.35, hatch=hatch, zorder=1)
        return Patch(facecolor=color, alpha=0.35, hatch=hatch, label=lbl) if h else None

    p_inf = shade_mask(ax1, infeasible_mask, '#FFCDD2', '///', 'Infeasible (Resource Limit)')
    p_disc = shade_mask(ax1, disconnected_mask, '#D1C4E9', '\\\\\\', 'Disconnected (No Paths)')

    # -------------------------------------------------------------------------
    # Peak Restructuring Annotations
    # -------------------------------------------------------------------------
    if len(migs) > 0 and max(migs) > 2:
        top_indices = np.argsort(migs)[::-1]
        annotated_steps = []
        for idx in top_indices:
            s = mig_steps[idx]
            # Avoid visually crowded/overlapping annotations
            if any(abs(s - prev_s) < 180 for prev_s in annotated_steps):
                continue
            annotated_steps.append(s)
            m = migs[idx]
            p = pcts[idx]
            act = actions[idx]
            
            # Position offset
            x_off = 160 if s < len(steps) * 0.75 else -720
            y_off = 2.5 if m < max(migs) * 0.8 else -4.0
            
            ax1.annotate(
                f"Step {s}: {m} apps ({p:.1f}%)\n[{act}]",
                xy=(s, m),
                xytext=(s + x_off, m + y_off),
                arrowprops=dict(facecolor='#263238', edgecolor='none', arrowstyle='->', lw=1.2),
                fontsize=8.5,
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#ECEFF1', edgecolor='#90A4AE', alpha=0.92),
                fontweight='bold',
                zorder=6
            )
            if len(annotated_steps) >= 3:
                break
    elif total_migs == 0:
        ax1.text(0.5, 0.5, 'No application migrations occurred\n(Optimal placement remained static throughout scenario)',
                 transform=ax1.transAxes, ha='center', va='center', fontsize=12, style='italic', color='#546E7A',
                 bbox=dict(boxstyle='round,pad=0.6', facecolor='#ECEFF1', edgecolor='#CFD8DC', alpha=0.85))

    ax1.set_xlabel('Simulation Step (Event)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Migrated Applications (count)', fontsize=12, color='#1A237E', fontweight='bold')
    ax1.tick_params(axis='y', labelcolor='#1A237E')
    ax1.yaxis.set_major_locator(MaxNLocator(integer=True))
    
    y_max1 = max(migs) * 1.35 if len(migs) > 0 and max(migs) > 0 else 5
    y_max2 = max(cum) * 1.25 if total_migs > 0 else 5
    ax1.set_ylim(0, y_max1)
    ax2.set_ylim(0, y_max2)
    ax1.set_xlim(0, len(steps))
    
    # -------------------------------------------------------------------------
    # Legends & Metadata
    # -------------------------------------------------------------------------
    size_handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#78909C',
               markersize=np.sqrt(25), label='≤ 5% system'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#78909C',
               markersize=np.sqrt(25 + 0.5 * 140), label='50% system'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#78909C',
               markersize=np.sqrt(25 + 0.9 * 140), label='90% system'),
    ]

    all_handles = scatter_handles + [Line2D([0], [0], color='#455A64', lw=1.8, ls='--',
                                           label='Cumulative Migrations')]
    if p_disc:
        all_handles.append(p_disc)
    if p_inf:
        all_handles.append(p_inf)

    leg1 = ax1.legend(handles=all_handles, loc='upper left', framealpha=0.92, edgecolor='#CFD8DC',
                      title='Trigger Category & Trends', title_fontsize=9)
    if total_migs > 0:
        leg2 = ax1.legend(handles=size_handles, loc='upper right', framealpha=0.92, edgecolor='#CFD8DC',
                          title='Restructuring Severity (% of Apps)', title_fontsize=9)
        ax1.add_artist(leg1)
    
    plt.title(f"{label} — Application Migrations & Restructuring Severity per Event",
              fontsize=13.5, fontweight='bold', pad=12)
    
    # Executive KPI summary card
    churn_steps = len(mig_steps)
    max_single = max(migs) if len(migs) > 0 else 0
    max_pct = max(pcts) if len(pcts) > 0 else 0.0

    stats_text = (
        f"Total Migrations: {total_migs}\n"
        f"Events with Churn: {churn_steps} ({churn_steps / len(steps) * 100:.1f}%)\n"
        f"Max Single Shift: {max_single} apps ({max_pct:.1f}%)"
    )
    ax1.text(0.48, 0.96, stats_text, transform=ax1.transAxes, verticalalignment='top', ha='center',
             fontsize=9, bbox=dict(boxstyle='round,pad=0.35', facecolor='#FFF8E1', edgecolor='#FFE082', alpha=0.92),
             fontfamily='monospace')

    # Save dual output formats (PDF & PNG)
    pdf_path = os.path.join(output_dir, f'plot14_app_migrations_{scenario_key}.pdf')
    png_path = os.path.join(output_dir, f'plot14_app_migrations_{scenario_key}.png')
    
    fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
    fig.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {pdf_path}")
    print(f"Saved: {png_path}")
    return pdf_path, png_path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Plot 14: Application Migrations per Event')
    parser.add_argument('--sim-dir', required=True, help='Directory containing Simulation*.json files')
    parser.add_argument('--scenario', required=True, help='Scenario key (e.g. electric_storm)')
    parser.add_argument('--output-dir', default='figures', help='Output directory for figures')
    parser.add_argument('--max-steps', type=int, default=None, help='Max steps to load')
    args = parser.parse_args()
    
    plot_app_migrations(args.sim_dir, args.scenario, args.output_dir, args.max_steps)
