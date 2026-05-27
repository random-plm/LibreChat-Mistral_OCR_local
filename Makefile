GHCR_USER ?= random-plm
IMAGE_NAME ?= ghcr.io/${GHCR_USER}/librechat-ocr
IMAGE_TAG ?= latest
IMAGE ?= $(IMAGE_NAME):$(IMAGE_TAG)
PLATFORMS ?= linux/amd64


.PHONY: login build publish

login:
	cat .pat | docker login ghcr.io -u $(GHCR_USER) --password-stdin

build:
	docker buildx build --platform $(PLATFORMS) --load -t $(IMAGE) .

publish:
	docker buildx build --platform $(PLATFORMS) --push -t $(IMAGE) .
