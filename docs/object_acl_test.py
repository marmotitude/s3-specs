import pytest
from botocore.exceptions import ClientError
from s3_helpers import (
    put_object_and_wait,
    outer_merge
)

# # OBJECT ACL

## test invalid arguments for acl
def test_invalid_put_object_acl(s3_client, existing_bucket_name, acl_name):
    try:
        s3_client.put_bucket_acl(Bucket = existing_bucket_name, ACL = acl_name)
        pytest.fail("Valid acl arg inputed, test failed")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'InvalidArgument'


## Try to set object acl with invalid permissions
@pytest.mark.parametrize("acl_name", ['batata','""',]) 
def test_invalid_put_object_acl(s3_client, bucket_with_one_object, acl_name):
    bucket_name, object_key, _ = bucket_with_one_object
    try:
        s3_client.put_object_acl(Bucket = bucket_name, ACL = acl_name, Key = object_key)
        pytest.fail("Valid acl argument inputed, test failed")
    except ClientError as e:
        assert e.response['Error']['Code'] == 'InvalidArgument'


## Try to create obj acl with different permissions
@pytest.mark.parametrize("acl_name", [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read',
]) 
def test_put_object_acl(s3_client, bucket_with_one_object, acl_name):
    bucket_name, object_key, _ = bucket_with_one_object
    response =  s3_client.put_object_acl(Bucket = bucket_name, ACL = acl_name, Key = object_key)

    assert response['ResponseMetadata']['HTTPStatusCode'] == 200


## Test the creater profile always has FULL CONTROL of the objects with acl
@pytest.mark.parametrize("bucket_with_one_object_acl", [
    'private',
    'public-read',
    'public-read-write',
    'authenticated-read',
], indirect=True) 
def test_get_object_acl(s3_client, bucket_with_one_object_acl):

    bucket, key, _ = bucket_with_one_object_acl
    response = s3_client.get_object_acl(Bucket=bucket, Key=key)

    assert any([g['Permission'] == "FULL_CONTROL" for g in response['Grants']])



# # Multiple clients tests

number_profiles = 2

# Vars for the tests
methods_input = {
    'list_objects_v2': {"Bucket": 'my-bucket'}, 
    'put_object': {"Bucket": 'my-bucket', "Key": 'my-key', "Body": 'content'},
    'get_object': {"Bucket": 'my-bucket', "Key": 'my-key'},
    'get_bucket_acl': {"Bucket": 'my-bucket'},
    #'put_bucket_acl': {"Bucket": 'my-bucket', "ACL": 'public-read'},
}

acl_permissions = ['private', 'public-read', 'public-read-write', 'authenticated-read', 'bucket-owner-read', 'bucket-owner-full-control', 'log-delivery-write']


expected_results = {
    'list_objects_v2': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],  
    'put_object': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],       
    'get_object': ['AccessDenied', 200, 200, 200],      
    'get_bucket_acl': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],   
    #'put_bucket_acl': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],   
}
# private, public-read, write, read, read-acp, write-acp, full-controll
@pytest.mark.parametrize(
    "multiple_s3_clients, acl_permission, method_args",
    [
        (
            {"number_profiles": number_profiles},  
            acl_permissions,  
            {
                "method": method,  
                "args": args, 
                "expected_results": expected_results[method]
            }
        )
        for method, args in methods_input.items()
    ],
    indirect=['multiple_s3_clients']  # Indicating that 'multiple_s3_clients' is a fixture
)


def test_object_acl(multiple_s3_clients, bucket_with_one_object, acl_permission, method_args):
    s3_owner = multiple_s3_clients[0]
    s3_other = multiple_s3_clients[1] 
    bucket_name, obj_key, _ = bucket_with_one_object
    
    results = []

    for acl in acl_permission:
        s3_owner.put_object_acl(Bucket = bucket_name, ACL = acl, Key=obj_key)
        #Get the arguments of inside of the subdict 
        
        input_method = outer_merge(method_args["args"], {'Bucket': bucket_name, 'Key': obj_key})

        method = getattr(s3_other, method_args["method"])
        
        try:
            response = method(**input_method)
            results.append(response['ResponseMetadata']['HTTPStatusCode'])
        except ClientError as e:
            results.append(e.response['Error']['Code'])
            

    assert results == method_args["expected_results"]
    



expected_results = {
    'list_objects_v2': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],  
    'put_object': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],       
    'get_object': ['AccessDenied', 200, 200, 200],      
    'get_bucket_acl': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],   
    #'put_bucket_acl': ['AccessDenied', 'AccessDenied', 'AccessDenied', 'AccessDenied'],   
}

@pytest.mark.parametrize(
    "multiple_s3_clients, acl_permission, method_args",
    [
        (
            {"number_profiles": number_profiles},  
            acl_permissions,  
            {
                "method": method,  
                "args": args, 
                "expected_results": expected_results[method]
            }
        )
        for method, args in methods_input.items()
    ],
    indirect=['multiple_s3_clients']  # Indicating that 'multiple_s3_clients' is a fixture
)
    
# ## Create 1 object with acl and another without acl and test the behavior of the functions
def test_2_object_acl(multiple_s3_clients, bucket_with_one_object, acl_permission, method_args):
    s3_owner = multiple_s3_clients[0]
    s3_other = multiple_s3_clients[1] 
    
    bucket_name, obj_key, _ = bucket_with_one_object
    obj_key_2 = obj_key + '2'
    content = 'this is the second object'

    #put another object to test the behavior of the fucntions when trying to access the regular one and one with acl, when both exists
    put_object_and_wait(s3_owner, bucket_name, obj_key_2, content)
    
    results = []

    for acl in acl_permission:
        s3_owner.put_object_acl(Bucket = bucket_name, ACL = acl, Key = obj_key)
        #Get the arguments of inside of the subdict 
        
        input_method = outer_merge(method_args["args"], {'Bucket': bucket_name, 'Key': obj_key_2})

        method = getattr(s3_other, method_args["method"])
        
        try:
            response = method(**input_method)
            results.append(response['ResponseMetadata']['HTTPStatusCode'])
        except ClientError as e:
            results.append(e.response['Error']['Code'])

    #Teardown
    s3_owner.delete_object(Bucket=bucket_name, Key=obj_key_2)


    assert results == method_args["expected_results"]
    
