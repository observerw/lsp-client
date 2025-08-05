# 使用官方Go镜像，自动支持多平台架构
FROM golang:1.24-alpine

# 安装必要的工具
RUN apk add --no-cache git ca-certificates

# 设置Go环境变量
ENV GOPATH=/go
ENV GOBIN=/go/bin
ENV PATH=$GOBIN:$PATH

# Install gopls (Go Language Server)
# Using @latest to get the most recent version compatible with Go 1.24
RUN go install golang.org/x/tools/gopls@latest

# Install additional useful Go tools for development
RUN go install golang.org/x/tools/cmd/goimports@latest && \
    go install github.com/go-delve/delve/cmd/dlv@latest && \
    go install honnef.co/go/tools/cmd/staticcheck@latest

# Set working directory
WORKDIR /workspace

# Verify installations
RUN go version && gopls version

# Default command
CMD ["/bin/bash"]