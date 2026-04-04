TARGET := $(word 2,$(MAKECMDGOALS))
SPRITE_DIR := static/games/$(TARGET)/sprites
TEST_DIR := dev/tests

.PHONY: sprites test
sprites:
	@if [ -z "$(TARGET)" ]; then \
		echo 'Usage: make sprites <target>'; \
		exit 1; \
	fi
	@find "$(SPRITE_DIR)" -type f -name '*.txt' -exec dev/gensprite {} \;

test:
	@set -e; \
	for test_file in "$(TEST_DIR)"/*.bash; do \
		[ -e "$$test_file" ] || continue; \
		echo "Running $$test_file"; \
		bash "$$test_file"; \
	done

%:
	@:

