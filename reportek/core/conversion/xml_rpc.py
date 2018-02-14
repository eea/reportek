import xmlrpc.client
import logging

from reportek.core.utils import log_xmlrpc_errors

log = logging.getLogger('reportek.conversions')
info = log.info
debug = log.debug
warn = log.warning
error = log.error


class RemoteConversion:
    """
    Proxies calls to a conversions XMLRPC server.
    """
    def __init__(self, uri):
        self.uri = uri

    @log_xmlrpc_errors(log)
    def get_available_xml_schemas(self):
        """
        Returns the distinct list of XML Schemas that have conversions available.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.getXMLSchemas()

    @log_xmlrpc_errors(log)
    def get_conversions(self, xml_schema_url):
        """
        Returns the list of available conversions for delivered XML file.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            # list of dictionaries; 'convert_id' should be used to call the
            # convert or convertPush methods
            return proxy.ConversionService.listConversions(xml_schema_url)

    @log_xmlrpc_errors(log)
    def convert_local_xml(self, local_file_path, convert_id, result_file_name):
        """
        Converts the local XML file (can be zipped xml) into specified format.
        Returns {content-type:'text/html;charset=UTF-8', filename:'ResultFile.html', content:<bytearray> }
        """
        with open(local_file_path, 'rb') as f:
            contents = f.read()

        # file parameter value encoded as Base64 byte array
        contents = xmlrpc.client.Binary(contents)
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertPush(contents, convert_id, result_file_name)
        # To Be Implemented
        # if result:
        #     encoding = utils.get_content_encoding(result[0]) or 'utf-8'

    @log_xmlrpc_errors(log)
    def convert_xml(self, xml_url, convert_id):
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convert(xml_url, convert_id)
