''' unit tests ONTAP Ansible module: na_ontap_snapmirror '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from ansible_collections.netapp.ontap.tests.unit.compat import unittest
from ansible_collections.netapp.ontap.tests.unit.compat.mock import patch, Mock
import ansible_collections.netapp.ontap.plugins.module_utils.netapp as netapp_utils

from ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror \
    import NetAppONTAPSnapmirror as my_module

if not netapp_utils.has_netapp_lib():
    pytestmark = pytest.mark.skip('skipping as missing required netapp_lib')


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


def get_args_rest():
    """ set args for rest """
    args = {
        "hostname": "10.193.189.206",
        "username": "admin",
        "password": "netapp123",
        "https": "yes",
        "validate_certs": "no",
        "use_rest": "always",
        "state": "present",
        "initialize": "True",
        "relationship_state": "active",
        "source_path": "svmsrc3:volsrc1",
        "destination_path": "svmdst3:voldst1",
        "relationship_type": "extended_data_protection"
    }
    return args


def get_args_restore_rest():
    """ set args for rest """
    args = {
        "hostname": "10.193.177.97",
        "username": "admin",
        "password": "netapp123",
        "https": "yes",
        "validate_certs": "no",
        "use_rest": "always",
        "state": "present",
        "initialize": "True",
        "relationship_state": "active",
        "source_vserver": "svmdst3",
        "source_volume": "voldst1",
        "source_hostname": "10.193.189.206",
        "source_username": "admin",
        "source_password": "netapp123",
        "destination_vserver": "svmsrc3",
        "destination_volume": "volsrc1",
        "relationship_type": "restore"
    }
    return args


def set_module_args_rest(args):
    """prepare arguments to use for REST """
    data = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(data)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


# REST API canned responses when mocking send_request
SRR = {
    # common responses
    'is_rest': (200, dict(version=dict(generation=9, major=8, minor=0, full='dummy')), None),
    'is_rest_9_7_0': (200, dict(version=dict(generation=9, major=7, minor=0, full='dummy')), None),
    'is_zapi': (400, {}, "Unreachable"),
    'empty_good': (200, {}, None),
    'end_of_sequence': (500, None, "Unexpected call to send_request"),
    'generic_error': (400, None, "Expected error"),
    # module specific responses
    'snapmirror_policy': (200, dict(num_records=1, records=[dict(type='async')]), None),
    'snapmirror_policy_unexpected_type': (200, dict(num_records=1, records=[dict(type='ohlala')]), None),
    'sm_get_empty': (200, {
        'records': [],
        'num_records': 0
    }, None),
    'snapmirror_post_responses': (200, {
        'uuid': '3a23a60e-542c-11ec-9779-005056b39a06',
        'state': 'success',
        '_links': {
            'self': {
                'href': '/api/cluster/jobs/3a23a60e-542c-11ec-9779-005056b39a06'
            }
        }
    }, None),
    'snapmirror_patch_responses': (200, {
        'uuid': '3a23a60e-542c-11ec-9779-005056b39a06',
        'state': 'success',
    }, None),
    'sm_get_uninitialized': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'uninitialized',
            'healthy': True,
        }],
        'num_records': 1,
    }, None),
    'sm_get_mirrored': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'snapmirrored',
            'transfer': {
                'state': 'success'
            },
            'healthy': True,
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/b5ee4571-5429-11ec-9779-005056b39a06/'
                }
            }
        }],
        'num_records': 1,
    }, None),
    'sm_get_restore': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmsrc3:volsrc1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'snapmirrored',
            'transfer': {
                'state': 'success'
            },
            'healthy': True,
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/b5ee4571-5429-11ec-9779-005056b39a06/'
                }
            }
        }],
        'num_records': 1,
    }, None),
    'sm_get_paused': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'paused',
            'transfer': {
                'state': 'success'
            },
            'healthy': True,
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/b5ee4571-5429-11ec-9779-005056b39a06/'
                }
            }
        }],
        'num_records': 1
    }, None),
    'sm_get_broken': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'broken_off',
            'transfer': {
                'state': 'success'
            },
            'healthy': True,
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/b5ee4571-5429-11ec-9779-005056b39a06/'
                }
            }
        }],
        'num_records': 1
    }, None),
    'sm_get_data_transferring': (200, {
        'records': [{
            'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'paused',
            'transfer': {
                'state': 'transferring',
                'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06'
            },
            'healthy': True,
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/b5ee4571-5429-11ec-9779-005056b39a06/'
                }
            }
        }],
        'num_records': 1
    }, None),
    'sm_get_resync': (200, {
        'uuid': 'b5ee4571-5429-11ec-9779-005056b39a06',
        'description': 'PATCH /api/snapmirror/relationships/1c4467ca-5434-11ec-9779-005056b39a06',
        'state': 'success',
        'message': 'success',
        'code': 0,
        '_links': {
            'self': {
                'href': '/api/cluster/jobs/6cd7ce6f-5434-11ec-9779-005056b39a06'
            }
        }
    }, None),
    'sm_get_abort': (200, {
        'records': [{
            'uuid': '7ddb18a6-542c-11ec-9779-005056b39a06',
            'destination': {
                'path': 'svmdst3:voldst1'
            },
            'policy': {
                'name': 'MirrorAndVault'
            },
            'state': 'snapmirrored',
            'transfer': {
                'state': 'failed'
            },
            'healthy': False,
            'unhealthy_reason': [{
                'message': 'Transfer aborted.'
            }],
            '_links': {
                'self': {
                    'href': '/api/snapmirror/relationships/7ddb18a6/'
                }
            }
        }],
        'num_records': 1
    }, None),
    'job_status': (201, {
        'job': {
            'uuid': '3a23a60e-542c-11ec-9779-005056b39a06',
            '_links': {
                'self': {
                    'href': '/api/cluster/jobs/3a23a60e-542c-11ec-9779-005056b39a06'
                }
            }
        }
    }, None)
}


class MockONTAPConnection(object):
    ''' mock server connection to ONTAP host '''

    def __init__(self, kind=None, parm=None, status=None, quiesce_status='passed'):
        ''' save arguments '''
        self.type = kind
        self.xml_in = None
        self.xml_out = None
        self.parm = parm
        self.status = status
        self.quiesce_status = quiesce_status

    def invoke_successfully(self, xml, enable_tunneling):  # pylint: disable=unused-argument
        ''' mock invoke_successfully returning xml data '''
        self.xml_in = xml
        if self.type == 'snapmirror':
            xml = self.build_snapmirror_info(
                self.parm, self.status, self.quiesce_status)
        elif self.type == 'snapmirror_fail':
            raise netapp_utils.zapi.NaApiError(
                code='TEST', message="This exception is from the unit test")
        self.xml_out = xml
        return xml

    @staticmethod
    def build_snapmirror_info(mirror_state, status, quiesce_status):
        ''' build xml data for snapmirror-entry '''
        xml = netapp_utils.zapi.NaElement('xml')
        data = {
            'num-records': 1,
            'status': quiesce_status,
            'attributes-list': {
                'snapmirror-info': {
                    'mirror-state': mirror_state,
                    'schedule': None,
                    'source-location': 'ansible:ansible',
                    'relationship-status': status,
                    'policy': 'ansible_policy',
                    'relationship-type': 'data_protection',
                    'max-transfer-rate': 1000,
                    'identity-preserve': 'true'
                },
                'snapmirror-destination-info': {
                    'destination-location': 'ansible'
                }
            }
        }
        xml.translate_struct(data)
        return xml


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)
        self.server = MockONTAPConnection()
        self.source_server = MockONTAPConnection()
        self.onbox = False

    def set_default_args(self):
        policy = 'ansible' if self.onbox else 'ansible_policy'
        use_rest = 'never'
        source_password = 'password'
        hostname = '10.10.10.10'
        update = True
        schedule = None
        username = 'admin'
        source_vserver = 'ansible'
        source_path = 'ansible:ansible'
        destination_path = 'ansible:ansible'
        relationship_state = 'active'
        destination_vserver = 'ansible'
        password = 'password'
        source_username = 'admin'
        relationship_type = 'data_protection'
        return dict({
            'hostname': hostname,
            'username': username,
            'password': password,
            'source_path': source_path,
            'destination_path': destination_path,
            'policy': policy,
            'source_vserver': source_vserver,
            'destination_vserver': destination_vserver,
            'relationship_type': relationship_type,
            'schedule': schedule,
            'source_username': source_username,
            'source_password': source_password,
            'relationship_state': relationship_state,
            'update': update,
            'use_rest': use_rest
        })

    def test_module_fail_when_required_args_missing(self):
        ''' required arguments are reported as errors '''
        with pytest.raises(AnsibleFailJson) as exc:
            set_module_args({})
            my_module()
        print('Info: %s' % exc.value.args[0]['msg'])

    def test_ensure_get_called(self):
        ''' test snapmirror_get for non-existent snapmirror'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = self.server
        assert my_obj.snapmirror_get is not None

    def test_ensure_get_called_existing(self):
        ''' test snapmirror_get for existing snapmirror'''
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.server = MockONTAPConnection(kind='snapmirror', status='idle')
        assert my_obj.snapmirror_get()

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    def test_successful_create(self, snapmirror_create):
        ''' creating snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['identity_preserve'] = True
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        data = self.set_default_args()
        data['update'] = False
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', 'snapmirrored', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_failure_break(self):
        ''' breaking snapmirror to test quiesce time-delay failure '''
        data = self.set_default_args()
        data['relationship_state'] = 'broken'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', 'snapmirrored', status='idle', quiesce_status='InProgress')
        with pytest.raises(AnsibleFailJson) as exc:
            # replace time.sleep with a noop
            with patch('time.sleep', lambda a: None):
                my_obj.apply()
        assert 'Taking a long time to Quiescing SnapMirror, try again later' in exc.value.args[
            0]['msg']

    def test_successful_break(self):
        ''' breaking snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['relationship_state'] = 'broken'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', 'snapmirrored', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        # to reset na_helper from remembering the previous 'changed' value
        set_module_args(self.set_default_args())
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', 'broken-off', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    def test_successful_create_without_initialize(self):
        ''' creating snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['identity_preserve'] = True
        data['initialize'] = False
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        my_obj.server = MockONTAPConnection(
            'snapmirror', 'Uninitialized', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_elementsw_parameters')
    def test_successful_element_ontap_create(self, check_param, snapmirror_create):
        ''' creating ElementSW to ONTAP snapmirror '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['connection_type'] = 'elementsw_ontap'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        check_param.assert_called_with()

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_create')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_elementsw_parameters')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_get')
    def test_successful_ontap_element_create(self, snapmirror_get, check_param, snapmirror_create):
        ''' creating ONTAP to ElementSW snapmirror '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['connection_type'] = 'ontap_elementsw'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        snapmirror_get.side_effect = [
            Mock(),
            None
        ]
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_create.assert_called_with()
        check_param.assert_called_with('destination')

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.delete_snapmirror')
    def test_successful_delete(self, delete_snapmirror):
        ''' deleting snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        my_obj.get_destination = Mock(return_value=True)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        delete_snapmirror.assert_called_with(False, 'data_protection', None)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_successful_delete_without_source_hostname_check(self):
        ''' source cluster hostname is optional when source is unknown'''
        data = self.set_default_args()
        data['state'] = 'absent'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    def test_successful_delete_with_source_path_state_absent_check(self):
        ''' with source cluster hostname but with state=present'''
        data = self.set_default_args()
        data['state'] = 'absent'
        data.pop('destination_path')
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        assert 'Missing parameters: Source path or Destination path' in exc.value.args[
            0]['msg']

    def test_successful_delete_check_get_destination(self):
        ''' check parameter source cluster hostname deleting snapmirror on both source & dest'''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
            my_obj.source_server = MockONTAPConnection(
                'snapmirror', status='idle')
        res = my_obj.get_destination()
        assert res is True

    def test_snapmirror_release(self):
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.source_server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        my_obj.snapmirror_release()
        assert my_obj.source_server.xml_in['destination-location'] == data['destination_path']

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_resume')
    def test_snapmirror_resume(self, snapmirror_resume):
        ''' resuming snapmirror '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='quiesced', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_resume.assert_called_with()

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_restore')
    def test_snapmirror_restore(self, snapmirror_restore):
        ''' restore snapmirror '''
        data = self.set_default_args()
        data['relationship_type'] = 'restore'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_restore.assert_called_with()

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.delete_snapmirror')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.wait_for_status')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_abort')
    def test_successful_abort(self, snapmirror_abort, wait_for_status, delete_snapmirror):
        ''' deleting snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['state'] = 'absent'
        data['source_hostname'] = '10.10.10.10'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='transferring')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_abort.assert_called_with()
        wait_for_status.assert_called_with()
        delete_snapmirror.assert_called_with(False, 'data_protection', None)
        # to reset na_helper from remembering the previous 'changed' value
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = self.server
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_modify')
    def test_successful_modify(self, snapmirror_modify):
        ''' modifying snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['policy'] = 'ansible2'
        data['schedule'] = 'abc2'
        data['max_transfer_rate'] = 2000
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_modify.assert_called_with(
            {'policy': 'ansible2', 'schedule': 'abc2', 'max_transfer_rate': 2000})
        # to reset na_helper from remembering the previous 'changed' value
        data = self.set_default_args()
        data['update'] = False
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.snapmirror_initialize')
    def test_successful_initialize(self, snapmirror_initialize):
        ''' initialize snapmirror and testing idempotency '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='uninitialized')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
        snapmirror_initialize.assert_called_with()
        # to reset na_helper from remembering the previous 'changed' value
        data = self.set_default_args()
        data['update'] = False
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    def test_successful_update(self):
        ''' update snapmirror and testing idempotency '''
        data = self.set_default_args()
        data['policy'] = 'ansible2'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror', status='idle')
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    def test_elementsw_volume_exists(self):
        ''' elementsw_volume_exists '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.volume_id_exists.side_effect = [1000, None]
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        my_obj.check_if_elementsw_volume_exists(
            '10.10.10.10:/lun/1000', mock_helper)
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_if_elementsw_volume_exists(
                '10.10.10.10:/lun/1000', mock_helper)
        assert 'Error: Source volume does not exist in the ElementSW cluster' in exc.value.args[
            0]['msg']

    def test_elementsw_svip_exists(self):
        ''' svip_exists '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.get_cluster_info.return_value.cluster_info.svip = '10.10.10.10'
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        my_obj.validate_elementsw_svip('10.10.10.10:/lun/1000', mock_helper)

    def test_elementsw_svip_exists_negative(self):
        ''' svip_exists negative testing'''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_helper = Mock()
        mock_helper.get_cluster_info.return_value.cluster_info.svip = '10.10.10.10'
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.validate_elementsw_svip(
                '10.10.10.11:/lun/1000', mock_helper)
        assert 'Error: Invalid SVIP' in exc.value.args[0]['msg']

    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.set_element_connection')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.validate_elementsw_svip')
    @patch('ansible_collections.netapp.ontap.plugins.modules.na_ontap_snapmirror.NetAppONTAPSnapmirror.check_if_elementsw_volume_exists')
    def test_check_elementsw_params_source(self, validate_volume, validate_svip, connection):
        ''' check elementsw parameters for source '''
        data = self.set_default_args()
        data['source_path'] = '10.10.10.10:/lun/1000'
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        mock_elem, mock_helper = Mock(), Mock()
        connection.return_value = mock_helper, mock_elem
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        my_obj.check_elementsw_parameters('source')
        connection.called_once_with('source')
        validate_svip.called_once_with(data['source_path'], mock_elem)
        validate_volume.called_once_with(data['source_path'], mock_helper)

    def test_check_elementsw_params_negative(self):
        ''' check elementsw parameters for source negative testing '''
        data = self.set_default_args()
        del data['source_path']
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_elementsw_parameters('source')
        assert 'Error: Missing required parameter source_path' in exc.value.args[0]['msg']

    def test_check_elementsw_params_invalid(self):
        ''' check elementsw parameters for source invalid testing '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_elementsw_parameters('source')
        assert 'Error: invalid source_path' in exc.value.args[0]['msg']

    def test_elementsw_source_path_format(self):
        ''' test element_source_path_format_matches '''
        data = self.set_default_args()
        set_module_args(data)
        my_obj = my_module()
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        match = my_obj.element_source_path_format_matches('1.1.1.1:dummy')
        assert match is None
        match = my_obj.element_source_path_format_matches(
            '10.10.10.10:/lun/10')
        assert match is not None

    def test_remote_volume_exists(self):
        ''' test check_if_remote_volume_exists '''
        data = self.set_default_args()
        data['source_volume'] = 'test_vol'
        data['destination_volume'] = 'test_vol2'
        set_module_args(data)
        my_obj = my_module()
        my_obj.set_source_cluster_connection = Mock(return_value=None)
        my_obj.asup_log_for_cserver = Mock(return_value=None)
        if not self.onbox:
            my_obj.server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
            my_obj.source_server = MockONTAPConnection(
                'snapmirror', status='idle', parm='snapmirrored')
        res = my_obj.check_if_remote_volume_exists()
        assert res

    def test_if_all_methods_catch_exception(self):
        data = self.set_default_args()
        data['source_hostname'] = '10.10.10.10'
        data['source_volume'] = 'ansible'
        data['destination_volume'] = 'ansible2'
        set_module_args(data)
        my_obj = my_module()
        if not self.onbox:
            my_obj.server = MockONTAPConnection('snapmirror_fail')
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_get()
        assert 'Error fetching snapmirror info: ' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_abort()
        assert 'Error aborting SnapMirror relationship :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_quiesce = Mock(return_value=None)
            my_obj.snapmirror_break()
        assert 'Error breaking SnapMirror relationship :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_get = Mock(
                return_value={'mirror_state': 'transferring'})
            my_obj.snapmirror_initialize()
        assert 'Error initializing SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_update('data_protection')
        assert 'Error updating SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.set_source_cluster_connection = Mock(return_value=True)
            my_obj.source_server = MockONTAPConnection('snapmirror_fail')
            my_obj.check_if_remote_volume_exists()
        assert 'Error fetching source volume details' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_if_remote_volume_exists = Mock(return_value=True)
            my_obj.source_server = MockONTAPConnection()
            my_obj.snapmirror_create()
        assert 'Error creating SnapMirror ' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_quiesce = Mock(return_value=None)
            my_obj.get_destination = Mock(return_value=None)
            my_obj.snapmirror_break = Mock(return_value=None)
            my_obj.delete_snapmirror(False, 'data_protection', None)
        assert 'Error deleting SnapMirror :' in exc.value.args[0]['msg']
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.snapmirror_modify({'policy': 'ansible2', 'schedule': 'abc2'})
        assert 'Error modifying SnapMirror schedule or policy :' in exc.value.args[0]['msg']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_successful_rest_create(self, mock_request):
        ''' creating snapmirror and testing idempotency '''
        set_module_args_rest(get_args_rest())
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_empty'],
            SRR['job_status'],
            SRR['snapmirror_post_responses'],
            SRR['sm_get_uninitialized'],  # SM get while SM init
            SRR['sm_get_uninitialized'],  # SM get inside SM init
            SRR['job_status'],
            SRR['snapmirror_patch_responses'],
            SRR['sm_get_mirrored'],
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    def test_negative_rest_create(self):
        ''' creating snapmirror with unsupported REST options '''
        data = self.set_default_args()
        data['schedule'] = 'abc'
        data['identity_preserve'] = True
        data['use_rest'] = 'always'
        set_module_args(data)
        with pytest.raises(AnsibleFailJson) as exc:
            my_module()
        msg = "REST API currently does not support 'identity_preserve, schedule, relationship_type: data_protection'"
        assert msg in exc.value.args[0]['msg']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_initialize(self, mock_request):
        ''' snapmirror initialize testing '''
        set_module_args_rest(get_args_rest())
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_uninitialized'],  # first snapmirror_initialize calls sm_get
            SRR['sm_get_uninitialized'],  # Inside SM init calls sm_get
            SRR['sm_get_uninitialized'],
            SRR['snapmirror_patch_responses'],  # Inside SM init patch response
            SRR['job_status'],
            SRR['sm_get_uninitialized'],   # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_update(self, mock_request):
        ''' snapmirror initialize testing '''
        set_module_args_rest(get_args_rest())
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_mirrored'],  # first sm_get
            SRR['sm_get_mirrored'],  # appy update calls again sm_get
            SRR['sm_get_mirrored'],  # sm update fn calls again sm_get
            SRR['snapmirror_patch_responses'],  # sm update
            SRR['job_status'],
            SRR['sm_get_mirrored'],   # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_sm_break_success_no_data_transfer(self, mock_request):
        ''' testing snapmirror break when no_data are transferring '''
        data = get_args_rest()
        data['relationship_state'] = 'broken'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_mirrored'],  # apply first sm_get with no data transfer
            SRR['sm_get_mirrored'],  # sm break calls again sm_get
            SRR['sm_get_mirrored'],  # sm quiesce api fn calls again sm_get
            SRR['snapmirror_patch_responses'],  # SM quiesce response
            SRR['job_status'],
            # sm quiesce validate the state which calls sm_get
            SRR['sm_get_mirrored'],
            # sm quiesce validate the state which calls sm_get after wait
            SRR['sm_get_paused'],
            SRR['sm_get_paused'],   # sm break calls sm_get
            SRR['snapmirror_patch_responses'],  # sm break response
            SRR['job_status'],
            SRR['sm_get_paused'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_sm_break_success_no_data_transfer_idempotency(self, mock_request):
        ''' testing snapmirror break when no_data are transferring idempotency '''
        data = get_args_rest()
        data['relationship_state'] = 'broken'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_broken'],  # apply first sm_get with no data transfer
            SRR['sm_get_broken'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert not exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_sm_break_fails_if_uninit(self, mock_request):
        ''' testing snapmirror break fails if sm state uninitialized '''
        data = get_args_rest()
        data['relationship_state'] = 'broken'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            # apply first sm_get with state uninitialized
            SRR['sm_get_uninitialized'],
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = "SnapMirror relationship cannot be broken if mirror state is uninitialized"
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_squiesce_fail_when_state_not_paused(self, mock_request):
        ''' testing snapmirror break when no_data are transferring '''
        data = get_args_rest()
        data['relationship_state'] = 'broken'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_mirrored'],  # apply first sm_get with no data transfer
            SRR['sm_get_mirrored'],  # sm break calls again sm_get
            SRR['sm_get_mirrored'],  # sm quiesce api fn calls again sm_get
            SRR['job_status'],
            SRR['snapmirror_patch_responses'],  # SM quiesce response
            # SM quiesce validate the state which calls sm_get after wait
            SRR['sm_get_mirrored'],
            SRR['sm_get_mirrored'],   # first fail
            SRR['sm_get_mirrored'],   # second fail
            SRR['sm_get_mirrored'],   # third fail
            SRR['sm_get_mirrored'],   # fourth fail
            SRR['end_of_sequence']   # fifth fail
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = "Taking a long time to Quiescing SnapMirror, try again later"
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_break_fails_if_data_is_transferring(self, mock_request):
        ''' testing snapmirror break when no_data are transferring '''
        data = get_args_rest()
        data['relationship_state'] = 'broken'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            # apply first sm_get with data transfer
            SRR['sm_get_data_transferring'],
            SRR['sm_get_data_transferring'],  # sm break calls again sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        msg = "snapmirror data are transferring"
        assert exc.value.args[0]['msg'] == msg

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_resync_when_state_is_broken(self, mock_request):
        ''' resync when snapmirror state is broken and relationship_state active  '''
        set_module_args_rest(get_args_rest())
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_broken'],  # apply first sm_get with state broken_off
            SRR['sm_get_broken'],  # sm resync api calls again sm_get
            SRR['job_status'],
            SRR['snapmirror_patch_responses'],  # sm resync response
            SRR['sm_get_mirrored'],  # check_health calls sm_get
            SRR['end_of_sequence'],
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_resume_when_state_quiesced(self, mock_request):
        ''' resync when snapmirror state is broken and relationship_state active  '''
        set_module_args_rest(get_args_rest())
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_paused'],  # apply first sm_get with state quiesced
            SRR['sm_get_paused'],  # sm resync api calls again sm_get
            SRR['snapmirror_patch_responses'],  # sm resync response
            SRR['job_status'],
            SRR['sm_get_mirrored'],  # sm update calls sm_get
            SRR['snapmirror_patch_responses'],  # sm update response
            SRR['job_status'],
            SRR['sm_get_mirrored'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_delete(self, mock_request):
        ''' snapmirror delete '''
        data = get_args_rest()
        data['state'] = 'absent'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_mirrored'],  # apply first sm_get with no data transfer
            SRR['sm_get_mirrored'],  # sm break calls again sm_get
            SRR['sm_get_mirrored'],  # sm quiesce api fn calls again sm_get
            SRR['snapmirror_patch_responses'],  # sm quiesce response
            SRR['job_status'],
            # sm quiesce validate the state which calls sm_get
            SRR['sm_get_paused'],
            # sm quiesce validate the state which calls sm_get after wait with 0 iter
            SRR['sm_get_paused'],
            SRR['sm_get_paused'],   # sm break calls sm_get
            SRR['snapmirror_patch_responses'],  # sm break response
            SRR['job_status'],
            SRR['sm_get_broken'],   # sm delete call sm_get
            SRR['snapmirror_patch_responses'],  # sm delete response
            SRR['job_status'],
            SRR['sm_get_empty'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_delete_calls_abort(self, mock_request):
        ''' snapmirror delete calls abort when transfer state is in transferring'''
        data = get_args_rest()
        data['state'] = 'absent'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            # apply first sm_get with data transfer
            SRR['sm_get_data_transferring'],
            SRR['empty_good'],  # sm abort response
            SRR['job_status'],
            SRR['sm_get_abort'],  # sm break calls again sm_get
            SRR['sm_get_mirrored'],  # sm quiesce api fn calls again sm_get
            SRR['snapmirror_patch_responses'],  # sm quiesce response
            SRR['job_status'],
            # sm quiesce validate the state which calls sm_get
            SRR['sm_get_paused'],
            # sm quiesce validate the state which calls sm_get after wait with 0 iter
            SRR['sm_get_paused'],
            SRR['sm_get_paused'],   # sm break calls sm_get
            SRR['snapmirror_patch_responses'],  # sm break response
            SRR['job_status'],
            SRR['sm_get_broken'],   # sm delete call sm_get
            SRR['snapmirror_patch_responses'],  # sm delete response
            SRR['job_status'],
            SRR['sm_get_empty'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_modify(self, mock_request):
        ''' snapmirror modify'''
        data = get_args_rest()
        data['policy'] = 'Asynchronous'
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            SRR['sm_get_mirrored'],  # apply first sm_get
            SRR['sm_get_mirrored'],  # sm modify calls sm_get
            SRR['snapmirror_patch_responses'],  # sm modify response
            SRR['job_status'],
            SRR['sm_get_mirrored'],  # sm update calls sm_get
            SRR['snapmirror_patch_responses'],  # sm update response
            SRR['job_status'],
            SRR['sm_get_empty'],  # check_health calls sm_get
            SRR['end_of_sequence']
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_snapmirror_restore(self, mock_request):
        ''' snapmirror restore '''
        data = get_args_restore_rest()
        set_module_args_rest(data)
        mock_request.side_effect = [
            SRR['is_rest'],
            # SRR['sm_get_mirrored'],  # apply first sm_get
            SRR['job_status'],  # first post job response
            SRR['snapmirror_post_responses'],  # first post response
            SRR['sm_get_mirrored'],  # After first post call to get relationship uuid
            SRR['job_status'],  # second post job response
            SRR['snapmirror_post_responses'],  # second post response
            SRR['sm_get_mirrored'],  # check_health calls sm_get
            SRR['end_of_sequence'],
        ]
        my_obj = my_module()
        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']
