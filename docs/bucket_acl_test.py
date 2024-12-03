import pytest
from botocore.exceptions import ClientError
from s3_helpers import(
    put_object_and_wait,
)


def outer_merge(a, b):
    # Iterate through the keys in dictionary b
    for key, value in b.items():
        if key in a:
            a[key] = value
            
    return a


# Bucket ACL

## test invalid arguments for acl
@pytest.mark.parametrize("acl_name", [
    "errado", "''"
]) 
def test_invalid_put_bucket_acl(s3_client,existing_bucket_name, acl_name):
    try:
        s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)
        pytest.fail("Valid acl arg inputed, test failed")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'InvalidArgument'


## Try to create acl with different permissions
@pytest.mark.parametrize("acl_name", [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read',
]) 
def test_put_bucket_acl(s3_client, existing_bucket_name, acl_name):
    response =  s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)

    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


# ACL -> ListObjects, ReadObject, WriteObject, ListAcl, ReadAcl, WriteAcl


number_profiles = 2

methods = {
    'list_objects_v2': {"Bucket": 'my-bucket'},
    'put_object': {"Bucket": 'my-bucket', "Key": 'my-key', "Body": 'content'},
    'get_object': {"Bucket": 'my-bucket', "Key": 'my-key'},
    'get_bucket_acl': {"Bucket": 'my-bucket'},
    'put_bucket_acl': {"Bucket": 'my-bucket', "ACL": 'public-read'},
}

expected_results = {
    'private': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied', 'NoSuchBucket'],
    'authenticated-read':[200, 'AccessDenied', 'AccessDenied', 'AccessDenied', 'NoSuchBucket'],
    'public-read':[200, 'AccessDenied', 'AccessDenied', 'AccessDenied', 'NoSuchBucket'],
    'public-read-write':[200, 200, 200, 'AccessDenied', 'NoSuchBucket'],
}


@pytest.mark.parametrize(
    "multiple_s3_clients, bucket_with_acl_one_object, methods, expected", 
    [({"number_profiles": number_profiles}, {"acl": acl}, methods, expected_results[acl]) for acl in expected_results], 
    indirect=['multiple_s3_clients', 'bucket_with_acl_one_object']
)


def test_bucket_acl(multiple_s3_clients, bucket_with_acl_one_object, methods, expected):
    client = multiple_s3_clients[1]
    bucket_name, obj_key = bucket_with_acl_one_object
    
    results = []

    for m, a in methods.items():
        a = outer_merge(a, {'Bucket': bucket_name, 'Key': obj_key})
        method = getattr(client, m)
        try:
            response = method(**a)
            results.append(response['ResponseMetadata']['HTTPStatusCode'])
        except ClientError as e:
            results.append(e.response['Error']['Code'])
 
        
    assert expected == results
        