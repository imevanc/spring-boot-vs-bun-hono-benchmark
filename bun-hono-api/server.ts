import { Hono } from 'hono'
import { serve } from 'bun'

const app = new Hono()

let requestCounter = 0
const startTime = Date.now()

// Root endpoint
app.get('/', (c) => {
  return c.json({
    service: 'bun-hono-benchmark',
    version: '1.0.0',
    timestamp: Date.now()
  })
})

// Health check endpoint
app.get('/health', (c) => {
  const requestId = ++requestCounter
  return c.json({
    status: 'healthy',
    requestId,
    timestamp: Date.now(),
    uptime: Date.now() - startTime
  })
})

// Echo endpoint
app.post('/echo', async (c) => {
  const requestId = ++requestCounter
  const payload = await c.req.json()
  
  return c.json({
    requestId,
    received: payload,
    timestamp: Date.now(),
    processingTime: Math.floor(Math.random() * 4) + 1
  })
})

// User endpoint with simulated DB delay
app.get('/users/:id', async (c) => {
  const id = c.req.param('id')
  
  const requestId = ++requestCounter
  const user = {
    id,
    name: `User ${id}`,
    email: `user${id}@benchmark.com`,
    role: parseInt(id) % 2 === 0 ? 'admin' : 'user',
    createdAt: Date.now() - Math.floor(Math.random() * 86400000)
  }
  
  return c.json({
    requestId,
    user,
    timestamp: Date.now()
  })
})

// CPU-intensive endpoint
app.get('/compute', (c) => {
  const requestId = ++requestCounter
  const startTime = performance.now()
  
  // CPU-intensive task
  let result = 0
  for (let i = 0; i < 10000; i++) {
    result += Math.sqrt(i) * Math.sin(i)
  }
  
  const endTime = performance.now()
  const processingTimeMs = endTime - startTime
  
  return c.json({
    requestId,
    result,
    processingTimeMs,
    timestamp: Date.now()
  })
})

// Stats endpoint
app.get('/stats', (c) => {
  const memUsage = process.memoryUsage()
  
  return c.json({
    totalRequests: requestCounter,
    uptime: Date.now() - startTime,
    memoryUsedMB: Math.round(memUsage.heapUsed / 1024 / 1024),
    memoryTotalMB: Math.round(memUsage.heapTotal / 1024 / 1024),
    timestamp: Date.now()
  })
})

// Export for Bun serve
export default {
  port: 3000,
  fetch: app.fetch,
}

console.log('Bun+Hono server starting on port 3000...')