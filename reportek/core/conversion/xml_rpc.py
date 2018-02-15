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

    @log_xmlrpc_errors(log)
    def convert_spreadsheet_to_xml(self, spreadsheet_url):
        """
        Converts the source MS Excel or OpenDocument Spreadsheet file into XML format
        (Schema specified in Data Dictionary).

        This method always returns 1 XML file.

        :param spreadsheet_url: url of the source MS Excel or ODS file
        :return: dictionary with the following structure:
            {'resultCode': '0',
             'conversionLog': '<div class="feedback"><h2>Conversion log ...',
             'resultDescription': 'Conversion successful.',
             'convertedFiles': [{'content': <xmlrpc.client.Binary object at 0x0472D770>,
                                 'fileName': 'SE_Rivers_Revised_SoE2008.xml'}]
            }

        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertDD_XML(spreadsheet_url)

    @log_xmlrpc_errors(log)
    def convert_spreadsheet_to_split_xml(self, spreadsheet_url, sheet_name=''):
        """
        Converts the source MS Excel or OpenDocument Spreadsheet file sheets
        into XML format (Schema specified in Data Dictionary),
        where each sheet is in different xml file.

        :param spreadsheet_url: url of the source MS Excel or ODS file
        :param sheet: the name of the sheet, if only one sheet is required to convert.
            Provide the empty string for converting all sheets.
        :return: dictionary with the following structure:
            {'resultCode': '0',
             'conversionLog': '<div class="feedback"><h2>Conversion log ...',
             'resultDescription': 'Conversion successful.',
             'convertedFiles': [{'content': <xmlrpc.client.Binary object at 0x0472D770>, 'fileName': 'Stations.xml'},
                                {'content': <xmlrpc.client.Binary object at 0x0472D880>, 'fileName': 'Nutrients.xml'}]
            }

        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertDD_XML_split(spreadsheet_url, sheet_name)

    @log_xmlrpc_errors(log)
    def convert_local_excel_to_xml(self, file_contents, file_name):
        """
        Converts the source MS Excel Spreadsheet file into XML files.
        MS Excel file should have sheet DO_NOT_DELETE_THIS_SHEET,
        where the Schema URL (implied row 4 first cell) and release version are specified
        (implied row 5 first cell).
        The method functionality originally is implied for conversion Air Quality Excel reports to XML.

        :param file_contents: Base64-encoded string representing excel file contents
        :param file_name: string
        :return: list of strings, first two elements are status code and description,
            next elements are pairs of file name and file contents, like this:
            ['0', 'OK.', '1.xml', '<?xml.....', '2.xml', '<?xml.....']

            In case of error the result array has always 2 elements: status code and status description.

        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertExcelToXMLPush(file_contents, file_name)

    @log_xmlrpc_errors(log)
    def convert_excel_to_xml(self, file_url):
        """
        Converts the source MS Excel file to number of XML files.
        MS Excel file should have sheet DO_NOT_DELETE_THIS_SHEET,
        where the Schema URL (implied row 4 first cell) and release version are specified
        (implied row 5 first cell).
        The method functionality originally is implied for conversion Air Quality Excel reports to XML.

        :param file_url:
        :return: list of strings, first two elements are status code and description,
            next elements are pairs of file name and file contents, like this:
            ['0', 'OK.', '1.xml', '<?xml.....', '2.xml', '<?xml.....']

            In case of error the result array has always 2 elements: status code and status description.

        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertExcelToXML(file_url)

    @log_xmlrpc_errors(log)
    def convert_json_to_xml(self, file_url):
        """
        Converts the JSON format data into XML format.

        :param file_url: RESTful URL to the webservice that returns JSON or the result in JSON format.
        :return: JSON representation in XML format where root element is called “root”
            and list item elements are called “element”.
            Other element names are inherited from JSON parameter names.
        """
        with xmlrpc.client.ServerProxy(self.uri) as proxy:
            return proxy.ConversionService.convertJson2Xml(file_url)
