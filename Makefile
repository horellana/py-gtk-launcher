build:
	cp src/* build/
	pip install --target ./build/vendor -r requirements.txt

install:
	sudo cp systemd/* /etc/systemd/user/
	systemctl --user enable pygtkl_update_cache

.PHONY: build install
