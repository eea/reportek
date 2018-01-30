import logging
import enum
from django.db import models
from django.utils import timezone

from reportek.core.qa import RemoteQA


log = logging.getLogger('reportek.qa')
info = log.info
debug = log.debug
warn = log.warning
error = log.error

__all__ = ['QAJob', 'QAJobResult']


class QAJob(models.Model):
    """
    A QA validation job for an ``EnvelopeFile``.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    envelope_file = models.ForeignKey(
        'core.EnvelopeFile',
        on_delete=models.CASCADE,
        related_name='qa_jobs'
    )
    qa_job_id = models.IntegerField()
    qa_script_id = models.CharField(max_length=20, blank=True, null=True)
    qa_script_name = models.CharField(max_length=200, blank=True, null=True)
    completed = models.BooleanField(default=False)
    refreshing = models.BooleanField(default=False)

    class Meta:
        db_table = 'core_qa_job'
        unique_together = ('envelope_file', 'qa_job_id')

    def add_or_update_result(self, rpc_result):
        """
        If ``rpc_result`` has different field values from the latest result,
        a new ``QAJobResult`` is created. Otherwise, only the update timestamp
        on the latest result is updated.

        Args:
            rpc_result (dict): Structured response a from QA/XMLCONV validation job.

        Returns:
            The updated or newly created ``QAJobResult`` instance.
        """
        job_not_found_err = '*** No such job or the job result has been already downloaded. ***'
        if rpc_result is None or rpc_result.get('VALUE') == job_not_found_err:
            return

        prev_result = self.latest_result
        if prev_result is not None and prev_result.same_as(**rpc_result):
            prev_result.updated_at = timezone.now()
            prev_result.save()
            result = prev_result
        else:
            result = QAJobResult.objects.create(
                job=self,
                code=rpc_result['CODE'],
                value=rpc_result['VALUE'],
                metatype=rpc_result['METATYPE'],
                script_title=rpc_result['SCRIPT_TITLE'],
                feedback_status=rpc_result['FEEDBACK_STATUS'],
                feedback_message=rpc_result['FEEDBACK_MESSAGE']
            )
            if not result.processing:
                self.completed = True
                self.save()
        return result

    def refresh(self, cleanup=True):
        """
        Fetches the job result from the remote QA system.
        Returns: id of created/updated QAJobResult, or `None` RPC .
        """
        if not self.refreshing and not self.completed:
            self.refreshing = True
            self.save()

            remote_qa = RemoteQA(
                self.envelope_file.envelope.obligation_spec.qa_xmlrpc_uri
            )
            rpc_result = remote_qa.get_job_result(self.qa_job_id)
            result = self.add_or_update_result(rpc_result)
            if cleanup and result is not None:
                self.cleanup_results()

            self.refreshing = False
            self.save()
            return result.id if result is not None else None

    @property
    def latest_result(self):
        """
        Returns the most recent result, or `None`.
        """
        try:
            return self.results.latest()
        except QAJobResult.DoesNotExist:
            return None

    def cleanup_results(self):
        """
        Removes all but the latest result.
        """
        latest = self.latest_result
        if latest is not None:
            QAJobResult.objects.\
                filter(job=latest.job).\
                exclude(pk=latest.pk).\
                delete()


class QAJobResult(models.Model):
    """
    Result of a ``QAJob``, fetched from the QA/XMLCONV system over RPC.
    """
    @enum.unique
    class CODES(enum.IntEnum):
        READY = 0
        NOT_READY = 1
        FATAL_ERROR = 2
        LIGHT_ERROR = 3

    @enum.unique
    class FEEDBACK_STATUSES(enum.Enum):
        BLOCKER = 'BLOCKER'
        ERROR = 'ERROR'
        WARNING = 'WARNING'
        INFO = 'INFO'
        UNKNOWN = 'UNKNOWN'

    OK_STATUSES = (
        FEEDBACK_STATUSES.INFO,
        FEEDBACK_STATUSES.WARNING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    job = models.ForeignKey(QAJob, on_delete=models.CASCADE, related_name='results')
    code = models.IntegerField(choices=((c.value, c.name) for c in CODES))
    value = models.TextField(blank=True, null=True)
    metatype = models.CharField(max_length=60, blank=True, null=True)
    script_title = models.CharField(max_length=100)
    feedback_status = models.CharField(max_length=40, choices=((s.value, s.name) for s in FEEDBACK_STATUSES))
    feedback_message = models.CharField(max_length=200, blank=True, null=True)

    @property
    def processing(self):
        """
        The QA query service specification only gives this criterion
        as indicating that the job is still processing.
        """
        # XMLCONV docs incorrectly state that the value is empty when still processing.
        # Instead, value is '*** Not ready ***' for jobs in process.
        return self.value == 1

    @property
    def ok(self):
        return self.feedback_status in self.OK_STATUSES

    class Meta:
        db_table = 'core_qa_job_result'
        get_latest_by = 'updated_at'

    def same_as(self, **kwargs):
        return self.code == kwargs.get('CODE') and \
            self.value == kwargs.get('VALUE') and \
            self.metatype == kwargs.get('METATYPE') and \
            self.script_title == kwargs.get('SCRIPT_TITLE') and \
            self.feedback_status == kwargs.get('FEEDBACK_STATUS') and \
            self.feedback_message == kwargs.get('FEEDBACK_MESSAGE')
