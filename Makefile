PYBABEL := .venv/bin/pybabel
TRANSLATIONS := src/translations
LANGUAGES := es fr nl sv

.PHONY: update-po compile-mo

run:
	docker compose -f docker-compose.dev.yml up --build

# Extract new strings from source and refresh all .po files
update-po:
	$(PYBABEL) extract -F babel.cfg -o $(TRANSLATIONS)/messages.pot src
	for lang in $(LANGUAGES); do \
		$(PYBABEL) update -i $(TRANSLATIONS)/messages.pot -d $(TRANSLATIONS) -l $$lang --previous; \
	done
	rm -f $(TRANSLATIONS)/messages.pot

# Compile all .po files into .mo binaries
compile-mo:
	$(PYBABEL) compile -d $(TRANSLATIONS)
