#!/usr/bin/env node

const http = require('http');
const https = require('https');
const fs = require('fs');
const { performance } = require('perf_hooks');

class LoadTester {
    constructor(config) {
        this.config = {
            baseUrl: 'http://localhost:8080',
            duration: 60,
            warmupDuration: 180, // 3 minutes
            warmupTPS: 1000,
            ...config
        };

        this.results = [];
        this.isRunning = false;
        this.requestCount = 0;
        this.errorCount = 0;
        this.responseTimes = [];
    }

    async makeRequest(endpoint, method = 'GET', data = null) {
        return new Promise((resolve, reject) => {
            const url = new URL(endpoint, this.config.baseUrl);
            const options = {
                hostname: url.hostname,
                port: url.port || (url.protocol === 'https:' ? 443 : 80),
                path: url.pathname,
                method: method,
                headers: {
                    'User-Agent': 'LoadTester/1.0',
                    'Connection': 'keep-alive'
                }
            };

            if (data && method === 'POST') {
                const jsonData = JSON.stringify(data);
                options.headers['Content-Type'] = 'application/json';
                options.headers['Content-Length'] = Buffer.byteLength(jsonData);
            }

            const startTime = performance.now();
            const client = url.protocol === 'https:' ? https : http;

            const req = client.request(options, (res) => {
                let body = '';

                res.on('data', (chunk) => {
                    body += chunk;
                });

                res.on('end', () => {
                    const endTime = performance.now();
                    const responseTime = endTime - startTime;

                    resolve({
                        statusCode: res.statusCode,
                        responseTime: responseTime,
                        body: body,
                        success: res.statusCode >= 200 && res.statusCode < 300
                    });
                });
            });

            req.on('error', (err) => {
                const endTime = performance.now();
                const responseTime = endTime - startTime;

                reject({
                    error: err.message,
                    responseTime: responseTime,
                    success: false
                });
            });

            req.on('timeout', () => {
                req.destroy();
                reject({
                    error: 'Request timeout',
                    responseTime: this.config.timeout || 30000,
                    success: false
                });
            });

            if (data && method === 'POST') {
                req.write(JSON.stringify(data));
            }

            req.end();
        });
    }

    async runWarmup() {
        console.log(`Starting intensive warmup (${this.config.warmupDuration}s at ${this.config.warmupTPS} TPS)...`);

        const totalWarmupRequests = this.config.warmupTPS * this.config.warmupDuration;
        const interval = 1000 / this.config.warmupTPS; // ms between requests

        const startTime = Date.now();
        const endTime = startTime + (this.config.warmupDuration * 1000);

        // Define warmup scenarios (simpler mix for warmup)
        const warmupScenarios = [
            { endpoint: '/health', method: 'GET', weight: 40 },
            { endpoint: '/users/123', method: 'GET', weight: 30 },
            { endpoint: '/echo', method: 'POST', weight: 20, data: { warmup: true, id: Math.random() } },
            { endpoint: '/stats', method: 'GET', weight: 10 }
        ];

        // Create weighted scenario array for warmup
        const weightedScenarios = [];
        warmupScenarios.forEach(scenario => {
            for (let i = 0; i < scenario.weight; i++) {
                weightedScenarios.push(scenario);
            }
        });

        let warmupRequestCount = 0;
        let warmupErrorCount = 0;
        const requestPromises = [];
        let nextRequestTime = startTime;

        console.log(`Target warmup requests: ${totalWarmupRequests}`);

        while (Date.now() < endTime) {
            const currentTime = Date.now();

            if (currentTime >= nextRequestTime) {
                // Select random scenario
                const scenario = weightedScenarios[Math.floor(Math.random() * weightedScenarios.length)];

                // Make request
                const requestPromise = this.makeRequest(scenario.endpoint, scenario.method, scenario.data)
                    .then(result => {
                        warmupRequestCount++;
                        if (!result.success) {
                            warmupErrorCount++;
                        }
                        return result;
                    })
                    .catch(error => {
                        warmupRequestCount++;
                        warmupErrorCount++;
                        return error;
                    });

                requestPromises.push(requestPromise);
                nextRequestTime += interval;

                // Progress reporting every 30 seconds
                if (warmupRequestCount % (this.config.warmupTPS * 30) === 0) {
                    const elapsed = Math.floor((Date.now() - startTime) / 1000);
                    const actualTPS = warmupRequestCount / elapsed;
                    console.log(`Warmup progress: ${elapsed}s elapsed, ${warmupRequestCount} requests sent, ${actualTPS.toFixed(1)} TPS`);
                }
            }

            // Small delay to prevent busy waiting
            await new Promise(resolve => setTimeout(resolve, 1));
        }

        // Wait for remaining requests to complete
        console.log('Waiting for warmup requests to complete...');
        await Promise.all(requestPromises);

        const actualWarmupTPS = warmupRequestCount / this.config.warmupDuration;
        const warmupErrorRate = (warmupErrorCount / warmupRequestCount) * 100;

        console.log(`Warmup completed:`);
        console.log(`  Total requests: ${warmupRequestCount}`);
        console.log(`  Actual TPS: ${actualWarmupTPS.toFixed(2)}`);
        console.log(`  Error rate: ${warmupErrorRate.toFixed(2)}%`);
        console.log('');
    }

    async runTest(tps, testName = '') {
        console.log(`\nStarting test: ${testName} (${tps} TPS for ${this.config.duration}s)`);

        this.requestCount = 0;
        this.errorCount = 0;
        this.responseTimes = [];
        this.isRunning = true;

        const totalRequests = tps * this.config.duration;
        const interval = 1000 / tps; // ms between requests

        const startTime = Date.now();
        const endTime = startTime + (this.config.duration * 1000);

        // Define test scenarios
        const scenarios = [
            { endpoint: '/health', method: 'GET', weight: 30 },
            { endpoint: '/users/123', method: 'GET', weight: 25 },
            { endpoint: '/echo', method: 'POST', weight: 25, data: { test: 'load-test', id: Math.random() } },
            { endpoint: '/compute', method: 'GET', weight: 15 },
            { endpoint: '/stats', method: 'GET', weight: 5 }
        ];

        // Create weighted scenario array
        const weightedScenarios = [];
        scenarios.forEach(scenario => {
            for (let i = 0; i < scenario.weight; i++) {
                weightedScenarios.push(scenario);
            }
        });

        const requestPromises = [];
        let nextRequestTime = startTime;

        while (Date.now() < endTime && this.isRunning) {
            const currentTime = Date.now();

            if (currentTime >= nextRequestTime) {
                // Select random scenario
                const scenario = weightedScenarios[Math.floor(Math.random() * weightedScenarios.length)];

                // Make request
                const requestPromise = this.makeRequest(scenario.endpoint, scenario.method, scenario.data)
                    .then(result => {
                        this.requestCount++;
                        this.responseTimes.push(result.responseTime);
                        if (!result.success) {
                            this.errorCount++;
                        }
                        return result;
                    })
                    .catch(error => {
                        this.requestCount++;
                        this.errorCount++;
                        this.responseTimes.push(error.responseTime || 0);
                        return error;
                    });

                requestPromises.push(requestPromise);
                nextRequestTime += interval;
            }

            // Small delay to prevent busy waiting
            await new Promise(resolve => setTimeout(resolve, 1));
        }

        // Wait for all requests to complete
        console.log('Waiting for all requests to complete...');
        await Promise.all(requestPromises);

        // Calculate statistics
        this.responseTimes.sort((a, b) => a - b);
        const stats = this.calculateStats();

        const result = {
            testName,
            targetTPS: tps,
            actualTPS: this.requestCount / this.config.duration,
            totalRequests: this.requestCount,
            errorCount: this.errorCount,
            errorRate: (this.errorCount / this.requestCount) * 100,
            ...stats
        };

        this.results.push(result);
        this.printResults(result);

        return result;
    }

    calculateStats() {
        if (this.responseTimes.length === 0) {
            return {
                avgResponseTime: 0,
                minResponseTime: 0,
                maxResponseTime: 0,
                p50ResponseTime: 0,
                p95ResponseTime: 0,
                p99ResponseTime: 0
            };
        }

        const sum = this.responseTimes.reduce((a, b) => a + b, 0);
        const avg = sum / this.responseTimes.length;

        return {
            avgResponseTime: avg,
            minResponseTime: this.responseTimes[0],
            maxResponseTime: this.responseTimes[this.responseTimes.length - 1],
            p50ResponseTime: this.percentile(50),
            p95ResponseTime: this.percentile(95),
            p99ResponseTime: this.percentile(99)
        };
    }

    percentile(p) {
        const index = Math.ceil((p / 100) * this.responseTimes.length) - 1;
        return this.responseTimes[Math.max(0, Math.min(index, this.responseTimes.length - 1))];
    }

    printResults(result) {
        console.log('\n--- Test Results ---');
        console.log(`Target TPS: ${result.targetTPS}`);
        console.log(`Actual TPS: ${result.actualTPS.toFixed(2)}`);
        console.log(`Total Requests: ${result.totalRequests}`);
        console.log(`Error Rate: ${result.errorRate.toFixed(2)}%`);
        console.log(`Avg Response Time: ${result.avgResponseTime.toFixed(2)}ms`);
        console.log(`P50 Response Time: ${result.p50ResponseTime.toFixed(2)}ms`);
        console.log(`P95 Response Time: ${result.p95ResponseTime.toFixed(2)}ms`);
        console.log(`P99 Response Time: ${result.p99ResponseTime.toFixed(2)}ms`);
        console.log('-------------------');
    }

    async runFullBenchmark(baseUrl) {
        this.config.baseUrl = baseUrl;
        const tpsLevels = [5, 10, 15, 30, 40, 100, 1000];

        console.log(`\n=== Starting Full Benchmark for ${baseUrl} ===`);

        // Intensive warmup at 1000 TPS for 3 minutes
        await this.runWarmup();

        // Run tests for each TPS level
        for (const tps of tpsLevels) {
            await this.runTest(tps, `${tps}TPS`);

            // Cool down between tests (except after the last test)
            if (tps !== 1000) {
                console.log('Cooling down for 10 seconds...');
                await new Promise(resolve => setTimeout(resolve, 10000));
            }
        }

        return this.results;
    }

    exportResults(filename = 'load-test-results.json') {
        fs.writeFileSync(filename, JSON.stringify(this.results, null, 2));
        console.log(`\nResults exported to ${filename}`);
    }

    stop() {
        this.isRunning = false;
        console.log('\nStopping load test...');
    }
}

// CLI interface
async function main() {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.log('Usage: node load-test.js <spring-boot-url> [bun-hono-url]');
        console.log('Example: node load-test.js http://localhost:8080 http://localhost:3000');
        process.exit(1);
    }

    const springBootUrl = args[0];
    const bunHonoUrl = args[1] || 'http://localhost:3000';

    console.log('=== API Load Testing Suite ===');
    console.log(`Spring Boot URL: ${springBootUrl}`);
    console.log(`Bun+Hono URL: ${bunHonoUrl}`);
    console.log(`Warmup: ${180}s at ${1000} TPS`);
    console.log(`Test sequence: [5, 10, 15, 30, 40, 100, 1000] TPS`);

    // Test Spring Boot
    const springTester = new LoadTester({
        duration: 60,
        warmupDuration: 180,
        warmupTPS: 1000
    });
    const springResults = await springTester.runFullBenchmark(springBootUrl);
    springTester.exportResults('spring-boot-results.json');

    console.log('\n' + '='.repeat(50));

    // Test Bun+Hono
    const bunTester = new LoadTester({
        duration: 60,
        warmupDuration: 180,
        warmupTPS: 1000
    });
    const bunResults = await bunTester.runFullBenchmark(bunHonoUrl);
    bunTester.exportResults('bun-hono-results.json');

    // Generate comparison report
    generateComparisonReport(springResults, bunResults);
}

function generateComparisonReport(springResults, bunResults) {
    console.log('\n' + '='.repeat(60));
    console.log('               PERFORMANCE COMPARISON REPORT');
    console.log('='.repeat(60));

    console.log('\nFramework Performance Summary:');
    console.log('-'.repeat(40));

    const springAvg = springResults.reduce((sum, r) => sum + r.avgResponseTime, 0) / springResults.length;
    const bunAvg = bunResults.reduce((sum, r) => sum + r.avgResponseTime, 0) / bunResults.length;

    const springP95 = springResults.reduce((sum, r) => sum + r.p95ResponseTime, 0) / springResults.length;
    const bunP95 = bunResults.reduce((sum, r) => sum + r.p95ResponseTime, 0) / bunResults.length;

    const springErrors = springResults.reduce((sum, r) => sum + r.errorRate, 0) / springResults.length;
    const bunErrors = bunResults.reduce((sum, r) => sum + r.errorRate, 0) / bunResults.length;

    console.log(`Spring Boot Average Response Time: ${springAvg.toFixed(2)}ms`);
    console.log(`Bun+Hono Average Response Time:   ${bunAvg.toFixed(2)}ms`);
    console.log(`Performance Improvement:          ${((springAvg - bunAvg) / springAvg * 100).toFixed(1)}%`);

    console.log(`\nSpring Boot P95 Response Time:    ${springP95.toFixed(2)}ms`);
    console.log(`Bun+Hono P95 Response Time:      ${bunP95.toFixed(2)}ms`);
    console.log(`P95 Improvement:                  ${((springP95 - bunP95) / springP95 * 100).toFixed(1)}%`);

    console.log(`\nSpring Boot Average Error Rate:   ${springErrors.toFixed(3)}%`);
    console.log(`Bun+Hono Average Error Rate:     ${bunErrors.toFixed(3)}%`);

    console.log('\nDetailed TPS Comparison:');
    console.log('-'.repeat(80));
    console.log('TPS\tSpring RPS\tBun RPS\t\tSpring Avg\tBun Avg\t\tImprovement');
    console.log('-'.repeat(80));

    for (let i = 0; i < springResults.length && i < bunResults.length; i++) {
        const spring = springResults[i];
        const bun = bunResults[i];
        const improvement = ((spring.avgResponseTime - bun.avgResponseTime) / spring.avgResponseTime * 100).toFixed(1);

        console.log(`${spring.targetTPS}\t${spring.actualTPS.toFixed(1)}\t\t${bun.actualTPS.toFixed(1)}\t\t${spring.avgResponseTime.toFixed(1)}ms\t\t${bun.avgResponseTime.toFixed(1)}ms\t\t${improvement}%`);
    }

    console.log('\n' + '='.repeat(60));
}

// Handle shutdown
process.on('SIGINT', () => {
    console.log('\nReceived SIGINT, shutting down gracefully...');
    process.exit(0);
});

if (require.main === module) {
    main().catch(console.error);
}

module.exports = LoadTester;