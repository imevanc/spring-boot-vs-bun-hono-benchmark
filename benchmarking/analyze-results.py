#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np
from pathlib import Path

def load_and_analyze_results(csv_file='benchmark_results.csv'):
    """Load and analyze benchmark results"""
    
    if not Path(csv_file).exists():
        print(f"Results file {csv_file} not found!")
        return
    
    # Load data
    df = pd.read_csv(csv_file)
    
    print("=== API Benchmark Analysis ===\n")
    
    # Basic statistics
    print("1. Overview:")
    print(f"   Total tests run: {len(df)}")
    print(f"   Frameworks tested: {', '.join(df['Framework'].unique())}")
    print(f"   Endpoints tested: {', '.join(df['Endpoint'].unique())}")
    print(f"   TPS levels: {sorted(df['Target_TPS'].unique())}")
    
    # Performance comparison by TPS
    print("\n2. Performance by TPS Level:")
    print("-" * 80)
    
    pivot_rps = df.pivot_table(
        values='Actual_RPS',
        index='Target_TPS',
        columns='Framework',
        aggfunc='mean'
    )
    
    pivot_avg_time = df.pivot_table(
        values='Avg_Time_ms',
        index='Target_TPS',
        columns='Framework',
        aggfunc='mean'
    )
    
    pivot_p95_time = df.pivot_table(
        values='P95_Time_ms',
        index='Target_TPS',
        columns='Framework',
        aggfunc='mean'
    )
    
    for tps in sorted(df['Target_TPS'].unique()):
        print(f"\nTPS Level: {tps}")
        
        spring_rps = pivot_rps.loc[tps, 'SpringBoot'] if 'SpringBoot' in pivot_rps.columns else 0
        bun_rps = pivot_rps.loc[tps, 'BunHono'] if 'BunHono' in pivot_rps.columns else 0
        
        spring_avg = pivot_avg_time.loc[tps, 'SpringBoot'] if 'SpringBoot' in pivot_avg_time.columns else 0
        bun_avg = pivot_avg_time.loc[tps, 'BunHono'] if 'BunHono' in pivot_avg_time.columns else 0
        
        spring_p95 = pivot_p95_time.loc[tps, 'SpringBoot'] if 'SpringBoot' in pivot_p95_time.columns else 0
        bun_p95 = pivot_p95_time.loc[tps, 'BunHono'] if 'BunHono' in pivot_p95_time.columns else 0
        
        print(f"  Actual RPS    - Spring Boot: {spring_rps:.1f}, Bun+Hono: {bun_rps:.1f}")
        print(f"  Avg Time (ms) - Spring Boot: {spring_avg:.1f}, Bun+Hono: {bun_avg:.1f}")
        print(f"  P95 Time (ms) - Spring Boot: {spring_p95:.1f}, Bun+Hono: {bun_p95:.1f}")
        
        if spring_avg > 0 and bun_avg > 0:
            improvement = ((spring_avg - bun_avg) / spring_avg) * 100
            print(f"  Performance   - Bun+Hono is {improvement:.1f}% faster")
    
    # Endpoint-specific analysis
    print("\n3. Performance by Endpoint:")
    print("-" * 50)
    
    for endpoint in df['Endpoint'].unique():
        endpoint_data = df[df['Endpoint'] == endpoint]
        print(f"\nEndpoint: /{endpoint}")
        
        spring_data = endpoint_data[endpoint_data['Framework'] == 'SpringBoot']
        bun_data = endpoint_data[endpoint_data['Framework'] == 'BunHono']
        
        if not spring_data.empty and not bun_data.empty:
            spring_avg_rps = spring_data['Actual_RPS'].mean()
            bun_avg_rps = bun_data['Actual_RPS'].mean()
            
            spring_avg_time = spring_data['Avg_Time_ms'].mean()
            bun_avg_time = bun_data['Avg_Time_ms'].mean()
            
            print(f"  Average RPS    - Spring Boot: {spring_avg_rps:.1f}, Bun+Hono: {bun_avg_rps:.1f}")
            print(f"  Average Time   - Spring Boot: {spring_avg_time:.1f}ms, Bun+Hono: {bun_avg_time:.1f}ms")
    
    # Error analysis
    print("\n4. Error Analysis:")
    print("-" * 30)
    
    total_errors = df.groupby('Framework')['Failed_Requests'].sum()
    total_requests = df.groupby('Framework').apply(
        lambda x: (x['Target_TPS'] * 60).sum()  # 60 seconds per test
    )
    
    for framework in df['Framework'].unique():
        if framework in total_errors.index:
            error_rate = (total_errors[framework] / total_requests[framework]) * 100
            print(f"  {framework}: {total_errors[framework]} errors ({error_rate:.3f}% error rate)")
    
    # Generate visualizations
    create_visualizations(df)

def create_visualizations(df):
    """Create performance visualization charts"""
    
    plt.style.use('seaborn-v0_8')
    
    # 2x2 grid for the first 4 charts
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('API Performance Benchmark: Spring Boot vs Bun+Hono', fontsize=16)
    
    # 1. Response Time by TPS
    pivot_time = df.pivot_table(
        values='Avg_Time_ms',
        index='Target_TPS',
        columns='Framework'
    )
    pivot_time.plot(kind='line', ax=axes[0,0], marker='o')
    axes[0,0].set_title('Average Response Time by TPS')
    axes[0,0].set_xlabel('Target TPS')
    axes[0,0].set_ylabel('Response Time (ms)')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Throughput by TPS
    pivot_rps = df.pivot_table(
        values='Actual_RPS',
        index='Target_TPS',
        columns='Framework'
    )
    pivot_rps.plot(kind='line', ax=axes[0,1], marker='s')
    axes[0,1].set_title('Actual Throughput by TPS')
    axes[0,1].set_xlabel('Target TPS')
    axes[0,1].set_ylabel('Actual RPS')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # 3. P95 Response Time
    pivot_p95 = df.pivot_table(
        values='P95_Time_ms',
        index='Target_TPS',
        columns='Framework'
    )
    pivot_p95.plot(kind='line', ax=axes[1,0], marker='^')
    axes[1,0].set_title('P95 Response Time by TPS')
    axes[1,0].set_xlabel('Target TPS')
    axes[1,0].set_ylabel('P95 Response Time (ms)')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. Error Rate by TPS
    df['Error_Rate'] = (df['Failed_Requests'] / (df['Target_TPS'] * 60)) * 100
    pivot_errors = df.pivot_table(
        values='Error_Rate',
        index='Target_TPS',
        columns='Framework'
    )
    pivot_errors.plot(kind='bar', ax=axes[1,1])
    axes[1,1].set_title('Error Rate by TPS')
    axes[1,1].set_xlabel('Target TPS')
    axes[1,1].set_ylabel('Error Rate (%)')
    axes[1,1].legend()
    axes[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig('benchmark_results.png', dpi=300, bbox_inches='tight')
    print(f"\n5. Visualization saved as 'benchmark_results.png'")
    
    # 5. Performance Improvement (%) - Bun+Hono vs Spring Boot (separate figure)
    pivot_avg_time = df.pivot_table(
        values='Avg_Time_ms',
        index='Target_TPS',
        columns='Framework'
    )
    improvement = ((pivot_avg_time['SpringBoot'] - pivot_avg_time['BunHono']) / pivot_avg_time['SpringBoot']) * 100
    
    plt.figure(figsize=(10,6))
    ax = plt.gca()
    improvement.plot(kind='line', marker='d', ax=ax)
    
    ax.axhline(0, color='black', lw=1, linestyle='--')
    ax.set_title('Performance Improvement (%) - Bun+Hono vs Spring Boot')
    ax.set_xlabel('Target TPS')
    ax.set_ylabel('Improvement (%)')
    ax.grid(True, alpha=0.3)
    
    # Color points green if improvement >0 else red and add data labels
    colors = ['green' if val > 0 else 'red' for val in improvement]
    for x, y, c in zip(improvement.index, improvement.values, colors):
        ax.scatter(x, y, color=c, s=100)
        ax.text(x, y + 1, f"{y:.1f}%", ha='center', color=c, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('performance_improvement.png', dpi=300, bbox_inches='tight')
    print(f"6. Performance improvement graph saved as 'performance_improvement.png'")
    
    # Show summary table
    print("\n7. Summary Table:")
    print("=" * 100)
    
    summary = df.groupby(['Framework', 'Target_TPS']).agg({
        'Actual_RPS': 'mean',
        'Avg_Time_ms': 'mean',
        'P95_Time_ms': 'mean',
        'Failed_Requests': 'sum'
    }).round(2)
    
    print(summary.to_string())

if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'benchmark_results.csv'
    
    try:
        load_and_analyze_results(csv_file)
    except ImportError as e:
        if 'matplotlib' in str(e) or 'seaborn' in str(e):
            print("Visualization libraries not available. Install with:")
            print("pip install matplotlib seaborn")
            print("\nRunning analysis without charts...")
            
            # Simplified analysis without charts
            import pandas as pd
            df = pd.read_csv(csv_file)
            
            print("=== Basic Analysis ===")
            print("\nAverage Performance by Framework:")
            summary = df.groupby('Framework').agg({
                'Actual_RPS': 'mean',
                'Avg_Time_ms': 'mean',
                'P95_Time_ms': 'mean'
            }).round(2)
            print(summary)
        else:
            raise
