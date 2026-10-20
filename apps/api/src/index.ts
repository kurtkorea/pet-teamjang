import Fastify from "fastify";
import cors from "@fastify/cors";
import pg from "pg";
import websocket from "@fastify/websocket";
import { readdir, stat } from "node:fs/promises";
import path from "node:path";
import Redis from "ioredis";

const app = Fastify({ logger: true });
const aiWorkerUrl = process.env.AI_WORKER_URL ?? "http://localhost:8001";
const events: unknown[] = [];
const pool = process.env.DATABASE_URL ? new pg.Pool({ connectionString: process.env.DATABASE_URL }) : null;
const sockets = new Set<any>();
const redisSubscriber = new Redis(process.env.REDIS_URL ?? "redis://localhost:6379");
function broadcast(payload: unknown) {
  const message = JSON.stringify(payload);
  sockets.forEach((socket) => {
    if (socket.readyState === 1) socket.send(message);
  });
}

async function latestRecording(root = "/data/recordings"): Promise<string | null> {
  const files: { path: string; mtime: number }[] = [];
  async function walk(dir: string) {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) await walk(full);
      else if (entry.name.endsWith(".mp4")) {
        const info = await stat(full);
        if (info.size > 0 && Date.now() - info.mtimeMs > 15_000) files.push({ path: full, mtime: info.mtimeMs });
      }
    }
  }
  try { await walk(root); } catch { return null; }
  return files.sort((a, b) => a.mtime - b.mtime).at(-1)?.path ?? null;
}
await app.register(cors, { origin: true });
await app.register(websocket);
await redisSubscriber.subscribe("pet:detections");
redisSubscriber.on("message", (_channel, message) => {
  try { broadcast(JSON.parse(message)); } catch (error) { app.log.warn({ error }, "invalid detection message"); }
});

app.get("/health", async () => ({ status: "ok", service: "api" }));

app.get("/api/v1/events", async () => {
  if (!pool) return { events };
  const result = await pool.query("SELECT * FROM pet_events ORDER BY occurred_at DESC LIMIT 200");
  return { events: result.rows };
});

app.get("/ws/detections", { websocket: true }, (socket) => {
  sockets.add(socket);
  socket.on("close", () => sockets.delete(socket));
});

app.post("/internal/detections", async (request) => {
  broadcast(request.body);
  return { broadcasted: sockets.size };
});

app.post("/api/v1/inference/latest", async (request, reply) => {
  const framePath = await latestRecording();
  if (!framePath) return reply.code(404).send({ error: "No recording found" });
  const response = await fetch(`${aiWorkerUrl}/infer`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ camera_id: "tc70-01", frame_path: framePath, sample_every: 30 })
  });
  if (!response.ok) return reply.code(502).send({ error: "AI worker failed", status: response.status });
  const result = await response.json() as { detections?: unknown[]; behaviors?: unknown[] };
  broadcast({ cameraId: "tc70-01", framePath, detections: result.detections ?? [], behaviors: result.behaviors ?? [] });
  return { framePath, ...result };
});

app.post("/api/v1/live/start", async (_request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/live/start`, { method: "POST" });
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.post("/api/v1/live/stop", async (_request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/live/stop`, { method: "POST" });
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.post<{ Body: { direction: string } }>("/api/v1/cameras/:cameraId/ptz", async (request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/ptz/move`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(request.body) });
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.post<{ Body: { enabled: boolean; dead_zone?: number; sensitivity?: number; speed?: number } }>("/api/v1/cameras/:cameraId/ptz/auto-track", async (request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/ptz/auto-track`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(request.body) });
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.get("/api/v1/inference/config", async (_request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/config/inference`);
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.post<{ Body: { target?: "human" | "dog"; imgsz: number; conf: number; iou: number; max_det: number } }>("/api/v1/inference/config", async (request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/config/inference`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(request.body) });
  const body = await response.text();
  return reply.code(response.status).type("application/json").send(body);
});

app.get("/api/v1/cameras/:cameraId/stream", async (request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/stream`);
  if (!response.ok || !response.body) return reply.code(502).send({ error: "AI worker stream unavailable" });
  reply.header("content-type", response.headers.get("content-type") ?? "multipart/x-mixed-replace; boundary=frame");
  return reply.send(response.body);
});

app.post<{ Body: { cameraId: string; framePath?: string; sampleEvery?: number } }>("/api/v1/inference", async (request, reply) => {
  const response = await fetch(`${aiWorkerUrl}/infer`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      camera_id: request.body.cameraId,
      frame_path: request.body.framePath,
      sample_every: request.body.sampleEvery ?? 30
    })
  });
  if (!response.ok) return reply.code(502).send({ error: "AI worker failed", status: response.status });
  const result = await response.json() as { events?: unknown[] };
  events.push(...(result.events ?? []));
  return result;
});

await app.listen({ host: "0.0.0.0", port: 3000 });
