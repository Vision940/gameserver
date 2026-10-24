TARGET := $(word 2,$(MAKECMDGOALS))
SPRITE_DIR := static/games/$(TARGET)/sprites
TEST_DIR := dev/tests

#TODO: add ascii to make ascii to sprite
#TODO: add devserver business
#TODO: make sprites all
.PHONY: sprites test
sprites:
	@TARGET=$(TARGET); \
	if [ -z "$$TARGET" ]; then \
		echo 'Usage: make sprites <target> (defaulting to all)'; \
		TARGET="all"; \
	fi; \
	if [ "$$TARGET" = "all" ]; then \
		find static/games -type d -name sprites | while read dir; do \
			echo "Generating sprites in $$dir"; \
			find "$$dir" -type f -name '*.txt' -exec dev/gensprite {} \;; \
		done; \
	else \
		find "$(SPRITE_DIR)" -type f -name '*.txt' -exec dev/gensprite {} \;; \
	fi

test:
	@set -e; \
	for test_file in "$(TEST_DIR)"/*.sh; do \
		[ -e "$$test_file" ] || continue; \
		echo "Running $$test_file"; \
		bash "$$test_file"; \
	done

%:
	@:

