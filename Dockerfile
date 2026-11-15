FROM python:3.9.7-slim-buster

ENV FLYWHEEL="/flywheel/v0"
WORKDIR ${FLYWHEEL}

# install pinned dependencies first so this layer is cached across code changes
COPY requirements.txt $FLYWHEEL/
RUN pip install -r requirements.txt

# copy only what the gear needs at run time
COPY run.py manifest.json $FLYWHEEL/
COPY fw_skullstrip_normalize ${FLYWHEEL}/fw_skullstrip_normalize

# start the pipeline
RUN chmod a+x $FLYWHEEL/run.py
RUN chmod -R 777 .
ENTRYPOINT ["python","/flywheel/v0/run.py"]
