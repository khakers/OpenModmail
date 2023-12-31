FROM python:3.11-alpine as base

RUN apk update && apk add git \
	# pillow dependencies
	jpeg-dev zlib-dev

FROM base as python-deps

RUN apk add --virtual build-deps build-base gcc libffi-dev

#Install pdm
RUN pip install -U pip setuptools wheel
RUN pip install pdm

COPY  pyproject.toml pdm.lock README.md /modmail/

WORKDIR /modmail
RUN pdm sync --prod --no-editable --fail-fast

FROM base as runtime

RUN adduser --disabled-password modmail
USER modmail


ENV USING_DOCKER yes
COPY --chown=modmail:modmail --from=python-deps /modmail /modmail

COPY --chown=modmail:modmail . /modmail
WORKDIR /modmail

ENV PATH="/modmail/.venv/bin:${PATH}"
CMD ["python", "bot.py"]

