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

from oslo.config import cfg

from keystone.openstack.common.db import api as db_api

CONF = cfg.CONF

_BACKEND_MAPPING = {'sqlalchemy': 'keystone.contrib.kds.db.sqlalchemy.api',
                    'kvs': 'keystone.contrib.kds.db.kvs.api'}

IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


def reset():
    global IMPL
    IMPL = db_api.DBAPI(backend_mapping=_BACKEND_MAPPING)


def get_instance():
    """Return a DB API instance."""
    return IMPL
