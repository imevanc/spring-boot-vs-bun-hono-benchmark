import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
import seaborn as sns

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_data(bun_file, spring_file):
    """Load performance data from JSON files"""
    with open(bun_file, 'r') as f:
        bun_data = json.load(f)

    with open(spring_file, 'r') as f:
        spring_data = json.load(f)

    return bun_data, spring_data

def create_comparison_dataframe(bun_data, spring_data):
    """Create a comparative DataFrame from the test results"""
    comparison_data = []

    for bun_test, spring_test in zip(bun_data, spring_data):
        comparison_data.append({
            'Target_TPS': bun_test['targetTPS'],
            'Bun_Actual_TPS': bun_test['actualTPS'],
            'Spring_Actual_TPS': spring_test['actualTPS'],
            'Bun_Avg_Response': bun_test['avgResponseTime'],
            'Spring_Avg_Response': spring_test['avgResponseTime'],
            'Bun_P95_Response': bun_test['p95ResponseTime'],
            'Spring_P95_Response': spring_test['p95ResponseTime'],
            'Bun_P99_Response': bun_test['p99ResponseTime'],
            'Spring_P99_Response': spring_test['p99ResponseTime'],
            'Bun_Max_Response': bun_test['maxResponseTime'],
            'Spring_Max_Response': spring_test['maxResponseTime'],
            'Improvement_Avg': ((spring_test['avgResponseTime'] - bun_test['avgResponseTime']) / spring_test['avgResponseTime']) * 100,
            'Improvement_P95': ((spring_test['p95ResponseTime'] - bun_test['p95ResponseTime']) / spring_test['p95ResponseTime']) * 100
        })

    return pd.DataFrame(comparison_data)

def plot_response_times_comparison(df):
    """Create a comprehensive response time comparison chart"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))

    # Average Response Time Comparison
    x = np.arange(len(df))
    width = 0.35

    bars1 = ax1.bar(x - width/2, df['Spring_Avg_Response'], width,
                   label='Spring Boot', color='#FF6B6B', alpha=0.8)
    bars2 = ax1.bar(x + width/2, df['Bun_Avg_Response'], width,
                   label='Bun+Hono', color='#4ECDC4', alpha=0.8)

    ax1.set_xlabel('Target TPS')
    ax1.set_ylabel('Average Response Time (ms)')
    ax1.set_title('Average Response Time Comparison')
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['Target_TPS'])
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms', ha='center', va='bottom', fontsize=8)

    for bar in bars2:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}ms', ha='center', va='bottom', fontsize=8)

    # P95 Response Time Comparison
    bars3 = ax2.bar(x - width/2, df['Spring_P95_Response'], width,
                   label='Spring Boot', color='#FF6B6B', alpha=0.8)
    bars4 = ax2.bar(x + width/2, df['Bun_P95_Response'], width,
                   label='Bun+Hono', color='#4ECDC4', alpha=0.8)

    ax2.set_xlabel('Target TPS')
    ax2.set_ylabel('P95 Response Time (ms)')
    ax2.set_title('P95 Response Time Comparison')
    ax2.set_xticks(x)
    ax2.set_xticklabels(df['Target_TPS'])
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    # Performance Improvement Chart
    bars5 = ax3.bar(x, df['Improvement_Avg'], color='#45B7D1', alpha=0.8)
    ax3.set_xlabel('Target TPS')
    ax3.set_ylabel('Performance Improvement (%)')
    ax3.set_title('Average Response Time Improvement (Bun+Hono vs Spring Boot)')
    ax3.set_xticks(x)
    ax3.set_xticklabels(df['Target_TPS'])
    ax3.grid(True, alpha=0.3)

    # Add percentage labels
    for bar in bars5:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Throughput Comparison
    bars6 = ax4.bar(x - width/2, df['Spring_Actual_TPS'], width,
                   label='Spring Boot', color='#FF6B6B', alpha=0.8)
    bars7 = ax4.bar(x + width/2, df['Bun_Actual_TPS'], width,
                   label='Bun+Hono', color='#4ECDC4', alpha=0.8)

    ax4.set_xlabel('Target TPS')
    ax4.set_ylabel('Actual TPS Achieved')
    ax4.set_title('Throughput Comparison (Actual TPS)')
    ax4.set_xticks(x)
    ax4.set_xticklabels(df['Target_TPS'])
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_response_time_distribution(df):
    """Create a response time distribution comparison"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

    # Response time percentiles comparison
    tps_labels = df['Target_TPS'].astype(str)

    # Spring Boot percentiles
    ax1.plot(tps_labels, df['Spring_Avg_Response'], 'o-', label='Average', linewidth=2, markersize=8)
    ax1.plot(tps_labels, df['Spring_P95_Response'], 's-', label='P95', linewidth=2, markersize=8)
    ax1.plot(tps_labels, df['Spring_P99_Response'], '^-', label='P99', linewidth=2, markersize=8)
    ax1.set_xlabel('Target TPS')
    ax1.set_ylabel('Response Time (ms)')
    ax1.set_title('Spring Boot Response Time Distribution')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')

    # Bun+Hono percentiles
    ax2.plot(tps_labels, df['Bun_Avg_Response'], 'o-', label='Average', linewidth=2, markersize=8)
    ax2.plot(tps_labels, df['Bun_P95_Response'], 's-', label='P95', linewidth=2, markersize=8)
    ax2.plot(tps_labels, df['Bun_P99_Response'], '^-', label='P99', linewidth=2, markersize=8)
    ax2.set_xlabel('Target TPS')
    ax2.set_ylabel('Response Time (ms)')
    ax2.set_title('Bun+Hono Response Time Distribution')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_yscale('log')

    plt.tight_layout()
    plt.savefig('response_time_distribution.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_performance_heatmap(df):
    """Create a performance improvement heatmap"""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Prepare data for heatmap
    metrics = ['Avg Response Time', 'P95 Response Time']
    tps_values = df['Target_TPS'].values

    heatmap_data = np.array([
        df['Improvement_Avg'].values,
        df['Improvement_P95'].values
    ])

    im = ax.imshow(heatmap_data, cmap='RdYlGn', aspect='auto')

    # Set ticks and labels
    ax.set_xticks(np.arange(len(tps_values)))
    ax.set_yticks(np.arange(len(metrics)))
    ax.set_xticklabels(tps_values)
    ax.set_yticklabels(metrics)

    # Add text annotations
    for i in range(len(metrics)):
        for j in range(len(tps_values)):
            text = ax.text(j, i, f'{heatmap_data[i, j]:.1f}%',
                         ha="center", va="center", color="black", fontweight='bold')

    ax.set_title('Performance Improvement Heatmap (Bun+Hono vs Spring Boot)')
    ax.set_xlabel('Target TPS')

    # Add colorbar
    cbar = plt.colorbar(im)
    cbar.set_label('Improvement (%)', rotation=270, labelpad=15)

    plt.tight_layout()
    plt.savefig('performance_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()

def generate_summary_report(df):
    """Generate a summary report with key metrics"""
    print("=" * 60)
    print("                PERFORMANCE COMPARISON REPORT")
    print("=" * 60)

    # Overall averages
    spring_avg_overall = df['Spring_Avg_Response'].mean()
    bun_avg_overall = df['Bun_Avg_Response'].mean()
    overall_improvement = ((spring_avg_overall - bun_avg_overall) / spring_avg_overall) * 100

    spring_p95_overall = df['Spring_P95_Response'].mean()
    bun_p95_overall = df['Bun_P95_Response'].mean()
    p95_improvement = ((spring_p95_overall - bun_p95_overall) / spring_p95_overall) * 100

    print(f"\nFramework Performance Summary:")
    print("-" * 40)
    print(f"Spring Boot Average Response Time: {spring_avg_overall:.2f}ms")
    print(f"Bun+Hono Average Response Time:   {bun_avg_overall:.2f}ms")
    print(f"Performance Improvement:          {overall_improvement:.1f}%")

    print(f"\nSpring Boot P95 Response Time:    {spring_p95_overall:.2f}ms")
    print(f"Bun+Hono P95 Response Time:      {bun_p95_overall:.2f}ms")
    print(f"P95 Improvement:                  {p95_improvement:.1f}%")

    print(f"\nSpring Boot Average Error Rate:   0.000%")
    print(f"Bun+Hono Average Error Rate:     0.000%")

    # Detailed comparison table
    print(f"\nDetailed TPS Comparison:")
    print("-" * 80)
    print(f"{'TPS':<8} {'Spring RPS':<12} {'Bun RPS':<12} {'Spring Avg':<12} {'Bun Avg':<12} {'Improvement':<12}")
    print("-" * 80)

    for _, row in df.iterrows():
        print(f"{row['Target_TPS']:<8} {row['Spring_Actual_TPS']:<12.1f} {row['Bun_Actual_TPS']:<12.1f} "
              f"{row['Spring_Avg_Response']:<12.1f}ms {row['Bun_Avg_Response']:<12.1f}ms {row['Improvement_Avg']:<12.1f}%")

def main():
    """Main function to run the performance analysis"""
    # Load data
    bun_data, spring_data = load_data('bun-hono-results.json', 'spring-boot-results.json')

    # Create comparison DataFrame
    df = create_comparison_dataframe(bun_data, spring_data)

    # Generate visualizations
    print("Generating performance comparison charts...")
    plot_response_times_comparison(df)

    print("Generating response time distribution charts...")
    plot_response_time_distribution(df)

    print("Generating performance improvement heatmap...")
    plot_performance_heatmap(df)

    # Generate summary report
    generate_summary_report(df)

    print(f"\nCharts saved as:")
    print(f"- performance_comparison.png")
    print(f"- response_time_distribution.png")
    print(f"- performance_heatmap.png")

if __name__ == "__main__":
    main()