sync-pyrefly:
    rm -rf tests/assets/pyrefly tests/assets/temp_pyrefly
    git clone --depth 1 --filter=blob:none --sparse https://github.com/facebook/pyrefly tests/assets/temp_pyrefly
    cd tests/assets/temp_pyrefly && git sparse-checkout set pyrefly/lib/test/lsp
    mv tests/assets/temp_pyrefly/pyrefly/lib/test/lsp tests/assets/pyrefly
    rm -rf tests/assets/temp_pyrefly

pdoc:
    mkdir -p dist
    uv run pdoc src/lsp_client --output-dir dist --docformat google
