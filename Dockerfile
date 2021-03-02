FROM python:3.7-slim-buster

ARG ADDITIONAL_PACKAGE
# Alternatively use ADD https:// (which will not be cached by Docker builder)

RUN apt-get -qy update && apt-get -qy install ${ADDITIONAL_PACKAGE}

# Add non root user
RUN addgroup --system app && adduser app --system --ingroup app
RUN chown app /home/app

USER app

ENV PATH=$PATH:/home/app/.local/bin

WORKDIR /home/app/

COPY index.py           .
COPY requirements.txt   .
USER root
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
USER app

RUN mkdir -p function
RUN touch ./function/__init__.py
WORKDIR /home/app/function/
COPY function/requirements.txt	.
RUN pip install --user -r requirements.txt

WORKDIR /home/app/

USER root
COPY function   function
RUN chown -R app:app ./
USER app

ENV MINIO_URL=localhost:9000
ENV MINIO_ACCESS_KEY=access_key
ENV MINIO_SECRET_KEY=secret_key
ENV MINIO_BUCKET=bucket
ENV DB_URL=localhost:9080

EXPOSE 8009
#HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1
CMD ["python", "index.py"]
