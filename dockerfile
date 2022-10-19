# FROM python:latest
#
# WORKDIR /fastapi_container
#
# #COPY ./ /fastapi_container/
# COPY main.py poetry.lock pyproject.toml /fastapi_container
#
# RUN pip install poetry
# RUN poetry config virtualenvs.create false && poetry install --no-root
#
# RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3001"]

FROM python:latest

WORKDIR /container_test

COPY main.py poetry.lock pyproject.toml ./test/test.py /container_test


RUN pip install poetry
RUN poetry config virtualenvs.create false && poetry install --no-root

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes --with dev
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9000"]
CMD ["pytest", "test.py"]

