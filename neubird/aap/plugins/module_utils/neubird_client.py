# -*- coding: utf-8 -*-
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import json
import time as _time

try:
    from urllib import quote as _url_quote
except ImportError:
    from urllib.parse import quote as _url_quote

from ansible.module_utils.urls import open_url


def login(url, username, password):
    """POST /api/v1/user/login -> access_token string."""
    endpoint = '{0}/api/v1/user/login'.format(url.rstrip('/'))
    payload = json.dumps({'email': username, 'password': password}).encode('utf-8')
    response = open_url(
        endpoint,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
        validate_certs=True,
    )
    return json.loads(response.read())['access_token']


def get_project_uuid(url, token, project_name):
    """GET /api/v1/project?search=<name> -> uuid string or None (exact name match)."""
    endpoint = '{0}/api/v1/project?search={1}'.format(url.rstrip('/'), _url_quote(project_name, safe=''))
    response = open_url(
        endpoint,
        data=json.dumps({}).encode('utf-8'),
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
        },
        method='GET',
        validate_certs=True,
    )
    specs = json.loads(response.read()).get('specs', [])
    for spec in specs:
        if spec.get('name') == project_name:
            return spec['uuid']
    return None


def _build_session_payload(project_uuid, prompt_text):
    return json.dumps({
        'project_uuid': project_uuid,
        'action': 'ACTION_NEXT',
        'session_mode': 'SESSION_MODE_CHAT',
        'session_type': 'SESSION_TYPE_USER',
        'session_origin': 'SESSION_ORIGIN_AUTOMATED',
        'messages': [{
            'content': {
                'content_type': 'CONTENT_TYPE_CHAT_PROMPT',
                'parts': [prompt_text],
            },
            'type': 'MESSAGE_TYPE_PROMPT',
        }],
    }).encode('utf-8')


def _sse_until(url, token, project_uuid, prompt_text, stop_type, connect_timeout):
    """POST /api/v1/inference/session; iterate SSE lines until stop_type event."""
    endpoint = '{0}/api/v1/inference/session'.format(url.rstrip('/'))
    response = open_url(
        endpoint,
        data=_build_session_payload(project_uuid, prompt_text),
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
        method='POST',
        validate_certs=True,
        timeout=connect_timeout,
    )
    for raw_line in response:
        line = raw_line.decode('utf-8', errors='replace').strip()
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:].strip())
                if event.get('type') == stop_type:
                    return
            except (ValueError, KeyError):
                pass
    raise Exception('SSE stream ended before {0} event'.format(stop_type))


def trigger_investigation(url, token, project_uuid, prompt_text):
    """POST /api/v1/inference/session; read SSE until first session_metadata event."""
    _sse_until(url, token, project_uuid, prompt_text, 'session_metadata', connect_timeout=60)


def wait_for_investigation(url, token, project_uuid, prompt_text, timeout=360):
    """POST /api/v1/inference/session; read SSE until done event or timeout."""
    deadline = _time.time() + timeout

    endpoint = '{0}/api/v1/inference/session'.format(url.rstrip('/'))
    response = open_url(
        endpoint,
        data=_build_session_payload(project_uuid, prompt_text),
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
        method='POST',
        validate_certs=True,
        timeout=90,
    )
    for raw_line in response:
        if _time.time() > deadline:
            raise Exception('Investigation timed out after {0} seconds'.format(timeout))
        line = raw_line.decode('utf-8', errors='replace').strip()
        if line.startswith('data:'):
            try:
                event = json.loads(line[5:].strip())
                if event.get('type') == 'done':
                    return
            except (ValueError, KeyError):
                pass
    raise Exception('SSE stream ended before done event')


def get_session_by_time(url, token, project_uuid, created_after):
    """POST /api/v2/inference/session/list with created_after -> sessions[0] or None."""
    endpoint = '{0}/api/v2/inference/session/list'.format(url.rstrip('/'))
    payload = json.dumps({
        'project_uuid': project_uuid,
        'created_after': created_after,
        'pagination': {'page_size': 5},
    }).encode('utf-8')
    response = open_url(
        endpoint,
        data=payload,
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
        },
        method='POST',
        validate_certs=True,
    )
    sessions = json.loads(response.read()).get('sessions', [])
    return sessions[0] if sessions else None


def get_session_metadata(url, token, session_uuid):
    """GET /api/v2/inference/session/metadata/{uuid} -> full response dict."""
    endpoint = '{0}/api/v2/inference/session/metadata/{1}'.format(url.rstrip('/'), session_uuid)
    response = open_url(
        endpoint,
        data=json.dumps({}).encode('utf-8'),
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
        },
        method='GET',
        validate_certs=True,
    )
    return json.loads(response.read())


def get_session_summary(url, token, session_uuid):
    """GET /api/v2/inference/session/summary/{uuid} -> summary_sections dict."""
    endpoint = '{0}/api/v2/inference/session/summary/{1}'.format(url.rstrip('/'), session_uuid)
    response = open_url(
        endpoint,
        data=json.dumps({}).encode('utf-8'),
        headers={
            'Authorization': 'Bearer {0}'.format(token),
            'Content-Type': 'application/json',
        },
        method='GET',
        validate_certs=True,
    )
    return json.loads(response.read()).get('summary_sections', {})
