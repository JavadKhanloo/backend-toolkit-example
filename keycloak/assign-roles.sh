#!/usr/bin/env bash
set -euo pipefail

SERVER="${KEYCLOAK_SERVER:-http://keycloak:8080}"
ADMIN_USER="${KC_BOOTSTRAP_ADMIN_USERNAME:-${KEYCLOAK_ADMIN:-admin}}"
ADMIN_PASSWORD="${KC_BOOTSTRAP_ADMIN_PASSWORD:-${KEYCLOAK_ADMIN_PASSWORD:-admin}}"
KCADM="/opt/keycloak/bin/kcadm.sh"

echo "Waiting for Keycloak admin API at ${SERVER}..."
for _ in $(seq 1 90); do
  if "${KCADM}" config credentials \
    --server "${SERVER}" \
    --realm master \
    --user "${ADMIN_USER}" \
    --password "${ADMIN_PASSWORD}" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

"${KCADM}" config credentials \
  --server "${SERVER}" \
  --realm master \
  --user "${ADMIN_USER}" \
  --password "${ADMIN_PASSWORD}"

echo "Waiting for realm app..."
for _ in $(seq 1 60); do
  if "${KCADM}" get realms/app >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

"${KCADM}" create roles -r app -s name=user >/dev/null 2>&1 || true
"${KCADM}" create roles -r app -s name=admin >/dev/null 2>&1 || true

"${KCADM}" add-roles -r app --uusername alice --rolename user || true
"${KCADM}" add-roles -r app --uusername admin --rolename user || true
"${KCADM}" add-roles -r app --uusername admin --rolename admin || true

echo "Keycloak realm app is ready."
