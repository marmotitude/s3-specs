# Object Locking

A funcionalidade de **Object Locking** no S3 permite bloquear versões individuais de objetos, 
impedindo sua modificação ou exclusão durante um período especificado.

Isto é usado para garantir **conformidade** (compliance) com requisitos legais ou simplesmente
garantir uma proteção extra contra modificações ou exclusão.

## Exemplos


```python
config = "../params/aws-east-1.yaml"
docs_dir = "."
```


```python
# Parameters
config = "params/aws-west-1.yaml"
docs_dir = "docs"

```


```python
import boto3
import botocore
import pytest
import logging
from datetime import datetime, timedelta
from s3_helpers import (
    run_example,
    cleanup_old_buckets,
    generate_unique_bucket_name,
    create_bucket_and_wait,
    put_object_and_wait,
    teardown_versioned_bucket_with_lock_config,
)
```

### Configuração de Object Locking em Bucket Versionado

A configuração de uma trava em um bucket deve ser feita em um bucket com versionamento habilitado
e é setada com o comando **put_object_lock_configuration**

Para os exemplos abaixo, vamos utilizar um bucket versionado com dois objetos, um de antes da entrada
da configuração de lock e outro de depois, quando uma regra de retenção padráo já foi definida.

Isto facilitará a demonstração de que regras de retenção do buckect só se aplicam às novas versões de objetos.


```python
@pytest.fixture
def versioned_bucket_with_lock_config(s3_client, test_params):
    base_name = "versioned-bucket-with-lock"
    lock_mode = test_params["lock_mode"]


    # Clean up old buckets, from past days (we are using 1 day retention, so if the lock mode is not
    # GOVERNANCE, we are not able to teardown immediately after the test)
    cleanup_old_buckets(s3_client, base_name)

    # Generate a unique name and create a versioned bucket
    bucket_name = generate_unique_bucket_name(base_name=base_name)
    create_bucket_and_wait(s3_client, bucket_name)
    s3_client.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"}
    )

    # Upload an initial object before lock configuration
    first_object_key = "pre-lock-object.txt"
    pre_lock_content = b"Content for object before lock configuration"
    first_version_id = put_object_and_wait(s3_client, bucket_name, first_object_key, pre_lock_content)

    # Configure Object Lock on the bucket
    lock_config = {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": lock_mode,
                "Days": 1
            }
        }
    }
    response = s3_client.put_object_lock_configuration(
        Bucket=bucket_name,
        ObjectLockConfiguration=lock_config
    )
    response_status = response["ResponseMetadata"]["HTTPStatusCode"]
    assert response_status == 200, "Expected HTTPStatusCode 200 for successful lock configuration."
    logging.info(f"Bucket '{bucket_name}' locked with mode {lock_mode}. Status: {response_status}")

    # Upload another object after lock configuration
    second_object_key = "post-lock-object.txt"
    post_lock_content = b"Content for object after lock configuration"
    second_version_id = put_object_and_wait(s3_client, bucket_name, second_object_key, post_lock_content)
    logging.info(f"Uploaded post-lock object: {bucket_name}/{second_object_key} with version ID {second_version_id}")

    # Yield details for tests to use
    yield bucket_name, first_object_key, second_object_key, first_version_id, second_version_id, pre_lock_content, post_lock_content

    # cleanup whatever is possible given the lock mode
    teardown_versioned_bucket_with_lock_config(s3_client, bucket_name, lock_mode)
```

### Remoção de objetos em um bucket com lock configuration

#### Simple Delete
Em um bucket versionado, um delete simples sem o id da versão do objeto não exclui dados, apenas
adiciona um marcador (delete marker), esta operação pode ocorrer independentemente se o bucket
possui ou não uma configuração de locking.


```python
def test_simple_delete_with_lock(versioned_bucket_with_lock_config, s3_client):
    bucket_name, first_object_key, second_object_key, _, _, _, _ = versioned_bucket_with_lock_config

    # Simple delete (without specifying VersionId), adding a delete marker
    logging.info(f"Attempting simple delete (delete marker) on pre-lock object: {bucket_name}/{first_object_key}")
    response = s3_client.delete_object(Bucket=bucket_name, Key=first_object_key)
    response_status = response["ResponseMetadata"]["HTTPStatusCode"]
    assert response_status == 204, "Expected HTTPStatusCode 204 for successful simple delete."
    logging.info(f"Simple delete (delete marker) added successfully for object '{first_object_key}'.")

    # Simple delete the locked (second object)
    logging.info(f"Attempting simple delete (delete marker) on object: {bucket_name}/{second_object_key}")
    response = s3_client.delete_object(Bucket=bucket_name, Key=second_object_key)
    response_status = response["ResponseMetadata"]["HTTPStatusCode"]
    assert response_status == 204, "Expected HTTPStatusCode 204 for successful simple delete."
    logging.info(f"Simple delete (delete marker) added successfully for object '{second_object_key}'.")

run_example(__name__, "locking", "test_simple_delete_with_lock", config=config, docs_dir=docs_dir)
```

    
    docs/locking_test.py::test_simple_delete_with_lock 

    
    -------------------------------- live log setup --------------------------------
    INFO     botocore.credentials:credentials.py:1278 Found credentials in shared credentials file: ~/.aws/credentials


    INFO     root:s3_helpers.py:58 Bucket 'versioned-bucket-with-lock-4d207c' confirmed as created.


    INFO     root:s3_helpers.py:79 Object 'pre-lock-object.txt' in bucket 'versioned-bucket-with-lock-4d207c' confirmed as uploaded.


    INFO     root:locking_test.py:92 Bucket 'versioned-bucket-with-lock-4d207c' locked with mode GOVERNANCE. Status: 200


    INFO     root:s3_helpers.py:79 Object 'post-lock-object.txt' in bucket 'versioned-bucket-with-lock-4d207c' confirmed as uploaded.


    INFO     root:locking_test.py:98 Uploaded post-lock object: versioned-bucket-with-lock-4d207c/post-lock-object.txt with version ID c.5j_r8KivShPFrxBZ3diqC.nwIssoKf


    -------------------------------- live log call ---------------------------------
    INFO     root:locking_test.py:119 Attempting simple delete (delete marker) on pre-lock object: versioned-bucket-with-lock-4d207c/pre-lock-object.txt


    INFO     root:locking_test.py:123 Simple delete (delete marker) added successfully for object 'pre-lock-object.txt'.


    INFO     root:locking_test.py:126 Attempting simple delete (delete marker) on object: versioned-bucket-with-lock-4d207c/post-lock-object.txt


    INFO     root:locking_test.py:130 Simple delete (delete marker) added successfully for object 'post-lock-object.txt'.


    PASSED

    
    ------------------------------ live log teardown -------------------------------
    INFO     root:s3_helpers.py:112 Deleting objects in 'versioned-bucket-with-lock-4d207c' with BypassGovernanceRetention.


    INFO     root:s3_helpers.py:132 Deleting bucket: versioned-bucket-with-lock-4d207c


    
    
    ============================== 1 passed in 8.51s ===============================


#### Permanent Delete

Já um delete permanente, que específica a versão do objeto, é afetado pela configuração de
locking e retorna um erro de `AccessDenied` se for aplicado a um objeto que tenha sido criado 
**após** a entrada da configuração e que esteja ainda em período de retenção.

Versões de objetos anteriores à configuração de uma retenção padrão podem ser deletadas 
permanentemente.


```python
def test_delete_object_after_locking(versioned_bucket_with_lock_config, s3_client):
    bucket_name, first_object_key, second_object_key, first_version_id, second_version_id, _, _ = versioned_bucket_with_lock_config

    # Perform a permanent delete on the pre-lock object version (should succeed due to no retention)
    delete_response = s3_client.delete_object(Bucket=bucket_name, Key=first_object_key, VersionId=first_version_id)
    delete_response_status = delete_response["ResponseMetadata"]["HTTPStatusCode"]
    logging.info(f"delete response status: {delete_response_status}")

    # Attempt to permanently delete the post-lock object version and expect failure
    with pytest.raises(botocore.exceptions.ClientError) as exc_info:
        s3_client.delete_object(Bucket=bucket_name, Key=second_object_key, VersionId=second_version_id)

    # Verify AccessDenied for the newly uploaded locked object
    error_code = exc_info.value.response['Error']['Code']
    assert error_code == "AccessDenied", f"Expected AccessDenied, got {error_code}"
    logging.info(f"Permanent deletion blocked as expected for new locked object '{second_object_key}' with version ID {second_version_id}")

run_example(__name__, "locking", "test_delete_object_after_locking", config=config, docs_dir=docs_dir)
```

    
    docs/locking_test.py::test_delete_object_after_locking 

    
    -------------------------------- live log setup --------------------------------
    INFO     botocore.credentials:credentials.py:1278 Found credentials in shared credentials file: ~/.aws/credentials


    INFO     root:s3_helpers.py:58 Bucket 'versioned-bucket-with-lock-a23728' confirmed as created.


    INFO     root:s3_helpers.py:79 Object 'pre-lock-object.txt' in bucket 'versioned-bucket-with-lock-a23728' confirmed as uploaded.


    INFO     root:locking_test.py:92 Bucket 'versioned-bucket-with-lock-a23728' locked with mode GOVERNANCE. Status: 200


    INFO     root:s3_helpers.py:79 Object 'post-lock-object.txt' in bucket 'versioned-bucket-with-lock-a23728' confirmed as uploaded.


    INFO     root:locking_test.py:98 Uploaded post-lock object: versioned-bucket-with-lock-a23728/post-lock-object.txt with version ID WqHec111MzwGb1F2AnYcHTrRVA6jmJic


    -------------------------------- live log call ---------------------------------
    INFO     root:locking_test.py:151 delete response status: 204


    INFO     root:locking_test.py:160 Permanent deletion blocked as expected for new locked object 'post-lock-object.txt' with version ID WqHec111MzwGb1F2AnYcHTrRVA6jmJic


    PASSED

    
    ------------------------------ live log teardown -------------------------------
    INFO     root:s3_helpers.py:112 Deleting objects in 'versioned-bucket-with-lock-a23728' with BypassGovernanceRetention.


    INFO     root:s3_helpers.py:132 Deleting bucket: versioned-bucket-with-lock-a23728


    
    
    ============================== 1 passed in 8.02s ===============================


### Conferindo a existência de uma configuração de tranca no bucket

É possível consultar se um **bucket** possui uma configuração de lock por meio do comando
**get_object_lock_configuration**


```python
def test_verify_object_lock_configuration(versioned_bucket_with_lock_config, s3_client, test_params):
    bucket_name, _, _, _, _, _, _ = versioned_bucket_with_lock_config
    lock_mode = test_params["lock_mode"]

    # Retrieve and verify the applied bucket-level Object Lock configuration
    logging.info("Retrieving Object Lock configuration from bucket...")
    applied_config = s3_client.get_object_lock_configuration(Bucket=bucket_name)
    assert applied_config["ObjectLockConfiguration"]["ObjectLockEnabled"] == "Enabled", "Expected Object Lock to be enabled."
    assert applied_config["ObjectLockConfiguration"]["Rule"]["DefaultRetention"]["Mode"] == lock_mode, f"Expected retention mode to be {lock_mode}."
    assert applied_config["ObjectLockConfiguration"]["Rule"]["DefaultRetention"]["Days"] == 1, "Expected retention period of 1 day."
    logging.info("Verified that Object Lock configuration was applied as expected.")
run_example(__name__, "locking", "test_verify_object_lock_configuration", config=config, docs_dir=docs_dir)
```

    
    docs/locking_test.py::test_verify_object_lock_configuration 

    
    -------------------------------- live log setup --------------------------------
    INFO     botocore.credentials:credentials.py:1278 Found credentials in shared credentials file: ~/.aws/credentials


    INFO     root:s3_helpers.py:58 Bucket 'versioned-bucket-with-lock-767203' confirmed as created.


    INFO     root:s3_helpers.py:79 Object 'pre-lock-object.txt' in bucket 'versioned-bucket-with-lock-767203' confirmed as uploaded.


    INFO     root:locking_test.py:92 Bucket 'versioned-bucket-with-lock-767203' locked with mode GOVERNANCE. Status: 200


    INFO     root:s3_helpers.py:79 Object 'post-lock-object.txt' in bucket 'versioned-bucket-with-lock-767203' confirmed as uploaded.


    INFO     root:locking_test.py:98 Uploaded post-lock object: versioned-bucket-with-lock-767203/post-lock-object.txt with version ID jV8ikJFMq01QhpBPjuPdR81IKLgpaqD0


    -------------------------------- live log call ---------------------------------
    INFO     root:locking_test.py:177 Retrieving Object Lock configuration from bucket...


    INFO     root:locking_test.py:182 Verified that Object Lock configuration was applied as expected.


    PASSED

    
    ------------------------------ live log teardown -------------------------------
    INFO     root:s3_helpers.py:112 Deleting objects in 'versioned-bucket-with-lock-767203' with BypassGovernanceRetention.


    INFO     root:s3_helpers.py:132 Deleting bucket: versioned-bucket-with-lock-767203


    
    
    ============================== 1 passed in 8.30s ===============================


### Conferindo a politica de retenção de objetos específicos

É possível consultar as regras de retenção para objetos novos, criados após a configuração de
uma regra padrão por meio dos comando **get_object_retention** e **head_object**.
Objetos pre-existentes, de antes da configuração do bucket não exibem estas informações.


```python
def test_verify_object_retention(versioned_bucket_with_lock_config, s3_client, test_params):
    bucket_name, first_object_key, second_object_key, _, _, _, _ = versioned_bucket_with_lock_config
    lock_mode = test_params["lock_mode"]

    # Objects from before the config don't have retention data
    logging.info(f"Fetching data of the pre-existing object with a head request...")
    head_response = s3_client.head_object(Bucket=bucket_name, Key=first_object_key)
    assert not head_response.get('ObjectLockRetainUntilDate'), 'Expected lock ending date to be unset.'
    assert not head_response.get('ObjectLockMode'), 'Expected lock mode to be unset'
    logging.info(f"Retention data not present on the pre-existing object as expected.")

    # Use get_object_retention to check object-level retention details
    logging.info("Retrieving object retention details...")
    retention_info = s3_client.get_object_retention(Bucket=bucket_name, Key=second_object_key)
    assert retention_info["Retention"]["Mode"] == lock_mode, f"Expected object lock mode to be {lock_mode}."
    logging.info(f"Retention verified as applied with mode {retention_info['Retention']['Mode']} "
          f"and retain until {retention_info['Retention']['RetainUntilDate']}.")

    # Use head_object to check retention details
    logging.info("Fetching data of the new object with a head request...")
    head_response = s3_client.head_object(Bucket=bucket_name, Key=second_object_key)
    assert head_response['ObjectLockRetainUntilDate'], 'Expected lock ending date to be present.'
    assert head_response['ObjectLockMode'] == lock_mode, f"Expected lock mode to be {lock_mode}"
    logging.info(f"Retention verified as applied with mode {head_response['ObjectLockMode']} "
          f"and retain until {head_response['ObjectLockRetainUntilDate']}.")
run_example(__name__, "locking", "test_verify_object_retention", config=config, docs_dir=docs_dir)
```

    
    docs/locking_test.py::test_verify_object_retention 

    
    -------------------------------- live log setup --------------------------------
    INFO     botocore.credentials:credentials.py:1278 Found credentials in shared credentials file: ~/.aws/credentials


    INFO     root:s3_helpers.py:58 Bucket 'versioned-bucket-with-lock-d16577' confirmed as created.


    INFO     root:s3_helpers.py:79 Object 'pre-lock-object.txt' in bucket 'versioned-bucket-with-lock-d16577' confirmed as uploaded.


    INFO     root:locking_test.py:92 Bucket 'versioned-bucket-with-lock-d16577' locked with mode GOVERNANCE. Status: 200


    INFO     root:s3_helpers.py:79 Object 'post-lock-object.txt' in bucket 'versioned-bucket-with-lock-d16577' confirmed as uploaded.


    INFO     root:locking_test.py:98 Uploaded post-lock object: versioned-bucket-with-lock-d16577/post-lock-object.txt with version ID GZkquKr2ezFC2RCJXMyMEesMUH2jN_0N


    -------------------------------- live log call ---------------------------------
    INFO     root:locking_test.py:198 Fetching data of the pre-existing object with a head request...


    INFO     root:locking_test.py:202 Retention data not present on the pre-existing object as expected.


    INFO     root:locking_test.py:205 Retrieving object retention details...


    INFO     root:locking_test.py:208 Retention verified as applied with mode GOVERNANCE and retain until 2024-10-31 01:40:16.885000+00:00.


    INFO     root:locking_test.py:212 Fetching data of the new object with a head request...


    INFO     root:locking_test.py:216 Retention verified as applied with mode GOVERNANCE and retain until 2024-10-31 01:40:16.885000+00:00.


    PASSED

    
    ------------------------------ live log teardown -------------------------------
    INFO     root:s3_helpers.py:112 Deleting objects in 'versioned-bucket-with-lock-d16577' with BypassGovernanceRetention.


    INFO     root:s3_helpers.py:132 Deleting bucket: versioned-bucket-with-lock-d16577


    
    
    ============================== 1 passed in 8.26s ===============================


### Configuração de Object Locking em Bucket Não-Versionado

Para que o Object Lock funcione, o bucket deve estar configurado com **versionamento** habilitado,
pois o bloqueio opera no nível de versão. Aplicar uma configuração de object locking em um
bucket comum (não versionado), deve retornar um erro do tipo `InvalidBucketState`.


```python
def test_configure_bucket_lock_on_regular_bucket(s3_client, existing_bucket_name, test_params):
    lock_mode = test_params["lock_mode"]
    # Set up Bucket Lock configuration
    bucket_lock_config = {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": lock_mode,
                "Days": 1
            }
        }
    }

    # Try applying the Object Lock configuration and expect an error
    logging.info("Attempting to apply Object Lock configuration on a non-versioned bucket...")
    with pytest.raises(s3_client.exceptions.ClientError) as exc_info:
        s3_client.put_object_lock_configuration(
            Bucket=existing_bucket_name,
            ObjectLockConfiguration=bucket_lock_config
        )

    # Verify that the correct error was raised
    assert "InvalidBucketState" in str(exc_info.value), "Expected InvalidBucketState error not raised."
    logging.info("Correctly raised InvalidBucketState error for non-versioned bucket.")

run_example(__name__, "locking", "test_configure_bucket_lock_on_regular_bucket", config=config, docs_dir=docs_dir)
```

    
    docs/locking_test.py::test_configure_bucket_lock_on_regular_bucket 

    
    -------------------------------- live log setup --------------------------------
    INFO     botocore.credentials:credentials.py:1278 Found credentials in shared credentials file: ~/.aws/credentials


    INFO     root:s3_helpers.py:58 Bucket 'existing-bucket-fc86cf' confirmed as created.


    -------------------------------- live log call ---------------------------------
    INFO     root:locking_test.py:242 Attempting to apply Object Lock configuration on a non-versioned bucket...


    INFO     root:locking_test.py:251 Correctly raised InvalidBucketState error for non-versioned bucket.


    PASSED

    
    ------------------------------ live log teardown -------------------------------
    INFO     root:s3_helpers.py:36 Bucket 'existing-bucket-fc86cf' confirmed as deleted.


    
    
    ============================== 1 passed in 3.64s ===============================


## Referências
- [Amazon S3 Object Lock Overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html) - Visão Geral sobre Object Lock no Amazon S3
- [put_object_lock_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object_lock_configuration.html) - Configurar Object Lock em um bucket
- [get_object_lock_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object_lock_configuration.html) - Recuperar configuração de Object Lock de um bucket
- [Why can I delete objects even after I turned on Object Lock for my Amazon S3 bucket?](https://repost.aws/knowledge-center/s3-object-lock-delete) - Detalhamento de como deletar e gerenciar retenção e legal hold em objetos S3