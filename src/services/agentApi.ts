export type ChatMessage = { role: 'user' | 'assistant' | 'tool'; content: string };
export type AgentContext = Record<string, unknown>;

export type AgentEvent<T = unknown> = {
  event: string;
  data: T;
};

// Generic SSE over fetch POST (since EventSource only supports GET)
export async function streamAgent<T = unknown>(
  url: string,
  payload: { messages: ChatMessage[]; context?: AgentContext },
  onEvent: (e: AgentEvent<T>) => void,
  opts?: { signal?: AbortSignal }
): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
    },
    body: JSON.stringify(payload),
    signal: opts?.signal,
  });
  if (!res.ok) throw new Error(`SSE request failed: ${res.status} ${res.statusText}`);
  if (!res.body) throw new Error('No response body');

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    // Parse SSE frames with support for both LF and CRLF delimiters
    // Find earliest frame boundary among "\n\n" and "\r\n\r\n"
    // Continue extracting frames until no full frame remains in buffer
    // This prevents UI from stalling when server uses CRLF
    // and avoids losing whitespace inside JSON payloads
    while (true) {
      const lfIdx = buffer.indexOf('\n\n');
      const crlfIdx = buffer.indexOf('\r\n\r\n');
      let frameIdx = -1;
      let delimLen = 0;
      if (lfIdx >= 0 && (crlfIdx < 0 || lfIdx < crlfIdx)) {
        frameIdx = lfIdx;
        delimLen = 2;
      } else if (crlfIdx >= 0) {
        frameIdx = crlfIdx;
        delimLen = 4;
      }

      if (frameIdx < 0) break;

      const raw = buffer.slice(0, frameIdx);
      buffer = buffer.slice(frameIdx + delimLen);

      const lines = raw.split(/\r?\n/);
      let event = 'message';
      const dataLines: string[] = [];
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
      }
      const dataStr = dataLines.join('\n');
      if (dataStr) {
        try {
          const parsed = JSON.parse(dataStr) as T;
          onEvent({ event, data: parsed });
        } catch {
          onEvent({ event, data: (dataStr as unknown) as T });
        }
      }
    }
  }
}

export async function completeAgent<T = { text: string; intent?: string; citations?: unknown[] }>(
  url: string,
  payload: { messages: ChatMessage[]; context?: AgentContext }
): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Complete request failed: ${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}
