FROM python:3.9.7-slim-buster

ENV FLYWHEEL="/flywheel/v0"
WORKDIR ${FLYWHEEL}

# install main dependenices
RUN pip install flywheel_gear_toolkit
RUN pip install fw_core_client
RUN pip install flywheel-sdk


# copy main files into working directory
COPY run.py manifest.json requirements.txt $FLYWHEEL/
COPY fw_skullstrip_normalize ${FLYWHEEL}/fw_skullstrip_normalize 
COPY ./ $FLYWHEEL/

RUN pip install -r requirements.txt

# start the pipeline
RUN chmod a+x $FLYWHEEL/run.py
RUN chmod -R 777 .
ENTRYPOINT ["python","/flywheel/v0/run.py"]
