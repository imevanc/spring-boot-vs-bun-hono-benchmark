package com.benchmark;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;
import org.springframework.http.HttpStatus;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.ThreadLocalRandom;

@SpringBootApplication
@RestController
public class BenchmarkApplication {

    private final AtomicLong requestCounter = new AtomicLong(0);
    private final long startTime = System.currentTimeMillis();

    public static void main(String[] args) {
        System.setProperty("server.tomcat.max-threads", "200");
        System.setProperty("server.tomcat.min-spare-threads", "20");
        SpringApplication.run(BenchmarkApplication.class, args);
    }

    @GetMapping("/")
    public ResponseEntity<Map<String, Object>> root() {
        Map<String, Object> response = new HashMap<>();
        response.put("service", "spring-boot-benchmark");
        response.put("version", "1.0.0");
        response.put("timestamp", Instant.now().toEpochMilli());
        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        long requestId = requestCounter.incrementAndGet();
        Map<String, Object> response = new HashMap<>();
        response.put("status", "healthy");
        response.put("requestId", requestId);
        response.put("timestamp", Instant.now().toEpochMilli());
        response.put("uptime", System.currentTimeMillis() - startTime);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/echo")
    public ResponseEntity<Map<String, Object>> echo(@RequestBody Map<String, Object> payload) {
        long requestId = requestCounter.incrementAndGet();
        Map<String, Object> response = new HashMap<>();
        response.put("requestId", requestId);
        response.put("received", payload);
        response.put("timestamp", Instant.now().toEpochMilli());
        response.put("processingTime", ThreadLocalRandom.current().nextInt(1, 5));
        return ResponseEntity.ok(response);
    }

    @GetMapping("/users/{id}")
    public ResponseEntity<Map<String, Object>> getUser(@PathVariable String id) {
        // Simulate database lookup delay
        try {
            Thread.sleep(ThreadLocalRandom.current().nextInt(1, 3));
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }

        long requestId = requestCounter.incrementAndGet();
        Map<String, Object> user = new HashMap<>();
        user.put("id", id);
        user.put("name", "User " + id);
        user.put("email", "user" + id + "@benchmark.com");
        user.put("role", id.hashCode() % 2 == 0 ? "admin" : "user");
        user.put("createdAt", Instant.now().minusSeconds(ThreadLocalRandom.current().nextInt(86400)).toEpochMilli());

        Map<String, Object> response = new HashMap<>();
        response.put("requestId", requestId);
        response.put("user", user);
        response.put("timestamp", Instant.now().toEpochMilli());

        return ResponseEntity.ok(response);
    }

    @GetMapping("/compute")
    public ResponseEntity<Map<String, Object>> compute() {
        long requestId = requestCounter.incrementAndGet();
        long startTime = System.nanoTime();

        // CPU-intensive task
        double result = 0;
        for (int i = 0; i < 10000; i++) {
            result += Math.sqrt(i) * Math.sin(i);
        }

        long endTime = System.nanoTime();
        double processingTimeMs = (endTime - startTime) / 1_000_000.0;

        Map<String, Object> response = new HashMap<>();
        response.put("requestId", requestId);
        response.put("result", result);
        response.put("processingTimeMs", processingTimeMs);
        response.put("timestamp", Instant.now().toEpochMilli());

        return ResponseEntity.ok(response);
    }

    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> stats() {
        Runtime runtime = Runtime.getRuntime();
        long totalMemory = runtime.totalMemory();
        long freeMemory = runtime.freeMemory();
        long usedMemory = totalMemory - freeMemory;

        Map<String, Object> response = new HashMap<>();
        response.put("totalRequests", requestCounter.get());
        response.put("uptime", System.currentTimeMillis() - startTime);
        response.put("memoryUsedMB", usedMemory / (1024 * 1024));
        response.put("memoryTotalMB", totalMemory / (1024 * 1024));
        response.put("availableProcessors", runtime.availableProcessors());
        response.put("timestamp", Instant.now().toEpochMilli());

        return ResponseEntity.ok(response);
    }
}