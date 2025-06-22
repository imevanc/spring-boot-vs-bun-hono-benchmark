# API Benchmarking Suite: Spring Boot vs Bun+Hono

## Complete Applications:
- Fully functional Spring Boot API with multiple endpoints.
- Bun+Hono TypeScript API with equivalent functionality.
- Both include health checks, user endpoints, echo services, compute tasks and stats.


## Multiple Benchmarking Tools:
- Apache Bench script: Automated testing across all TPS levels.
- Artillery.io config: Professional load testing with weighted scenarios.
- Custom Node.js load tester: Advanced metrics and real-time monitoring.


## Comprehensive Analysis:
- Python script for detailed performance analysis.
- Automated chart generation.
- Statistical comparisons and performance insights.


## All TPS Levels Covered: 5, 10, 15, 30, 40, 100, and 1000 TPS with:
- Response time measurements (avg, P50, P95, P99)
- Throughput analysis
- Error rate tracking
- Resource usage monitoring


## Quick Start:
- Build Spring Boot: mvn clean package && java -jar target/app.jar
- Start Bun+Hono: bun install && bun run server.ts
- Run Benchmark: ./benchmark.sh
- Analyze Results: python3 analyze-results.py

The suite will automatically test both frameworks across all specified TPS levels and generate detailed performance comparisons, charts and recommendations. Each tool provides different insights - use Apache Bench for quick comparisons, Artillery for realistic load patterns and the custom Node.js tester for detailed metrics.
