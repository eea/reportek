import logging
from collections import defaultdict
from celery import group, chord

from reportek.site.celery import app

import reportek.core.models  # avoid circular import errors

from reportek.core.qa import RemoteQA
from reportek.core.utils import fully_qualify_url

log = logging.getLogger('reportek.tasks')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


@app.task(ignore_result=True)
def submit_xml_to_qa(envelope_pk):
    """
    Sends an envelope's XML files to remote QA, for batch analysis.
    """

    envelope = reportek.core.models.Envelope.objects.get(pk=envelope_pk)
    remote_qa = RemoteQA(
        envelope.obligation_spec.qa_xmlrpc_uri
    )

    params = defaultdict(list)
    urls_to_files = {}
    for file in envelope.envelopefiles.all():
        if file.xml_schema is not None:  # only consider XML files
            file.qa_jobs.all().delete()  # delete existing jobs and results
            xml_schema = file.xml_schema.split(' ')[0]  # use the first schema listed in file
            file_url = file.fq_download_url
            params[xml_schema].append(file_url)
            urls_to_files[file_url] = file.pk

    params = dict(params)  # XMLRPC cannot marshall defaultdicts
    if params:
        jobs = remote_qa.analyze_xml_files(params) or []
        for job_id, file_url, script_id, script_name in jobs:
            try:
                file = reportek.core.models.EnvelopeFile.objects.get(pk=urls_to_files.get(file_url))
                qa_job = reportek.core.models.QAJob.objects.create(
                        envelope_file=file,
                        qa_job_id=job_id,
                        qa_script_id=script_id,
                        qa_script_name=script_name
                )
            except reportek.core.models.EnvelopeFile.DoesNotExist:
                continue
    else:
        jobs = []

    return jobs


@app.task(ignore_result=False)
def get_qa_result(job_id):
    """
    Gets the result of a QA job.
    The corresponding `QAJobResult` will be created or updated.
    Returns:
        A tuple of the envelope id and `QAJobResult` id,
        or (None, None) if the job does not exist.
    """
    qa_job = reportek.core.models.QAJob.objects.get(pk=job_id)
    if qa_job is None:
        return None, None
    return qa_job.envelope_file.envelope_id, qa_job.refresh()


@app.task(ignore_result=True)
def get_qa_results():
    """
    Scheduled task to fetch results for all QAJobs not yet completed
    or currently refreshing.
    Spawns a group of subtasks, one per job.
    """
    qa_jobs = reportek.core.models.QAJob.objects.filter(
        completed=False, refreshing=False
    ).all()
    results = chord(
        (get_qa_result.s(job.id) for job in qa_jobs),
        process_qa_results.s()
    )()
    return results.get()


@app.task(ignore_result=False)
def process_qa_results(results):
    """
    Processes the results of QA jobs. Spawns group of subtasks that run
    the QA results handler for each affected envelope.
    """
    envelope_ids = {
        r[0] for r in results
        if r[0] is not None and r[1] is not None
    }
    res = group(
        process_envelope_qa_results.s(env_id)
        for env_id in envelope_ids
    )()
    return res.get()


@app.task(ignore_result=False)
def process_envelope_qa_results(envelope_id):
    env = reportek.core.models.Envelope.objects.get(pk=envelope_id)
    env.workflow.handle_auto_qa_results()
    return envelope_id

