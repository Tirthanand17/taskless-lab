# B4c4 GitHub-hosted technical inert image only: NO AWS push, NO YouTube.
# Caller must supply a registry RESOLVED @sha256:<64hex> base reference.
# Never build with a mutable base tag or expose owner credentials.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="FlowMinute inert owner cloud boot guard"
LABEL org.opencontainers.image.description="Owner read-only guard; no network/provider/upload operations"
LABEL flowminute.release_authorized="false"
LABEL flowminute.production_deployed="false"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLOWMINUTE_RUNTIME_MODE=OWNER_READ_ONLY_BOOT_GUARD \
    FLOWMINUTE_ENABLE_PUBLISH=0 \
    PUBLISH_ENABLED=false \
    FLOWMINUTE_ALLOW_LAPTOP=0 \
    FLOWMINUTE_ENABLE_GEMINI=0 \
    FLOWMINUTE_MODEL_PAID_SPEND_USD=0 \
    FLOWMINUTE_RUNTIME_NETWORK_AUTHORIZED=0 \
    FLOWMINUTE_OWNER_RELEASE_AUTHORIZED=0

WORKDIR /app
COPY --chown=65532:65532 autopilot /app/autopilot

USER 65532:65532
ENTRYPOINT ["python","-B","-m","autopilot.b4c2_runtime_boot_guard"]
