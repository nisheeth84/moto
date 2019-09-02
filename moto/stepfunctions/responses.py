from __future__ import unicode_literals

import json

from moto.core.responses import BaseResponse
from moto.core.utils import amzn_request_id
from .exceptions import AWSError
from .models import stepfunction_backends


class StepFunctionResponse(BaseResponse):

    @property
    def stepfunction_backend(self):
        return stepfunction_backends[self.region]

    @amzn_request_id
    def create_state_machine(self):
        name = self._get_param('name')
        definition = self._get_param('definition')
        roleArn = self._get_param('roleArn')
        tags = self._get_param('tags')
        try:
            state_machine = self.stepfunction_backend.create_state_machine(name=name, definition=definition,
                                                                           roleArn=roleArn,
                                                                           tags=tags)
            response = {
                'creationDate': state_machine.creation_date,
                'stateMachineArn': state_machine.arn
            }
            return 200, {}, json.dumps(response)
        except AWSError as err:
            return err.response()

    @amzn_request_id
    def list_state_machines(self):
        list_all = self.stepfunction_backend.list_state_machines()
        list_all = sorted([{'creationDate': sm.creation_date,
                            'name': sm.name,
                            'stateMachineArn': sm.arn} for sm in list_all],
                          key=lambda x: x['name'])
        response = {'stateMachines': list_all}
        return 200, {}, json.dumps(response)

    @amzn_request_id
    def describe_state_machine(self):
        arn = self._get_param('stateMachineArn')
        try:
            state_machine = self.stepfunction_backend.describe_state_machine(arn)
            response = {
                'creationDate': state_machine.creation_date,
                'stateMachineArn': state_machine.arn,
                'definition': state_machine.definition,
                'name': state_machine.name,
                'roleArn': state_machine.roleArn,
                'status': 'ACTIVE'
            }
            return 200, {}, json.dumps(response)
        except AWSError as err:
            return err.response()

    @amzn_request_id
    def delete_state_machine(self):
        arn = self._get_param('stateMachineArn')
        try:
            self.stepfunction_backend.delete_state_machine(arn)
            return 200, {}, json.dumps('{}')
        except AWSError as err:
            return err.response()

    @amzn_request_id
    def list_tags_for_resource(self):
        arn = self._get_param('resourceArn')
        try:
            state_machine = self.stepfunction_backend.describe_state_machine(arn)
            tags = state_machine.tags or []
        except AWSError:
            tags = []
        response = {'tags': tags}
        return 200, {}, json.dumps(response)
