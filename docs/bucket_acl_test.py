import pytest
from itertools import product
from botocore.exceptions import ClientError
from s3_helpers import update_existing_keys
import logging

# # Bucket ACL


# ## Bucket ACL tests with 1 client

# test invalid arguments for acl
@pytest.mark.parametrize("acl_name", ["non-existing-acl-name", ""]) 
def test_invalid_put_bucket_acl(s3_client,existing_bucket_name, acl_name):
    try:
        s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)
        pytest.fail("Valid acl argument inputed, test failed")
    except ClientError as e:
        assert e.response['ResponseMetadata']['HTTPStatusCode'] == 400

@pytest.mark.parametrize("acl_name", [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read'
]) 
def test_valid_put_bucket_acl(s3_client, existing_bucket_name, acl_name):
    response = s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)
    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


# ## Bucket ACL tests with 2 authenticated clients (the owner and another user)

# Define bucket- and object-level operations
bucket_operations = ['list_objects_v2', 'get_bucket_acl']
object_operations = ['get_object', 'put_object']

# Define what a second user is allowed to do for each ACL
non_owner_allowed_operations = {
    "authenticated-read": {"bucket": ["list_objects_v2"], "object": ["get_object"]},
    "bucket-owner-full-control": {"bucket": [], "object": []},
    "bucket-owner-read": {"bucket": [], "object": []},
    "log-delivery-write": {"bucket": [], "object": []},
    "private": {"bucket": [], "object": []},
    "public-read": {"bucket": ["list_objects_v2"], "object": ["get_object"]},
    "public-read-write": {
        "bucket": ["list_objects_v2"],
        "object": ["get_object", "put_object"],
    },
}

# Define methods and their default inputs
methods_input = {
    'list_objects_v2': {"Bucket": ''},
    'put_object': {"Bucket": '', "Key": '', "Body": 'content'},
    'get_object': {"Bucket": '', "Key": ''},
    'get_bucket_acl': {"Bucket": ''},
    'put_object_acl': {"Bucket": '', "Key": '', "ACL": ''}, 
    # TODO: uncomment when MagaluCloud fixes the wrong 404 instead of the correct 403
    # 'put_bucket_acl': {"Bucket": '', "ACL": ''},
}

# Generate test cases declaratively
test_cases = [
    (
        acl_name,
        method_name,
        200 if method_name in non_owner_allowed_operations[acl_name]["bucket"]
             or method_name in non_owner_allowed_operations[acl_name]["object"]
        else 403
    )
    for acl_name, method_name in product(non_owner_allowed_operations.keys(), methods_input.keys())
]

# Generate descriptive test IDs
test_ids = [
    f"ACL={acl_name},Method={method_name},Context={'bucket' if method_name in bucket_operations else 'object'},Expected={expected_status_code}"
    for acl_name, method_name, expected_status_code in test_cases
]

# Test ACL permissions with 2 authenticated clients. This covers both bucket-level
# and object-level ACLs, verifying that the second client can only perform operations
# they are explicitly allowed to.
@pytest.mark.parametrize(
    "multiple_s3_clients, acl_name, method_name, expected_status_code",
    [({"number_clients": 2}, acl, method, status) for acl, method, status in test_cases],
    indirect=['multiple_s3_clients'],  # Indicate 'multiple_s3_clients' is a fixture
    ids=test_ids,  # Provide descriptive IDs for the test cases
)
def test_bucket_acl(multiple_s3_clients, bucket_with_one_object, acl_name, method_name, expected_status_code):
    bucket_name, obj_key, _ = bucket_with_one_object

    # Set the bucket-level ACL
    s3_owner = multiple_s3_clients[0]
    s3_owner.put_bucket_acl(Bucket=bucket_name, ACL=acl_name)

    # Set the object-level ACL if required
    if method_name in non_owner_allowed_operations[acl_name]["object"]:
        s3_owner.put_object_acl(Bucket=bucket_name, Key=obj_key, ACL=acl_name)

    # Prepare arguments
    method_kwargs = update_existing_keys(
        methods_input[method_name],
        { "Bucket": bucket_name, "Key": obj_key, "ACL": acl_name }
    )

    # Log prepared arguments and method name
    logging.info(f"method_args: {method_kwargs} method_name: {method_name}")

    # Execute the method
    s3_other = multiple_s3_clients[1]
    method = getattr(s3_other, method_name)

    try:
        response = method(**method_kwargs)
        actual_status_code = response['ResponseMetadata']['HTTPStatusCode']
    except Exception as e:
        actual_status_code = e.response['ResponseMetadata']['HTTPStatusCode'] if hasattr(e, 'response') else 500

    # Assert the result
    assert actual_status_code == expected_status_code, (
        f"ACL: {acl_name}, Method: {method_name}, "
        f"Expected: {expected_status_code}, Actual: {actual_status_code}"
    )
