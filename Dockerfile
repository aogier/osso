ARG PYTHON_BASE_IMAGE_BUILD=3.7-alpine
ARG PYTHON_BASE_IMAGE=3.7-slim
FROM python:${PYTHON_BASE_IMAGE_BUILD} as build

RUN apk add curl \
    && curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3

COPY poetry.lock pyproject.toml ./

RUN . $HOME/.poetry/env \
    && poetry export -f requirements.txt > /tmp/requirements.txt

FROM python:${PYTHON_BASE_IMAGE}

ARG POETRY_VERSION=1.0.0

COPY --from=build /tmp/requirements.txt /srv

WORKDIR /srv

RUN pip install -r requirements.txt

COPY . /srv

ENTRYPOINT ["uvicorn", "osso.app:app", "--host", "0", "--proxy-headers"]
