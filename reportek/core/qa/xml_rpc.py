import xmlrpc.client
import logging

from reportek.core.utils import bin_to_str, get_content_encoding, log_xmlrpc_errors

log = logging.getLogger('reportek.qa')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class RemoteQA:
    """
    Proxies calls to a QA XMLRPC server.
    """
    def __init__(self, uri):
        self.uri = uri

    @log_xmlrpc_errors(log)
    def validate(self, file_url):
        """
        Validates the source XML file against the XML Schema or DOCTYPE defined within the XML file.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ValidationService.validate(file_url)

    @log_xmlrpc_errors(log)
    def validate_schema(self, file_url, xml_schema):
        """
        Validates the source XML file against the specified XML Schema.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ValidationService.validateSchema(file_url, xml_schema)

    @log_xmlrpc_errors(log)
    def analyze_xml_files(self, files):
        """
        Analyzes several XML files with QA methods.

        Args:
            files (dict): Mapping of XML schemas to lists of file URLs.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            response = proxy.XQueryService.analyzeXMLFiles(files)
            debug(f'QA analyzeXMLFiles response: {response}')
            return response or []

    @log_xmlrpc_errors(log)
    def analyze(self, file_url, xquery_script):
        """
        Analyses an XML file using the given XQuery script.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.XQueryService.analyze(file_url, xquery_script)

    @log_xmlrpc_errors(log)
    def get_job_result(self, job_id):
        """
        Returns the result of QA for given job ID.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            response = proxy.XQueryService.getResult(str(job_id))
            debug(f'QA getResult({job_id}) response: {response}')
            return response

    @log_xmlrpc_errors(log)
    def get_scripts(self, xml_schema):
        """
        Returns the list of available QA rules for one particular schema,
        as list of dicts with the keys:
            `id`
            `title`
            `last_updated`
            `max_size`
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            scripts = proxy.XQueryService.listQAScripts(xml_schema)
            scripts = scripts or []
            return [
                dict(zip(['id', 'title', 'last_updated', 'max_size'], s))
                for s in scripts
            ]

    @log_xmlrpc_errors(log)
    def get_queries(self, xml_schema):
        """
        Returns the list of available QA rules for one particular schema.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.XQueryService.listQueries(xml_schema)

    @log_xmlrpc_errors(log)
    def run_script(self, file_url, script_id):
        """
        Runs the QA script with specified id against the XML file at the URL,
        and returns the result as dict with the keys:
            `content-type`
            `result`
            `feedback_status`
            `feedback_message`
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            result = proxy.XQueryService.runQAScript(file_url, script_id)
            if result:
                encoding = get_content_encoding(result[0]) or 'utf-8'
                result = {
                    'content-type': result[0],
                    'result': bin_to_str(result[1], encoding=encoding),
                    'feedback_status': bin_to_str(result[2], encoding=encoding),
                    'feedback_message': bin_to_str(result[3], encoding=encoding)
                }
            return result
