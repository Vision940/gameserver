TARGET := $(word 2,$(MAKECMDGOALS))
SPRITE_DIR := static/games/sprites/$(TARGET)

.PHONY: sprites
sprites:
	@if [ -z "$(TARGET)" ]; then \
		echo 'Usage: make sprites <target>'; \
		exit 1; \
	fi
	@find "$(SPRITE_DIR)" -type f -name '*.txt' -exec dev/gensprite {} \;

%:
	@:

