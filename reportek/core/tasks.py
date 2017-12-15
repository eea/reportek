import logging
from collections import defaultdict
from reportek.site.celery import app

from reportek.core.models import (
    Envelope,
    EnvelopeFile,
    QAJob,
)

from reportek.core.qa import RemoteQA
from reportek.core.utils import fully_qualify_url

log = logging.getLogger('reportek.tasks')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


@app.task(ignore_result=True)
def submit_xml_to_qa(envelope_pk, resubmit=False):
    """
    Sends an envelope's XML files to remote QA, for batch analysis.
    """

    envelope = Envelope.objects.get(pk=envelope_pk)
    remote_qa = RemoteQA(
        envelope.obligation_group.qa_xmlrpc_uri
    )

    params = defaultdict(list)
    urls_to_files = {}
    for file in envelope.files.all():
        if file.xml_schema is not None:  # only consider XML files
            if not file.qa_jobs.exists() or resubmit:  # only resubmit if forced
                file_url = fully_qualify_url(file.get_api_download_url())
                params[file.xml_schema].append(file_url)
                urls_to_files[file_url] = file.pk

    params = dict(params)  # XMLRPC cannot marshall defaultdicts
    if params:
        jobs = remote_qa.analyze_files(params) or []
        for job_id, file_url, script_id, script_name in jobs:
            try:
                file = EnvelopeFile.objects.get(pk=urls_to_files.get(file_url))
                qa_job = QAJob.objects.create(
                        envelope_file=file,
                        qa_job_id=job_id,
                        qa_script_id=script_id,
                        qa_script_name=script_name
                )
            except EnvelopeFile.DoesNotExist:
                continue


@app.task(ignore_result=True)
def fetch_qa_results():
    """
    Scheduled task to get QA job results.
    Spawns a fetch task for each job.
    """
    qa_jobs = QAJob.objects.filter(completed=False, refreshing=False)
    for qa_job in qa_jobs:
        fetch_qa_result.delay(qa_job.pk)


@app.task(ignore_result=True)
def fetch_qa_result(job_id):
    """
    Gets (refreshes) the result of a QA job.
    """
    qa_job = QAJob.objects.get(pk=job_id)
    qa_job.refresh()
