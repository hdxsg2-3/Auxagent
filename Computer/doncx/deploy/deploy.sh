#!/usr/bin/env bash
# Auxagent 服务器端部署脚本
#
# 由 GitHub Actions 通过 SSH 调用，也可以手工执行：
#   bash deploy.sh /tmp/auxagent-deploy.tar.gz
#
# 设计前提（按需求确定）：
#   - 直接覆盖部署到 app/，不做版本目录、不做回滚、不备份
#   - shared/（.env、SQLite 数据、venv、日志）永不触碰
#   - 每次部署都执行 pip install：依赖清单可能新增包，交由 pip 自身的
#     下载缓存（服务器 ~/.cache/pip）加速，不做自定义跳过判断
set -euo pipefail

ARCHIVE="${1:?用法: deploy.sh <发布包路径>}"
START_TS="$(date +%s)"

APP_DIR="/home/lighthouse/sziit/auxagent/app"
SHARED_DIR="/home/lighthouse/sziit/auxagent/shared"
VENV_PIP="${SHARED_DIR}/venv/bin/pip"
PIP_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
SERVICE="auxagent"
HEALTH_URL="http://127.0.0.1:5000/api/health"

log() { echo "[deploy] $*"; }

log "1/6 校验并解压发布包"
[ -f "${ARCHIVE}" ] || { echo "找不到发布包: ${ARCHIVE}" >&2; exit 1; }
STAGE="$(mktemp -d /tmp/auxagent-stage.XXXXXX)"
trap 'rm -rf "${STAGE}"' EXIT
tar -xzf "${ARCHIVE}" -C "${STAGE}"
[ -d "${STAGE}/backend" ] || { echo "发布包缺少 backend 目录" >&2; exit 1; }
[ -f "${STAGE}/frontend/dist/index.html" ] || { echo "发布包缺少前端构建产物 frontend/dist/index.html" >&2; exit 1; }

log "2/6 同步后端代码（--checksum：内容相同的文件不重写，保留 __pycache__ 以复用字节码缓存）"
mkdir -p "${APP_DIR}/backend" "${APP_DIR}/frontend/dist"
rsync -a --checksum --delete --exclude '__pycache__/' "${STAGE}/backend/" "${APP_DIR}/backend/"

log "3/6 同步前端构建产物"
rsync -a --checksum --delete "${STAGE}/frontend/dist/" "${APP_DIR}/frontend/dist/"

log "4/6 安装依赖（清华镜像；已装过的包走 pip 本地缓存，不重复下载）"
"${VENV_PIP}" install -q --index-url "${PIP_INDEX}" --timeout 60 \
  -r "${APP_DIR}/backend/requirements-server.txt"

log "5/6 重启服务"
sudo systemctl restart "${SERVICE}"

log "6/6 健康检查"
healthy=0
for _ in $(seq 1 20); do
  if curl -fsS --max-time 5 "${HEALTH_URL}" >/dev/null 2>&1; then
    healthy=1
    break
  fi
  sleep 1
done
if [ "${healthy}" != "1" ]; then
  echo "[deploy] 健康检查失败，服务最近日志：" >&2
  sudo journalctl -u "${SERVICE}" -n 30 --no-pager >&2 || true
  exit 1
fi

echo "[deploy] 健康检查通过：$(curl -s "${HEALTH_URL}")"
echo "[deploy] 服务状态：$(systemctl is-active "${SERVICE}")"
echo "[deploy] 前端产物：$(grep -o 'assets/[^"]*\.js' "${APP_DIR}/frontend/dist/index.html" || true)"
log "部署完成，耗时 $(( $(date +%s) - START_TS )) 秒"
