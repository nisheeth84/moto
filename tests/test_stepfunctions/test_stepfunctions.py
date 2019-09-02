from __future__ import unicode_literals

import boto3
import sure   # noqa
import datetime

from datetime import datetime
from botocore.exceptions import ClientError
from moto.config.models import DEFAULT_ACCOUNT_ID
from nose.tools import assert_raises

from moto import mock_sts, mock_stepfunctions


region = 'us-east-1'
simple_definition = '{"Comment": "An example of the Amazon States Language using a choice state.",' \
                    '"StartAt": "DefaultState",' \
                    '"States": ' \
                    '{"DefaultState": {"Type": "Fail","Error": "DefaultStateError","Cause": "No Matches!"}}}'
default_stepfunction_role = 'arn:aws:iam:' + str(DEFAULT_ACCOUNT_ID) + ':role/unknown_sf_role'


@mock_stepfunctions
@mock_sts
def test_state_machine_creation_succeeds():
    client = boto3.client('stepfunctions', region_name=region)
    name = 'example_step_function'
    #
    response = client.create_state_machine(name=name,
                                           definition=str(simple_definition),
                                           roleArn=default_stepfunction_role)
    #
    response['ResponseMetadata']['HTTPStatusCode'].should.equal(200)
    response['creationDate'].should.be.a(datetime)
    response['stateMachineArn'].should.equal('arn:aws:states:' + region + ':123456789012:stateMachine:' + name)


@mock_stepfunctions
def test_state_machine_creation_fails_with_invalid_names():
    client = boto3.client('stepfunctions', region_name=region)
    invalid_names = [
        'with space',
        'with<bracket', 'with>bracket', 'with{bracket', 'with}bracket', 'with[bracket', 'with]bracket',
        'with?wildcard', 'with*wildcard',
        'special"char', 'special#char', 'special%char', 'special\\char', 'special^char', 'special|char',
        'special~char', 'special`char', 'special$char', 'special&char', 'special,char', 'special;char',
        'special:char', 'special/char',
        u'uni\u0000code', u'uni\u0001code', u'uni\u0002code', u'uni\u0003code', u'uni\u0004code',
        u'uni\u0005code', u'uni\u0006code', u'uni\u0007code', u'uni\u0008code', u'uni\u0009code',
        u'uni\u000Acode', u'uni\u000Bcode', u'uni\u000Ccode',
        u'uni\u000Dcode', u'uni\u000Ecode', u'uni\u000Fcode',
        u'uni\u0010code', u'uni\u0011code', u'uni\u0012code', u'uni\u0013code', u'uni\u0014code',
        u'uni\u0015code', u'uni\u0016code', u'uni\u0017code', u'uni\u0018code', u'uni\u0019code',
        u'uni\u001Acode', u'uni\u001Bcode', u'uni\u001Ccode',
        u'uni\u001Dcode', u'uni\u001Ecode', u'uni\u001Fcode',
        u'uni\u007Fcode',
        u'uni\u0080code', u'uni\u0081code', u'uni\u0082code', u'uni\u0083code', u'uni\u0084code',
        u'uni\u0085code', u'uni\u0086code', u'uni\u0087code', u'uni\u0088code', u'uni\u0089code',
        u'uni\u008Acode', u'uni\u008Bcode', u'uni\u008Ccode',
        u'uni\u008Dcode', u'uni\u008Ecode', u'uni\u008Fcode',
        u'uni\u0090code', u'uni\u0091code', u'uni\u0092code', u'uni\u0093code', u'uni\u0094code',
        u'uni\u0095code', u'uni\u0096code', u'uni\u0097code', u'uni\u0098code', u'uni\u0099code',
        u'uni\u009Acode', u'uni\u009Bcode', u'uni\u009Ccode',
        u'uni\u009Dcode', u'uni\u009Ecode', u'uni\u009Fcode']
    #

    for invalid_name in invalid_names:
        with assert_raises(ClientError) as exc:
            client.create_state_machine(name=invalid_name,
                                        definition=str(simple_definition),
                                        roleArn=default_stepfunction_role)
        exc.exception.response['Error']['Code'].should.equal('InvalidName')
        exc.exception.response['Error']['Message'].should.equal("Invalid Name: '" + invalid_name + "'")
        exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
def test_state_machine_creation_requires_valid_role_arn():
    client = boto3.client('stepfunctions', region_name=region)
    name = 'example_step_function'
    #
    with assert_raises(ClientError) as exc:
        client.create_state_machine(name=name,
                                    definition=str(simple_definition),
                                    roleArn='arn:aws:iam:1234:role/unknown_role')
    exc.exception.response['Error']['Code'].should.equal('InvalidArn')
    exc.exception.response['Error']['Message'].should.equal("Invalid Role Arn: 'arn:aws:iam:1234:role/unknown_role'")
    exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
@mock_sts
def test_state_machine_creation_requires_role_in_same_account():
    client = boto3.client('stepfunctions', region_name=region)
    name = 'example_step_function'
    #
    with assert_raises(ClientError) as exc:
        client.create_state_machine(name=name,
                                    definition=str(simple_definition),
                                    roleArn='arn:aws:iam:000000000000:role/unknown_role')
    exc.exception.response['Error']['Code'].should.equal('AccessDeniedException')
    exc.exception.response['Error']['Message'].should.equal('Cross-account pass role is not allowed.')
    exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
def test_state_machine_list_returns_empty_list_by_default():
    client = boto3.client('stepfunctions', region_name=region)
    #
    list = client.list_state_machines()
    list['stateMachines'].should.be.empty


@mock_stepfunctions
@mock_sts
def test_state_machine_list_returns_created_state_machines():
    client = boto3.client('stepfunctions', region_name=region)
    #
    machine2 = client.create_state_machine(name='name2',
                                           definition=str(simple_definition),
                                           roleArn=default_stepfunction_role)
    machine1 = client.create_state_machine(name='name1',
                                           definition=str(simple_definition),
                                           roleArn=default_stepfunction_role,
                                           tags=[{'key': 'tag_key', 'value': 'tag_value'}])
    list = client.list_state_machines()
    #
    list['ResponseMetadata']['HTTPStatusCode'].should.equal(200)
    list['stateMachines'].should.have.length_of(2)
    list['stateMachines'][0]['creationDate'].should.be.a(datetime)
    list['stateMachines'][0]['creationDate'].should.equal(machine1['creationDate'])
    list['stateMachines'][0]['name'].should.equal('name1')
    list['stateMachines'][0]['stateMachineArn'].should.equal(machine1['stateMachineArn'])
    list['stateMachines'][1]['creationDate'].should.be.a(datetime)
    list['stateMachines'][1]['creationDate'].should.equal(machine2['creationDate'])
    list['stateMachines'][1]['name'].should.equal('name2')
    list['stateMachines'][1]['stateMachineArn'].should.equal(machine2['stateMachineArn'])


@mock_stepfunctions
@mock_sts
def test_state_machine_creation_is_idempotent_by_name():
    client = boto3.client('stepfunctions', region_name=region)
    #
    client.create_state_machine(name='name', definition=str(simple_definition), roleArn=default_stepfunction_role)
    sm_list = client.list_state_machines()
    sm_list['stateMachines'].should.have.length_of(1)
    #
    client.create_state_machine(name='name', definition=str(simple_definition), roleArn=default_stepfunction_role)
    sm_list = client.list_state_machines()
    sm_list['stateMachines'].should.have.length_of(1)
    #
    client.create_state_machine(name='diff_name', definition=str(simple_definition), roleArn=default_stepfunction_role)
    sm_list = client.list_state_machines()
    sm_list['stateMachines'].should.have.length_of(2)


@mock_stepfunctions
@mock_sts
def test_state_machine_creation_can_be_described_by_name():
    client = boto3.client('stepfunctions', region_name=region)
    #
    sm = client.create_state_machine(name='name', definition=str(simple_definition), roleArn=default_stepfunction_role)
    desc = client.describe_state_machine(stateMachineArn=sm['stateMachineArn'])
    desc['ResponseMetadata']['HTTPStatusCode'].should.equal(200)
    desc['creationDate'].should.equal(sm['creationDate'])
    desc['definition'].should.equal(str(simple_definition))
    desc['name'].should.equal('name')
    desc['roleArn'].should.equal(default_stepfunction_role)
    desc['stateMachineArn'].should.equal(sm['stateMachineArn'])
    desc['status'].should.equal('ACTIVE')


@mock_stepfunctions
@mock_sts
def test_state_machine_throws_error_when_describing_unknown_machine():
    client = boto3.client('stepfunctions', region_name=region)
    #
    with assert_raises(ClientError) as exc:
        unknown_state_machine = 'arn:aws:states:' + region + ':' + str(DEFAULT_ACCOUNT_ID) + ':stateMachine:unknown'
        client.describe_state_machine(stateMachineArn=unknown_state_machine)
    exc.exception.response['Error']['Code'].should.equal('StateMachineDoesNotExist')
    exc.exception.response['Error']['Message'].\
        should.equal("State Machine Does Not Exist: '" + unknown_state_machine + "'")
    exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
@mock_sts
def test_state_machine_throws_error_when_describing_machine_in_different_account():
    client = boto3.client('stepfunctions', region_name=region)
    #
    with assert_raises(ClientError) as exc:
        unknown_state_machine = 'arn:aws:states:' + region + ':000000000000:stateMachine:unknown'
        client.describe_state_machine(stateMachineArn=unknown_state_machine)
    exc.exception.response['Error']['Code'].should.equal('AccessDeniedException')
    exc.exception.response['Error']['Message'].should.contain('is not authorized to access this resource')
    exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
@mock_sts
def test_state_machine_can_be_deleted():
    client = boto3.client('stepfunctions', region_name=region)
    sm = client.create_state_machine(name='name', definition=str(simple_definition), roleArn=default_stepfunction_role)
    #
    response = client.delete_state_machine(stateMachineArn=sm['stateMachineArn'])
    response['ResponseMetadata']['HTTPStatusCode'].should.equal(200)
    #
    sm_list = client.list_state_machines()
    sm_list['stateMachines'].should.have.length_of(0)


@mock_stepfunctions
@mock_sts
def test_state_machine_can_deleted_nonexisting_machine():
    client = boto3.client('stepfunctions', region_name=region)
    #
    unknown_state_machine = 'arn:aws:states:' + region + ':123456789012:stateMachine:unknown'
    response = client.delete_state_machine(stateMachineArn=unknown_state_machine)
    response['ResponseMetadata']['HTTPStatusCode'].should.equal(200)
    #
    sm_list = client.list_state_machines()
    sm_list['stateMachines'].should.have.length_of(0)


@mock_stepfunctions
@mock_sts
def test_state_machine_deletion_validates_arn():
    client = boto3.client('stepfunctions', region_name=region)
    #
    with assert_raises(ClientError) as exc:
        unknown_account_id = 'arn:aws:states:' + region + ':000000000000:stateMachine:unknown'
        client.delete_state_machine(stateMachineArn=unknown_account_id)
    exc.exception.response['Error']['Code'].should.equal('AccessDeniedException')
    exc.exception.response['Error']['Message'].should.contain('is not authorized to access this resource')
    exc.exception.response['ResponseMetadata']['HTTPStatusCode'].should.equal(400)


@mock_stepfunctions
@mock_sts
def test_state_machine_list_tags_for_created_machine():
    client = boto3.client('stepfunctions', region_name=region)
    #
    machine = client.create_state_machine(name='name1',
                                           definition=str(simple_definition),
                                           roleArn=default_stepfunction_role,
                                           tags=[{'key': 'tag_key', 'value': 'tag_value'}])
    response = client.list_tags_for_resource(resourceArn=machine['stateMachineArn'])
    tags = response['tags']
    tags.should.have.length_of(1)
    tags[0].should.equal({'key': 'tag_key', 'value': 'tag_value'})


@mock_stepfunctions
@mock_sts
def test_state_machine_list_tags_for_machine_without_tags():
    client = boto3.client('stepfunctions', region_name=region)
    #
    machine = client.create_state_machine(name='name1',
                                           definition=str(simple_definition),
                                           roleArn=default_stepfunction_role)
    response = client.list_tags_for_resource(resourceArn=machine['stateMachineArn'])
    tags = response['tags']
    tags.should.have.length_of(0)


@mock_stepfunctions
@mock_sts
def test_state_machine_list_tags_for_nonexisting_machine():
    client = boto3.client('stepfunctions', region_name=region)
    #
    non_existing_state_machine = 'arn:aws:states:' + region + ':' + str(DEFAULT_ACCOUNT_ID) + ':stateMachine:unknown'
    response = client.list_tags_for_resource(resourceArn=non_existing_state_machine)
    tags = response['tags']
    tags.should.have.length_of(0)
