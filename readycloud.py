import os, sys, json, unicodecsv
import requests
from urllib import urlencode
from cli.log import LoggingApp
from collections import OrderedDict

API_ENDPOINT = u'https://www.readycloud.com/api/v1/'

class Struct(object):

    def __init__(self, dict_order=None, **entries):
        self.dict_order = dict_order if dict_order is not None else entries.keys()
        if set(self.dict_order) > set(entries.keys()):
            raise Exception(u'Headers do not match dictionary values.')
        self.__dict__.update(entries)

    def keys(self):
        return self.dict_order

    def values(self):
        vals = []
        for o in self.dict_order:
            vals.append(self.__dict__[o])
        return vals

    def items(self):
        items = []
        for o in self.dict_order:
            items.append((o, self.__dict__[o]))
        return items

    def to_string(self):
        return u'\n '.join(u'{}: {}'.format(k, str(v)) for (k, v) in self.items())

    def name(self):
        if u'id' in self.__dict__:
            return u'{}: {}'.format(self.__class__.__name__, self.__dict__[u'id'])
        else:
            return u'{}:'.format(self.__class__.__name__)


class RCClient(object):
    refresh_token_storage = u'refresh_token.txt'

    def __init__(self, access_token, api_endpoint, log):
        self.log = log
        self.api_endpoint = api_endpoint
        self.resource_url_template = '{}{}/'
        self.access_token = access_token
        self.client = requests.session()

    def get_api_result(self, url):
        """Gets a json response from the api and
        converts it into a dict for use in the client.
        """
        data = dict(bearer_token=self.access_token,
                    format=u'json')
        response = self.client.get(u'{0}?{1}'.format(url, urlencode(data)))
        try:
            return json.loads(response.content)
        except ValueError:
            self.log.error(u"No data obtained. It may be that this application's access "
                           u"to the api has been revoked.")
            return {}

    def get_resource(self, name, label, field='objects', dict_order=None):
        """Gets a list of resources from the api server."""
        url = self.resource_url_template.format(self.api_endpoint, name)
        result = self.get_api_result(url)
        if not self.check_result(result):
            return []
        new_res = []
        if field in result:
            for obj in result[field]:
                new_res.append(type(label, (Struct,), {})(dict_order=dict_order, **obj))
        return new_res

    def check_result(self, result):
        if 'error_message' in result:
            self.log.error(u'Error: {} {}'.format(result['error_message'],
                                                  u'Your access token may be revoked or invalid.'))
            return False
        return True


    def get_orders(self, dict_order=None):
        """Gets all orders from the api server."""
        return self.get_resource('order', 'Order', dict_order=dict_order)


class RCCLI(LoggingApp):
    # Replace localhost:8000 here with the readycloud server
    token_file = u'access_token.txt'
    commands = ['list_orders', 'authorize']

    def main(self):

        self.api_endpoint = self.params.api_endpoint

        if not self.api_endpoint.endswith('/'):
            self.api_endpoint += '/'

        self.redirect_uri = self.params.redirect_uri or\
                            u'{}oauth2/auth_code'.format(self.api_endpoint)

        self.auth_url = u'{}oauth2/authorize'.format(self.api_endpoint)

        if self.params.command == 'authorize':
            self.authorize()
            return
        else:
            self.read_access_token()

        self.client = RCClient(self.access_token, self.api_endpoint, self.log)

        if hasattr(self, self.params.command):
            command_call = getattr(self, self.params.command)
            command_call()

    def list_orders(self):
        order_headers = ['id', 'primary_id', 'numerical_id', 'alias_id',
                         'po_number', 'customer_number', 'source',
                         'tax', 'tax_source', 'imported_tax',
                         'calculated_tax', 'shipping', 'shipping_source',
                         'imported_shipping', 'calculated_shipping', 'actual_shipcost',
                         'status_shipped', 'ship_type', 'ship_via', 'ship_time', 'future_ship_time',
                         'total', 'total_source', 'imported_total', 'calculated_total',
                         'base_price', 'base_price_source', 'imported_base_price',
                         'calculated_base_price', 'message', 'terms', 'resource_uri',
                         'created_at', 'updated_at', 'print_time', 'order_time',
                         'import_time']

        self.print_data(self.client.get_orders(order_headers),
                        self.params.display_format)

    def print_data(self, data, format):
        self.display_formats[format](data)

    def print_plain(self, data):
        for item in data:
            print(u'{}\n {}\n'.format(item.name(), item.to_string()))

    def print_csv(self, data):
        w = unicodecsv.writer(sys.stdout, encoding='utf-8')
        self.write_headers(data, w)
        for item in data:
            w.writerow(item.values())

    def write_headers(self, data, writer):
        if data:
            writer.writerow(data[0].keys())

    def setup(self):
        LoggingApp.setup(self)
        self.display_formats = {'csv':   self.print_csv,
                                'plain': self.print_plain}

        self.add_param('-c', '--client-id', default=None, dest='client_id',
                       help='The client id of the app.')
        self.add_param('-a', '--api-endpoint', default=API_ENDPOINT, dest='api_endpoint',
                       help='The default api endpoint. Defaults to https://www.readycloud.com/api/v1/')
        self.add_param('-r', '--redirect-uri', default=None, dest='redirect_uri',
                       help='Redirect uri that the client is setup for. Default is "{API_ENDPOINT}/oauth2/auth_code"')
        self.add_param('-z', '--scope', default='order', dest='scope',
                       help=('The requested scope of the app. Can be single or space separated. '
                             'ex "xml_backup" or "xml_backup orders"'))
        self.add_param('command', choices=self.commands,
                       help='The command to execute.')
        self.add_param('display_format', default='plain', nargs='?',
                       choices=self.display_formats.keys(),
                       help='The display format to display the data returned.')

    def needs_authorization(self):
        return not os.path.exists(self.token_file)

    def authorize(self):

        if not self.params.client_id:
            self.log.error('You must enter a client id in order to authorize.\n')
            self.argparser.print_help()
            sys.exit()

        if not self.needs_authorization():
            print('You seem to have an access code already.')
            ans = raw_input('Would you like to get another one? (Y/n) ')
            if ans != 'Y' and ans != 'y':
                print('Exiting.')
                sys.exit()

        data = {'redirect_uri': self.redirect_uri,
                'client_id': self.params.client_id,
                'response_type': 'token'}

        if self.params.scope:
            data['scope'] = self.params.scope

        print(u'\nTo authenticate with ReadyCloud and grant {} access to your account,\n'
                      u'follow this link in a web browser:'.format(__file__))

        url = u'{}?{}'.format(self.auth_url, urlencode(data))

        print(u'\n\t' + url)

        print('\nAfter authorizing, please paste the code displayed on the page here.')

        self.access_token = raw_input('Enter code: ')

        self.save_access_token()

    def save_access_token(self):
        if self.access_token:
            with open(self.token_file, 'w+') as f:
                f.write(u'{}\n{}'.format(self.access_token, self.api_endpoint))

    def read_access_token(self):
        if os.path.exists(self.token_file):
            with open(self.token_file) as f:
                self.access_token = f.readline().strip()
                self.api_endpoint = f.readline().strip()
        else:
            self.log.error(u'You must first call "{} authorize --client-id=YOUR_CLIENT_ID" '
                           u'in order to get an access code.'.format(__file__))
            sys.exit()


if __name__ == '__main__':
    ls = RCCLI()
    ls.run()
