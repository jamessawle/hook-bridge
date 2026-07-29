#!/usr/bin/env bash

set -euo pipefail

repository_root=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
sandbox_name=${SANDBOX_NAME:-hook-bridge}
sbx_kits_base='git+https://github.com/jamessawle/sbx-kits.git#ref=v0.2.0'
kits=(
	'git+https://github.com/docker/sbx-kits-contrib.git#ref=v0.12.0&dir=mise'
	"$sbx_kits_base&dir=kits/mise/network-python-uv"
	"$sbx_kits_base&dir=kits/language/python-uv"
	"$sbx_kits_base&dir=kits/harness/codex"
)
kit_sources='["docker.io/","github.com/docker/","github.com/jamessawle/"]'

require_sbx() {
	command -v sbx >/dev/null 2>&1 || {
		echo "Docker Sandbox (sbx) is required." >&2
		exit 1
	}
}

validate_kits() {
	for kit in "${kits[@]}"; do
		DOCKER_SANDBOXES_KIT_ALLOWED_SOURCES=$kit_sources \
			sbx kit validate "$kit"
	done
}

setup_repository() {
	sbx exec \
		--workdir "$repository_root" \
		"$sandbox_name" \
		mise trust
	sbx exec \
		--workdir "$repository_root" \
		"$sandbox_name" \
		mise run setup
}

require_sbx

case "${1:-}" in
attach)
	setup_repository
	exec sbx run --name "$sandbox_name"
	;;
rebuild)
	validate_kits
	if sbx inspect "$sandbox_name" >/dev/null 2>&1; then
		sbx rm --force "$sandbox_name"
	fi

	create_args=(sbx create --name "$sandbox_name")
	for kit in "${kits[@]}"; do
		create_args+=(--kit "$kit")
	done
	DOCKER_SANDBOXES_KIT_ALLOWED_SOURCES=$kit_sources \
		"${create_args[@]}" codex "$repository_root"
	setup_repository
	;;
*)
	echo "usage: $0 <attach|rebuild>" >&2
	exit 2
	;;
esac
