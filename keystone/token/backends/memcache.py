# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack LLC
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from __future__ import absolute_import
import copy

import memcache

from keystone.common import utils
from keystone import config
from keystone import exception
from keystone.openstack.common import jsonutils
from keystone import token


CONF = config.CONF
config.register_str('servers', group='memcache', default='localhost:11211')


class Token(token.Driver):

    revocation_key = 'revocation-list'

    def __init__(self, client=None):
        self._memcache_client = client

    @property
    def client(self):
        return self._memcache_client or self._get_memcache_client()

    def _get_memcache_client(self):
        memcache_servers = CONF.memcache.servers.split(',')
        self._memcache_client = memcache.Client(memcache_servers, debug=0)
        return self._memcache_client

    def _prefix_token_id(self, token_id):
        return 'token-%s' % token_id.encode('utf-8')

    def get_token(self, token_id):
        ptk = self._prefix_token_id(token_id)
        token = self.client.get(ptk)
        if token is None:
            raise exception.TokenNotFound(token_id=token_id)

        return token

    def create_token(self, token_id, data):
        data_copy = copy.deepcopy(data)
        ptk = self._prefix_token_id(token_id)
        if 'expires' not in data_copy:
            data_copy['expires'] = self._get_default_expire_time()
        kwargs = {}
        if data_copy['expires'] is not None:
            expires_ts = utils.unixtime(data_copy['expires'])
            kwargs['time'] = expires_ts
        self.client.set(ptk, data_copy, **kwargs)
        return copy.deepcopy(data_copy)

    def _add_to_revocation_list(self, data):
        data_json = jsonutils.dumps(data)
        if not self.client.append(self.revocation_key, ',%s' % data_json):
            if not self.client.add(self.revocation_key, data_json):
                if not self.client.append(self.revocation_key,
                                          ',%s' % data_json):
                    msg = _('Unable to add token to revocation list.')
                    raise exception.UnexpectedError(msg)

    def delete_token(self, token_id):
        # Test for existence
        data = self.get_token(token_id)
        ptk = self._prefix_token_id(token_id)
        result = self.client.delete(ptk)
        self._add_to_revocation_list(data)
        return result

    def list_revoked_tokens(self):
        list_json = self.client.get(self.revocation_key)
        if list_json:
            return jsonutils.loads('[%s]' % list_json)
        return []
