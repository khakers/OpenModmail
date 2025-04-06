ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-alpine AS base

RUN apk update && apk add git \
	# pillow dependencies
	jpeg-dev zlib-dev

FROM base AS python-deps

RUN apk add --virtual build-deps build-base gcc libffi-dev

#Install pdm
RUN pip install -U pip setuptools wheel
RUN pip install pdm

FROM python-deps AS builder

COPY  pyproject.toml pdm.lock README.md /modmail/

WORKDIR /modmail

RUN pdm install --check --prod --no-editable --fail-fast;

ARG INCLUDE_SUPPORTUTILS=false

RUN if [ "$INCLUDE_SUPPORTUTILS" = "true" ]; then \
        pdm install --prod -G supportutils --no-editable --fail-fast; \
    fi

FROM base AS runtime

RUN adduser --disabled-password modmail
USER modmail


ENV USING_DOCKER yes
COPY --chown=modmail:modmail --from=builder /modmail /modmail

COPY --chown=modmail:modmail . /modmail
WORKDIR /modmail

ENV PATH="/modmail/.venv/bin:${PATH}"
CMD ["python", "bot.py"]

