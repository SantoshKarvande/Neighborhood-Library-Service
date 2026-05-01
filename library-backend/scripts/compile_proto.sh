#!/usr/bin/env bash
# scripts/compile_proto.sh
# Compiles proto/library.proto → app/proto_gen/library_pb2.py
# Run from the project root: bash scripts/compile_proto.sh

set -euo pipefail

PROTO_DIR="proto"
OUT_DIR="app/proto_gen"
PYTHON_BIN="python"

if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
fi

GRPC_PROTO_DIR="$("$PYTHON_BIN" -c 'import grpc_tools; import os; print(os.path.join(os.path.dirname(grpc_tools.__file__), "_proto"))')"

if [[ ! -d "$GRPC_PROTO_DIR" ]]; then
    echo "Error: grpc_tools bundled proto directory not found: $GRPC_PROTO_DIR" >&2
    echo "Try reinstalling grpcio-tools in the Python environment used by this script." >&2
    exit 1
fi

echo "Creating output directory: $OUT_DIR"
mkdir -p "$OUT_DIR"
touch "$OUT_DIR/__init__.py"

echo "Compiling $PROTO_DIR/library.proto ..."
"$PYTHON_BIN" -m grpc_tools.protoc \
    -I"$PROTO_DIR" \
    -I"$GRPC_PROTO_DIR" \
    --python_out="$OUT_DIR" \
    --pyi_out="$OUT_DIR" \
    "$PROTO_DIR/library.proto"

echo ""
echo "Generated files:"
ls -lh "$OUT_DIR"
echo ""
echo "Done! Proto stubs are in $OUT_DIR/"
