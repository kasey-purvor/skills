---
  name: spark-vllm
  description: Use this skill whenever the user wants to run LLM inference against their own hardware instead of a cloud API —
  specifically a vLLM OpenAI-compatible endpoint running on their NVIDIA Spark box over Tailscale. Triggers include "hit my
  spark", "use my local model", "run this through Qwen locally", batch inference jobs the user wants routed to their own GPU, or
  any task where shipping prompts to an OpenAI-shape API on their home network would be appropriate.
  ---

  # Spark vLLM — local OpenAI-compatible inference

  The user owns an NVIDIA DGX Spark (GB10 Grace Blackwell, aarch64, 128 GB unified memory) running a containerized vLLM server.
  It's reachable over Tailscale from any device on their tailnet. Use this endpoint instead of the Claude API when the user asks
  for "local" inference, explicitly names the Spark, or is doing batch work where latency and cost favor their own hardware.

  ## Connection

  | | Value |
  |---|---|
  | **Base URL** | `http://100.97.157.50:8000/v1` |
  | **Tailscale hostname (also works)** | `http://spark-7d98:8000/v1` |
  | **Model ID** | `Qwen/Qwen2.5-32B-Instruct` |
  | **API key** | vLLM does not authenticate. Pass any string, e.g. `"EMPTY"` or `"sk-local"` |
  | **Protocol** | OpenAI Chat Completions API (spec-compatible) |

  The user's Tailscale must be connected for the base URL to resolve/route. If not, prompt them to run `tailscale status` locally.

  ## Endpoints

  ```
  POST /v1/chat/completions     primary inference endpoint
  POST /v1/completions          legacy text completions (prefer chat)
  GET  /v1/models               list loaded models
  GET  /health                  liveness probe
  GET  /metrics                 Prometheus-format server metrics
  ```

  **Not available:** `/v1/embeddings`, `/v1/audio`, `/v1/images`, Assistants API, Threads, Batch API, Moderation. vLLM is
  inference-only.

  ## Chat completions — the shape you'll use 95% of the time

  Request body is standard OpenAI:

  ```json
  {
    "model": "Qwen/Qwen2.5-32B-Instruct",
    "messages": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "..."},
      {"role": "assistant", "content": "..."}
    ],
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "stream": false,
    "stop": ["\n\n"],
    "seed": 42,
    "tools": [...],
    "tool_choice": "auto"
  }
  ```

  Response is standard OpenAI chat completion JSON — read `choices[0].message.content`.

  **Server is stateless.** No session memory between calls. For multi-turn conversations, the client must resend the full
  `messages` array each turn (vLLM caches the KV state for repeated prefixes, so this is cheap — don't try to optimize by sending
  only the new turn).

  **Context limit:** 8192 tokens. If the `messages` array plus requested `max_tokens` exceeds this, the request fails.

  ## Invocation patterns

  ### curl — single command (must be one line, or use `\` continuations)

  ```bash
  curl http://100.97.157.50:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"model":"Qwen/Qwen2.5-32B-Instruct","messages":[{"role":"user","content":"say hi"}],"max_tokens":20}'
  ```

  ### curl — streaming (SSE)

  Add `"stream": true` to the body and pass `-N` to curl (disables output buffering so events print as they arrive):

  ```bash
  curl -N http://100.97.157.50:8000/v1/chat/completions \
    -H 'Content-Type: application/json' \
    -d '{"model":"Qwen/Qwen2.5-32B-Instruct","messages":[{"role":"user","content":"count to 10"}],"stream":true}'
  ```

  Response is `data: {...}\n\ndata: {...}\n\n...data: [DONE]\n\n`.

  ### Python — OpenAI SDK, synchronous

  ```python
  from openai import OpenAI

  client = OpenAI(
      base_url="http://100.97.157.50:8000/v1",
      api_key="EMPTY",
  )

  resp = client.chat.completions.create(
      model="Qwen/Qwen2.5-32B-Instruct",
      messages=[{"role": "user", "content": "Explain attention in one paragraph."}],
      max_tokens=256,
  )
  print(resp.choices[0].message.content)
  ```

  ### Python — streaming

  ```python
  stream = client.chat.completions.create(
      model="Qwen/Qwen2.5-32B-Instruct",
      messages=[{"role": "user", "content": "Count to 10."}],
      stream=True,
  )
  for chunk in stream:
      if chunk.choices[0].delta.content:
          print(chunk.choices[0].delta.content, end="", flush=True)
  ```

  ### Python — multi-turn conversation

  ```python
  history = [{"role": "system", "content": "You are a senior backend engineer."}]

  def ask(msg: str) -> str:
      history.append({"role": "user", "content": msg})
      r = client.chat.completions.create(
          model="Qwen/Qwen2.5-32B-Instruct",
          messages=history,
      )
      reply = r.choices[0].message.content
      history.append({"role": "assistant", "content": reply})
      return reply
  ```

  ### Python — async concurrent batch (for batch jobs)

  vLLM's **continuous batching** handles server-side fusing. Client just needs to fire many requests concurrently. Do **NOT** try
  to pack prompts into one request; send them in parallel instead.

  ```python
  import asyncio
  from openai import AsyncOpenAI
  from tqdm.asyncio import tqdm_asyncio

  client = AsyncOpenAI(base_url="http://100.97.157.50:8000/v1", api_key="EMPTY")

  async def one(prompt: str) -> str:
      r = await client.chat.completions.create(
          model="Qwen/Qwen2.5-32B-Instruct",
          messages=[{"role": "user", "content": prompt}],
          max_tokens=256,
      )
      return r.choices[0].message.content

  async def run(prompts: list[str], concurrency: int = 32) -> list[str]:
      sem = asyncio.Semaphore(concurrency)
      async def bounded(p):
          async with sem:
              return await one(p)
      return await tqdm_asyncio.gather(*[bounded(p) for p in prompts])

  results = asyncio.run(run(my_prompts, concurrency=32))
  ```

  Start with `concurrency=32`. If GPU utilization (user can check with `nvtop` on the Spark) is below ~80%, raise it. If requests
  start queueing (you'll see `vllm:num_requests_waiting` climb on `/metrics`), you've maxed it.

  ### Tool calls

  Qwen2.5 supports OpenAI-shape tool calls. Pass `tools` and optionally `tool_choice` in the request; the response may include
  `choices[0].message.tool_calls`. Parse them the same way you would for OpenAI's GPT-4 tool calls. The format matches.

  ## Server behavior the agent should know

  - **Stateless**: no session state between calls. Client holds history.
  - **Continuous batching**: concurrent requests are fused GPU-side. Don't serialize client-side.
  - **Prefix caching**: repeated message prefixes are KV-cached. Resending full history is near-free.
  - **Max context**: 8192 tokens (prompt + completion combined).
  - **Warmup**: first request after a long idle period may take 5–10s (CUDA graph + torch.compile cache is warm but vLLM may
  re-initialize some paths). Subsequent are fast.
  - **Default sampling**: if `temperature`/`top_p` not passed, vLLM uses model defaults. For deterministic output, set
  `temperature=0` and `seed` to a fixed value.

  ## Gotchas and troubleshooting

  **"Connection refused" or hang from dev machine**
  - Check Tailscale is up: `tailscale status` should list `spark-7d98`.
  - If listed but unreachable, nudge the tunnel: `tailscale ping spark-7d98`.
  - If Tailscale is fine, the vLLM container may be down. The user can SSH to the Spark and run:
    ```bash
    docker ps --filter name=vllm
    docker compose -f ~/dev/infrastructure/services/vllm/docker-compose.yml logs --tail=50
    ```

  **"curl: option -d: requires parameter"**
  - The JSON body was pasted onto a new line without `\` continuation. Use one long line or escape newlines.

  **Streaming appears to hang in terminal**
  - Some shells/prompts buffer SSE output. Confirm by first running the same request non-streaming; if that works, connectivity is
   fine.

  **"Context length exceeded" errors**
  - Prompt + `max_tokens` > 8192. Either shrink the prompt (drop older turns) or reduce `max_tokens`.

  **Model doesn't know about recent events/hardware**
  - Qwen2.5-32B-Instruct has a pre-2024 training cutoff. It doesn't know about GB10, Spark, or the user's machine. For queries
  that need fresh info, provide it in the prompt (RAG-style).

  **Slow first response after writing code**
  - If the Spark was idle for a while or container restarted, first call takes longer. Don't retry — just wait.

  ## When NOT to use this

  - Real-time user-facing chat where latency <500ms matters — Claude API will usually be faster.
  - Tasks requiring embeddings, audio, image, or moderation endpoints (not loaded).
  - When the user wants Claude specifically, or is debugging Claude behavior.
  - When the user's Tailscale is down and they want a quick result — fall back to Claude API.

  ## Useful status / debugging commands (on the Spark, via SSH)

  ```bash
  # Is vLLM up?
  docker ps --filter name=vllm

  # Recent logs
  docker compose -f ~/dev/infrastructure/services/vllm/docker-compose.yml logs --tail=100

  # GPU utilization (the real bottleneck)
  nvtop

  # Live request/queue metrics
  curl -s http://localhost:8000/metrics | grep -E 'vllm:num_requests|vllm:gpu_cache|vllm:time_to'
  ```

  ## Hardware context (for agents that care)

  - GPU: NVIDIA GB10 Grace Blackwell, compute capability 12.1
  - Memory: 128 GB unified (CPU+GPU share one pool)
  - Runtime: `nvcr.io/nvidia/vllm:25.11-py3` (Blackwell-native kernels, NVFP4-capable)
  - Model weights cached on host at `~/.cache/huggingface` and mounted into the container