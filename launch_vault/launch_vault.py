import docker
import requests
import argparse

import json
from time import sleep

VAULT_HEADER = {'X-Vault-Token': 'myroot'}
VAULT_URL = 'http://127.0.0.1:8200'
VAULT_VERSION = '0.9.6'
RETRIES = 5

DESC = '''Launches a Vault application docker container, enables and
configures AppRole auth backend, and writes specified secret.

There are two modes available:  init, read-secret

init:  Run this mode first to initialize the container.  An App
Role called 'sdcrole' is created with a policy giving read
access to path 'secret/sdc/*'.  The value given by '--secret-value'
will then be written to 'secret/sdc/passwd'.  At the end, the Role
ID and Secret ID will be printed for use.

read-secret:  Run this mode once you've run 'init' and you have
obtained the Role ID and Secret ID.  This mode will validate that
the secret can be read from 'secret/sdc/passwd' using the provided
Role ID and Secret ID.  Use this mode for validation.
'''

def main():
    parser = argparse.ArgumentParser(description=DESC,
                                     formatter_class=argparse.RawTextHelpFormatter,
                                     prog='launch_vault')
    parser.add_argument('mode',
                        type=str,
                        choices=['init', 'read-secret'],
                        help='Specify either init or read-secret.')
    parser.add_argument('--secret-value',
                        type=str,
                        help='Secret value to write under path secret/sdc/passwd')
    parser.add_argument('--role-id',
                        type=str,
                        help='Role ID to pass for read-secret validation')
    parser.add_argument('--secret-id',
                        type=str,
                        help='Secret ID to pass for read-secret validation')
    args = parser.parse_args()
    if args.mode == 'init':
        if not args.secret_value:
            print('For init, --secret-value is required')
            return
        init(args.secret_value)
    if args.mode == 'read-secret':
        if not args.role_id or not args.secret_id:
            print('For read-secret, both --role-id and --secret-id are required')
            return
        read_secret(args.role_id, args.secret_id)

def init(secret_value):
    start_container()
    sleep(5)
    if not is_initialized():
        print('Vault server failed to initialize.  Exiting..')
        return
    requests.post(VAULT_URL+'/v1/secret/sdc/passwd',
                  data='{"value":"' + secret_value + '"}',
                  headers=VAULT_HEADER)
    approle_enable = requests.post(VAULT_URL+'/v1/sys/auth/approle',
                                   data='{"type":"approle"}',
                                   headers=VAULT_HEADER)
    policy = {'policy': '{"path": {"secret/sdc/*": {"policy": "read"}}}'}
    policy_enable = requests.put(VAULT_URL+'/v1/sys/policy/sdc-policy',
                                 json=policy,
                                 headers=VAULT_HEADER)
    requests.post(VAULT_URL+'/v1/auth/approle/role/sdcrole',
                  data='{"policies":"sdc-policy"}',
                  headers=VAULT_HEADER)
    roleid_response = requests.get(VAULT_URL+'/v1/auth/approle/role/sdcrole/role-id',
                                   headers=VAULT_HEADER)
    roleid = roleid_response.json()['data']['role_id']
    print('Role ID: ' + roleid)
    secretid_response = requests.post(VAULT_URL+'/v1/auth/approle/role/sdcrole/secret-id',
                                      headers=VAULT_HEADER)
    secretid = secretid_response.json()['data']['secret_id']
    print('Secret ID: ' + secretid)

def start_container():
    client = docker.from_env()
    print('Pulling Vault image ' + VAULT_VERSION + '...')
    client.images.pull('vault:' + VAULT_VERSION)
    print('Launching Vault server in development mode...')
    print('    VAULT_DEV_ROOT_TOKEN_ID=myroot')
    print('    Launching on 0.0.0.0:8200')
    container = client.containers.run('vault:' + VAULT_VERSION,
            cap_add=['IPC_LOCK'],
            environment=['VAULT_DEV_ROOT_TOKEN_ID=myroot'],
            ports={'8200/tcp': 8200},
            detach=True)

def is_initialized():
    for i in range(RETRIES):
        init = requests.get(VAULT_URL+'/v1/sys/init', headers=VAULT_HEADER)
        if init.json()['initialized']:
            print('Vault server is initialized')
            return True
        print('Waiting for Vault server to be initialized...')
        sleep(3)
    return False

def read_secret(role_id, secret_id):
    auth_data = '{"role_id": "' + role_id + '", \
                 "secret_id": "' + secret_id + '"}'
    try:
        login_response = requests.post(VAULT_URL+'/v1/auth/approle/login',
                                       data=auth_data,
                                       headers=VAULT_HEADER)
        client_token = login_response.json()['auth']['client_token']
    except:
        print('Failed to obtain client token using given Role ID and Secret ID.')
        print(login_response.text)
        raise
    CLIENT_TOKEN_HEADER = {'X-Vault-Token': client_token}
    secret_response = requests.get(VAULT_URL+'/v1/secret/sdc/passwd',
                                   headers=CLIENT_TOKEN_HEADER)
    try:
        secret_data = secret_response.json()['data']['value']
    except:
        print('Failed to obtain secret value')
        print(secret_response.text)
        raise
    print('Secret value obtained successfully. The value is: ' + secret_data)

if __name__ == '__main__':
    main()
