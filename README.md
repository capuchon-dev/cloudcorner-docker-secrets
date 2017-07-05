Cloud Corner #17 - Secrets in Docker
====================================

Bad practices
-------------

### Use COPY or ADD to put a secret in the image

Use this kind of Dockerfile:

    FROM alpine:3.6
    
    COPY secret.txt /var/

You can build it with (from the 'ImageUsingCOPY' directory):

     > docker build -t secret .

You can run it with:

     > docker run -it --rm --name secret secret sh
     # cat /var/secret.txt

*Problems:*
* The secret is in the image. It is very easy to retrieve for anybody.
* This is especially a problem if the image is stored in a public registry (but
  even with a private registry, this remains a problem).

**Secret must never been stored in an image!**


### Use environment variables with '-e' at runtime

You can give an environment variable at runtime:

    > docker run -it --rm -e "MYSECRET=secret" --name alpine alpine:3.6 sh
    > echo $MYSECRET

*Advantage:*
* The image is safe, it contains no secret.

*Problems:*
* The secret appears in the host shell history.
* It is very easy to inspect the container afterward to get all the environment
  variables:
  
      > docker inspect alpine
      [...]
      "Env": [
          "MYSECRET=secret",
          "no_proxy=*.local, 169.254/16",
          "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
      ],
      [...]

**Don't gives secrets using '-e' at runtime, it appears in the host shell
history and is very easy to inspect.**


Good practices
--------------

Good practices to put secrets in Docker containers are:
* Separate the process of building from the process of customizing it.
* Use Volumes to store secrets.
* Be aware of Shell history: use files instead of command line arguments.
* Use env_file instead of command line '-e' argument (however, not perfect:
  `docker inspect` still show them).
* Use Docker Compose to customize the container (in addition to Dockerfiles to
  build images).


### Full example of better practices

* Go to 'ImageUsingCompose' directory.
* Build the services (note: nothing will be built in this version, because the
  compose file use only a public image):
  
      > docker-compose build

* Run the services in interactive mode:
  
      > docker-compose run --rm secret

* Check the secrets are there:
  
      > cat /var/secret.txt
      > echo $MYSECRET

> **WARNING:** This example store the 'secrets.env' file in SCM for educational
> purpose. In real life, never do that!

However, there is several drawbacks here:
* The 'secret.txt' file is mounted in the container from the host. Which leads
  to these problems:
  * If the file is modified in the container, it is also modified on the host,
    and vice-versa.
  * If the file is shared between several containers (multiple instances), the
    writing problem is even worst.
  * This can't be used in production, where the servers are often independent
    of the command host (remote docker engine).
* The environment variables (and their values) remains visible from a
  `docker inspect` command.


Introducing Vault
-----------------

[Vault][VAULT] (from HashiCorp) is a tool for securely access secrets. Its an
executable that run as a server. It has an API to create, store, access, delete
secrets, plus authentication, revocation, etc... It uses strong encryption to
store secrets, and it uses TLS for its API (in production mode). Vault should be
seen as a key/value database with strong encryption storage and secure access.

Because Vault is a server, it inserts very well in a backend architecture. It
can be easily put in a Docker container ([official image available from Docker
Store][VAULT_DOCKER] and so can act as a micro-service in the backend, in charge
of storing secrets and providing a standardized access to them for the whole
system.

Vault is [Open Source][VAULT_SOURCES] and free to use (Mozilla Public License
2.0).


### Learn Vault basics

* Download Vault here for your OS: <https://www.vaultproject.io/downloads.html>
* Launch 'vault' executable to see if the usage displays:
  
      > vault
      usage: vault [-version] [-help] <command> [args]
      
      Common commands:
          delete           Delete operation on secrets in Vault
          path-help        Look up the help for a path
          read             Read data or secrets from Vault
          renew            Renew the lease of a secret
          revoke           Revoke a secret.
          server           Start a Vault server
          status           Outputs status of whether Vault is sealed and if HA mode is enabled
          unwrap           Unwrap a wrapped secret
          write            Write secrets or configuration into Vault
      
      All other commands:
          audit-disable    Disable an audit backend
          audit-enable     Enable an audit backend
          audit-list       Lists enabled audit backends in Vault
          auth             Prints information about how to authenticate with Vault
          auth-disable     Disable an auth provider
          auth-enable      Enable a new auth provider
          capabilities     Fetch the capabilities of a token on a given path
          generate-root    Generates a new root token
          init             Initialize a new Vault server
          key-status       Provides information about the active encryption key
          list             List data or secrets in Vault
          mount            Mount a logical backend
          mount-tune       Tune mount configuration parameters
          mounts           Lists mounted backends in Vault
          policies         List the policies on the server
          policy-delete    Delete a policy from the server
          policy-write     Write a policy to the server
          rekey            Rekeys Vault to generate new unseal keys
          remount          Remount a secret backend to a new path
          rotate           Rotates the backend encryption key used to persist data
          seal             Seals the Vault server
          ssh              Initiate an SSH session
          step-down        Force the Vault node to give up active duty
          token-create     Create a new auth token
          token-lookup     Display information about the specified token
          token-renew      Renew an auth token if there is an associated lease
          token-revoke     Revoke one or more auth tokens
          unmount          Unmount a secret backend
          unseal           Unseals the Vault server
          version          Prints the Vault version
  
* Launch the server in dev mode:
  
      > ./vault server -dev
  
* When launching, two very important data displays:
  * The server address,
  * The root token.
* The unseal key is also very important, but not in dev mode (in dev mode, Vault
  is unsealed by default).
* In another shell session, check that the server is running and is ok:
  
      > export VAULT_ADDR='http://127.0.0.1:8200'
      > vault status
  
* Play with the CRUD API:
  * Write a secret:
    
        > vault write secret/mysecret value=CloudCornerSecret
    
  * Read a secret
    
        > vault read secret/mysecret
    
  * Delete a secret
    
        > vault delete secret/mysecret
    
* Some tips to write secrets securely:
  * Write a file content as a secret (mode secure than command line arguments,
    safe from Shell history, very useful for SSH keys):

        > vault write secret/myPrivateKey value=@/home/cornerguy/.ssh/id_rsa
    
  * Write a password / passphrase that exists only in your head without shell
    history, without file, without any uncrypted write:

        > read -s myvar && echo $myvar | tr -d '\n' | ./vault write secret/mySecret value=- && unset myvar
    
* Other important points we have no time to play with, but you should know:
  * Learn to seal/unseal in production mode,
  * Learn how to setup TLS communication with Vault (need to generate a
    certificate),
  * Learn about secret backends and dynamic secrets,
  * Learn about leases and revocations,
  * The most difficult part: learn about authentication and ACLs.
  * All these points are introduced in the Vault [Getting Started][VAULT_START]
    sections on the Vault web site.

### Playing with the Vault HTTP API

In this example, we use the preceding server in dev mode, so there is no TLS, no
certificate and no authentication. In real life, you'll have to deal with all of
this.

* Take a tool like Postman or 'curl'.
* Write a secret in Vault using the command line, as seen in the preceding
  chapter:

      > vault write secret/mysecret "value=Hello Cloud Corner's guys."
  
* Read it with a HTTP request:
  * Postman:
    * GET request: `http://127.0.0.1:8200/v1/secret/mysecret`
    * HTTP Headers:
      * X-Vault-Token: \<your root token as given by Vault when you launched it\>
  * Curl:
    
        > export VAULT_TOKEN=<your root token as given by Vault when you launched it>
        > curl -X GET -H "X-Vault-Token: $VAULT_TOKEN" http://127.0.0.1:8200/v1/secret/mysecret
    
  * Do you know the ['jq' tool][JQ]?
    
        > curl -s -X GET -H "X-Vault-Token: $VAULT_TOKEN" http://127.0.0.1:8200/v1/secret/mysecret | jq
        > curl -s -X GET -H "X-Vault-Token: $VAULT_TOKEN" http://127.0.0.1:8200/v1/secret/mysecret | jq -r .data.value


### Alternatives

Vault has the immense advantage to be Cloud-agnostic. You can design portable
Cloud architectures with it. But if you don't care about portability and want
to go Cloud-native, AWS has the [KMS][AMAZON_KMS] service as alternative, with
the advantage of using hardware security
([HSM: Hardware Security Module][HSM_DEFINITION]).


A full example with a real application
--------------------------------------




[VAULT]:          https://www.vaultproject.io/                                   "Vault project."
[VAULT_DOCKER]:   https://store.docker.com/images/vault                          "Vault official docker image."
[VAULT_SOURCES]:  https://github.com/hashicorp/vault                             "Vault sources repository."
[VAULT_START]:    https://www.vaultproject.io/intro/getting-started/install.html "Vault getting started documentation."
[JQ]:             https://stedolan.github.io/jq/                                 "JQ official web site."
[AMAZON_KMS]:     https://aws.amazon.com/kms/                                    "Amazon Key Management Service."
[HSM_DEFINITION]: https://en.wikipedia.org/wiki/Hardware_security_module         "Hardware Security Module definition on Wikipedia."
