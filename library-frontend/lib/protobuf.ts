import protobuf from "protobufjs";

export const PROTO_CONTENT_TYPE = "application/x-protobuf";

let rootPromise: Promise<protobuf.Root> | null = null;

export type PlainRecord = Record<string, unknown>;

export function getApiBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_LIBRARY_API_BASE_URL ??
    "http://localhost:8000/api/v1"
  ).replace(/\/$/, "");
}

export function loadProtoRoot(): Promise<protobuf.Root> {
  if (!rootPromise) {
    (protobuf.parse as typeof protobuf.parse & { defaults: { keepCase: boolean } }).defaults.keepCase = true;
    rootPromise = protobuf.load("/proto/library.proto");
  }
  return rootPromise;
}

export function setProtoRootForTests(root: protobuf.Root): void {
  rootPromise = Promise.resolve(root);
}

export function resetProtoRootForTests(): void {
  rootPromise = null;
}

export async function encodeMessage(
  messageName: string,
  payload: PlainRecord
): Promise<Uint8Array> {
  const root = await loadProtoRoot();
  const MessageType = root.lookupType(`library.v1.${messageName}`);
  const prepared = prepareOutgoing(payload) as PlainRecord;
  const validationError = MessageType.verify(prepared);

  if (validationError) {
    throw new Error(`${messageName} validation failed: ${validationError}`);
  }

  return MessageType.encode(MessageType.create(prepared)).finish();
}

export async function decodeMessage(
  messageName: string,
  bytes: ArrayBuffer
): Promise<PlainRecord> {
  const root = await loadProtoRoot();
  const MessageType = root.lookupType(`library.v1.${messageName}`);
  const decoded = MessageType.decode(new Uint8Array(bytes));

  return MessageType.toObject(decoded, {
    longs: String,
    enums: String,
    defaults: false,
    arrays: true,
    objects: true
  }) as PlainRecord;
}

export function prepareOutgoing(value: unknown): unknown {
  if (Array.isArray(value)) {
    return value.map(prepareOutgoing);
  }

  if (!value || typeof value !== "object") {
    return value;
  }

  const input = value as PlainRecord;
  const output: PlainRecord = {};

  for (const [key, rawValue] of Object.entries(input)) {
    if (rawValue === "" || rawValue === null || rawValue === undefined) {
      continue;
    }

    if (key === "due_date" && typeof rawValue === "string") {
      output[key] = dateInputToTimestamp(rawValue);
    } else {
      output[key] = prepareOutgoing(rawValue);
    }
  }

  return output;
}

export function dateInputToTimestamp(value: string): PlainRecord {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    throw new Error(`Invalid date/time: ${value}`);
  }

  return {
    seconds: Math.floor(date.getTime() / 1000),
    nanos: (date.getTime() % 1000) * 1_000_000
  };
}

export async function decodeErrorResponse(response: Response): Promise<string> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes(PROTO_CONTENT_TYPE)) {
    const data = await decodeMessage("ErrorResponse", await response.arrayBuffer());
    return `${data.error ?? "Request failed"}: ${data.detail ?? response.statusText}`;
  }

  const text = await response.text();
  return text || response.statusText || `HTTP ${response.status}`;
}

export function formatResult(data: unknown): string {
  return JSON.stringify(data, null, 2);
}
