# launch_vault

This is a quick utility script to automatically launch a Vault docker container, configure it, write the provided secret, and return the role ID and secret ID.  You can use this to expedite testing with vault integrations.

What this script does:

mode:init
- Pulls and launches Vault docker container
- Enable AppRole
- Write provided secret to path 'secret/sdc/passwd' under key 'value'
- Create role 'sdcrole' with read policy on 'secret/sdc/*'
- Print obtained role ID and secret ID for 'sdcrole'

mode:read-secret
- Uses the provided role ID and secret ID to login and obtain client token
- Use client token to read value stored under 'secret/sdc/passwd'
- Print this value

Requirements:
You will need the docker service installed and running.  You will also need pip3 and python installed.

To install:
```
git clone https://github.com/hiro-kuwabara/launch_vault/
cd launch_vault
pip3 install .
```

You should now be able to run 'launch_vault' on commandline.

For help:
```
launch_vault -h
```

To initialize container, write secret value to 'secret/sdc/passwd', configure, and get role ID + secret ID:
```
launch_vault init --secret-value <value>
```

To validate the secret is readable by logging in with the returned role ID + secret ID and sending a request with the returned client token:
```
launch_vault read-secret --secret-id <secret_id> --role-id <role_id>
```

For StreamSets Data Collector:

In $SDC_CONF/credential-stores.properties, set the following parameters:
```
credentialStores=vault
credentialStore.vault.config.role.id=<role_id>
credentialStore.vault.config.secret.id=<secret_id>
```
where:

<role_id> is the Role ID returned from 'launch_vault init'

<secret_id> is the Secret ID returned from 'launch_vault init'.  If set to a file (e.g. ${file("vault-secret-id")}), update the content of the file with the Secret ID returned.

Afterwards, restart Data Collector, and the secret should be accessible through the credential EL.  E.g. ${credential:get("vault", "all", "/secret/sdc/passwd&value")}
