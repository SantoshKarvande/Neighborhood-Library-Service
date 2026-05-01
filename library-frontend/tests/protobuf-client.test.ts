import fs from "node:fs";
import path from "node:path";
import protobuf from "protobufjs";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  buildUrl,
  callOperation,
  normalizeFormValues,
  operations
} from "../lib/api";
import {
  PROTO_CONTENT_TYPE,
  decodeMessage,
  encodeMessage,
  resetProtoRootForTests,
  setProtoRootForTests
} from "../lib/protobuf";

function exactArrayBuffer(bytes: Uint8Array): ArrayBuffer {
  return bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
}

function loadTestRoot() {
  (protobuf.parse as typeof protobuf.parse & { defaults: { keepCase: boolean } }).defaults.keepCase = true;
  const root = new protobuf.Root();
  const timestampProto = fs.readFileSync(
    path.join(process.cwd(), "public/proto/google/protobuf/timestamp.proto"),
    "utf8"
  );
  const libraryProto = fs
    .readFileSync(path.join(process.cwd(), "public/proto/library.proto"), "utf8")
    .replace('import "google/protobuf/timestamp.proto";', "");

  protobuf.parse(timestampProto, root, { keepCase: true });
  protobuf.parse(libraryProto, root, { keepCase: true });
  return root;
}

describe("protobuf REST client", () => {
  beforeEach(() => {
    process.env.NEXT_PUBLIC_LIBRARY_API_BASE_URL = "http://localhost:8000/api/v1";
    setProtoRootForTests(loadTestRoot());
  });

  afterEach(() => {
    vi.restoreAllMocks();
    resetProtoRootForTests();
  });

  it("encodes and decodes CreateAuthorRequest/AuthorResponse", async () => {
    const bytes = await encodeMessage("CreateAuthorRequest", { name: "Octavia Butler" });
    expect(bytes.length).toBeGreaterThan(0);

    const root = loadTestRoot();
    const AuthorResponse = root.lookupType("library.v1.AuthorResponse");
    const responseBytes = AuthorResponse.encode(
      AuthorResponse.create({
        author: { author_id: 7, name: "Octavia Butler" }
      })
    ).finish();

    const decoded = await decodeMessage("AuthorResponse", exactArrayBuffer(responseBytes));
    expect(decoded).toEqual({ author: { author_id: "7", name: "Octavia Butler" } });
  });

  it("builds query URLs from clear text form values", () => {
    const listBooks = operations.find((operation) => operation.id === "listBooks")!;
    const values = normalizeFormValues({
      skip: "0",
      limit: "10",
      search: "Dune",
      author_id: "3",
      available_only: true
    });

    expect(buildUrl(listBooks, values)).toBe(
      "http://localhost:8000/api/v1/books/?skip=0&limit=10&search=Dune&author_id=3&available_only=true"
    );
  });

  it("sends protobuf request and decodes protobuf response for create member", async () => {
    const root = loadTestRoot();
    const MemberResponse = root.lookupType("library.v1.MemberResponse");
    const responseBytes = MemberResponse.encode(
      MemberResponse.create({
        member: {
          member_id: 42,
          name: "Alice Proto",
          email: "alice@example.com",
          phone: "123"
        }
      })
    ).finish();

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(responseBytes, {
        status: 201,
        headers: { "content-type": PROTO_CONTENT_TYPE }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    const operation = operations.find((item) => item.id === "createMember")!;
    const result = await callOperation(operation, {
      name: "Alice Proto",
      email: "alice@example.com",
      phone: "123"
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/members/",
      expect.objectContaining({
        method: "POST",
        headers: {
          Accept: PROTO_CONTENT_TYPE,
          "Content-Type": PROTO_CONTENT_TYPE
        },
        body: expect.any(Object)
      })
    );
    expect(fetchMock.mock.calls[0][1].body.byteLength).toBeGreaterThan(0);
    expect(result).toEqual({
      member: {
        member_id: "42",
        name: "Alice Proto",
        email: "alice@example.com",
        phone: "123"
      }
    });
  });

  it("encodes borrow due_date as protobuf Timestamp", async () => {
    const operation = operations.find((item) => item.id === "borrowBook")!;
    const root = loadTestRoot();
    const TransactionResponse = root.lookupType("library.v1.TransactionResponse");
    const responseBytes = TransactionResponse.encode(
      TransactionResponse.create({
        transaction: {
          transaction_id: 9,
          copy_id: 4,
          member_id: 2,
          status: "TRANSACTION_STATUS_BORROWED"
        }
      })
    ).finish();

    const fetchMock = vi.fn().mockResolvedValue(
      new Response(responseBytes, {
        status: 201,
        headers: { "content-type": PROTO_CONTENT_TYPE }
      })
    );
    vi.stubGlobal("fetch", fetchMock);

    await callOperation(operation, {
      copy_id: "4",
      member_id: "2",
      due_date: "2026-06-01T10:30"
    });

    const request = fetchMock.mock.calls[0][1];
    const BorrowRequest = root.lookupType("library.v1.BorrowRequest");
    const decodedRequest = BorrowRequest.decode(new Uint8Array(request.body));
    const plain = BorrowRequest.toObject(decodedRequest, { longs: String, objects: true });

    expect(plain.copy_id).toBe("4");
    expect(plain.member_id).toBe("2");
    expect(plain.due_date).toHaveProperty("seconds");
  });
});
