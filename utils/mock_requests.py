# Mock requests module for simple use cases
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
import logging

logger = logging.getLogger(__name__)
logger.info("Using mock requests module")

class Response:
    def __init__(self, status_code, headers, content):
        self.status_code = status_code
        self.headers = headers
        self._content = content
        
    def json(self):
        return json.loads(self._content.decode('utf-8'))
        
    @property
    def text(self):
        return self._content.decode('utf-8')
        
    @property
    def content(self):
        return self._content
        
    @property
    def ok(self):
        return 200 <= self.status_code < 300

def get(url, headers=None, params=None, timeout=None, verify=True):
    try:
        logger.info(f"Mock GET request to {url}")
        
        # Build URL with params
        if params:
            url_parts = list(urllib.parse.urlparse(url))
            query = dict(urllib.parse.parse_qsl(url_parts[4]))
            query.update(params)
            url_parts[4] = urllib.parse.urlencode(query)
            url = urllib.parse.urlunparse(url_parts)
        
        # Create request
        req = urllib.request.Request(url)
        
        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # Handle SSL verification
        context = None
        if not verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Make request
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            return Response(
                response.status,
                dict(response.getheaders()),
                response.read()
            )
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.reason}")
        return Response(
            e.code,
            dict(e.headers),
            e.read()
        )
    except Exception as e:
        logger.error(f"Error in GET request: {str(e)}")
        raise

def post(url, data=None, json=None, headers=None, timeout=None, verify=True):
    try:
        logger.info(f"Mock POST request to {url}")
        
        # Create request
        req = urllib.request.Request(url, method='POST')
        
        # Add headers
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        
        # Add data or JSON payload
        body = None
        if json is not None:
            req.add_header('Content-Type', 'application/json')
            body = json.dumps(json).encode('utf-8')
        elif data is not None:
            if isinstance(data, dict):
                body = urllib.parse.urlencode(data).encode('utf-8')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            else:
                body = data
        
        # Handle SSL verification
        context = None
        if not verify:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        # Make request
        with urllib.request.urlopen(req, data=body, timeout=timeout, context=context) as response:
            return Response(
                response.status,
                dict(response.getheaders()),
                response.read()
            )
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP Error: {e.code} - {e.reason}")
        return Response(
            e.code,
            dict(e.headers),
            e.read()
        )
    except Exception as e:
        logger.error(f"Error in POST request: {str(e)}")
        raise