## Python Client

Install requirements:
    pip install -r requirements.txt

Setup a test client:
    Go to the admin page and create a client.
    Make sure the redirect url is set to:
        http://{YOUR_SERVER}/api/v1/oauth2/auth_code

Look at help text:

    >  python readycloud.py -h

    usage: main [-h] [-l LOGFILE] [-q] [-s] [-v] [-c CLIENT_ID] [-a API_ENDPOINT]
            [-r REDIRECT_URI] [-z SCOPE]
            {list_orders,authorize} [{plain,csv}]

    positional arguments:
      {list_orders,authorize}
                            The command to execute.
      {plain,csv}           The display format to display the data returned.

    optional arguments:
      -h, --help            show this help message and exit
      -l LOGFILE, --logfile LOGFILE
                            log to file (default: log to stdout)
      -q, --quiet           decrease the verbosity
      -s, --silent          only log warnings
      -v, --verbose         raise the verbosity
      -c CLIENT_ID, --client-id CLIENT_ID
                            The client id of the app.
      -a API_ENDPOINT, --api-endpoint API_ENDPOINT
                            The default api endpoint. Defaults to
                            https://www.readycloud.com/api/v1/
      -r REDIRECT_URI, --redirect-uri REDIRECT_URI
                            Redirect uri that the client is setup for. Default is
                            "{API_ENDPOINT}/oauth2/auth_code"
      -z SCOPE, --scope SCOPE
                            The requested scope of the app. Can be single or space
                            separated. ex "xml_backup" or "xml_backup orders"

Example Usage:
    On first run:
        python readycloud.py authorize --client-id=0e6b45f3b6c962ae39f49c514f2f4d --api-endpoint https://www.readycloud.com/api/v1/ --redirect-uri https://www.readycloud.com/api/v1/oauth2/auth_code

    Follow the instructions and then after you are authorized:
        python readycloud.py list_orders csv -a https://www.readycloud.com/api/v1/

