from __future__ import unicode_literals

import json
import re

from moto.core.responses import BaseResponse
from .models import lambda_backends


class LambdaResponse(BaseResponse):
    
    @classmethod
    def root(cls, request, full_url, headers):
        if request.method == 'GET':
            return cls()._list_functions(request, full_url, headers)
        elif request.method == 'POST':
            return cls()._create_function(request, full_url, headers)
        else:
            raise ValueError("Cannot handle request")

    @classmethod
    def function(cls, request, full_url, headers):
        if request.method == 'GET':
            return cls()._get_function(request, full_url, headers)
        elif request.method == 'DELETE':
            return cls()._delete_function(request, full_url, headers)
        else:
            raise ValueError("Cannot handle request")

    def _list_functions(self, request, full_url, headers):
        lambda_backend = self.get_lambda_backend(full_url)
        return 200, headers, json.dumps({
            "Functions": [fn.get_configuration() for fn in lambda_backend.list_functions()],
            "NextMarker": "aws-lambda-next-marker",
        })

    def _create_function(self, request, full_url, headers):
        lambda_backend = self.get_lambda_backend(full_url)

        spec = json.loads(request.body)
        fn = lambda_backend.create_function(spec)
        config = fn.get_configuration()
        return 200, headers, json.dumps(config)

    def _delete_function(self, request, full_url, headers):
        lambda_backend = self.get_lambda_backend(full_url)

        function_name = request.path.split('/')[-1]

        if lambda_backend.has_function(function_name):
            lambda_backend.delete_function(function_name)
            return 204, headers, ""
        else:
            return 404, headers, "{}"

    def _get_function(self, request, full_url, headers):
        lambda_backend = self.get_lambda_backend(full_url)

        function_name = request.path.split('/')[-1]

        if lambda_backend.has_function(function_name):
            fn = lambda_backend.get_function(function_name)
            code = fn.get_code()
            return 200, headers, json.dumps(code)
        else:
            return 404, headers, "{}"
    
    def get_lambda_backend(self, full_url):
        from moto.awslambda.models import lambda_backends
        region = self._get_aws_region(full_url)
        return lambda_backends[region]

    def _get_aws_region(self, full_url):
        region = re.search(self.region_regex, full_url)
        if region:
            return region.group(1)
        else:
            return self.default_region
