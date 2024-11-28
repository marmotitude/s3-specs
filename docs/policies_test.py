import pytest
from botocore.exceptions import ClientError
from s3_helpers import(
    change_policies_json,
)



policy_read ='''{
    "Version": "2012-10-18",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "meu-bucket/*"
        }
    ]
}'''

false_policy = """{
    "Version": "2012-10-18",
    "Statement": [
        {
            ¨¨ dsa
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "vosso-bucket/*"
        }
    ]
}
"""

json_read = """{
    "Version": "2012-10-18",
    "Statement": 
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "teu-bucket/*"
        }
    ]
}
"""

cases = [
    *[(case, "MalformedJSON") for case in ['', 'jason',"''", json_read,false_policy]],
    *[(case, "MalformedPolicy") for case in ['{}','""', policy_read]],
 ]   

@pytest.mark.parametrize('input, expected_error', cases)

# Asserting the possible combinations that are allowed as policy arguments
def test_put_invalid_bucket_policy(s3_client, existing_bucket_name, input, expected_error):

    try:
        s3_client.put_bucket_policy(Bucket=existing_bucket_name, Policy=input)
        pytest.fail("Expected exception not raised")
    except ClientError as e:
        # Assert the error code matches the expected one 
        assert e.response['Error']['Code'] == expected_error



policy_dict = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Deny",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "meu-bucket/*"
        }
    ]
}



@pytest.mark.parametrize('actions', [
    "s3:PutObject",
    "s3:DeleteObject",
    "s3:GetObject",
   ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
])


def test_setup_policies(s3_client, existing_bucket_name, actions, effect = 'Allow'):
    bucket_name = existing_bucket_name

    #given a existent and valid bucket
    policy = change_policies_json(existing_bucket_name, policy_dict, actions, effect)

    try:
        s3_client.put_bucket_policy(Bucket=bucket_name, Policy=policy)
    #except ClientError as e:
    #    assert e.response['Error']['Code'] == "Forbidden"
    except ClientError as e:
        assert e.response['Error']['Code'] == 'BucketNotExists'

    
@pytest.mark.parametrize('bucket_with_policy, expected_output', [
    ({"policy_dict": policy_dict, "actions": "s3:PutObject", "effect": "Deny"}, "403"),
    ({"policy_dict": policy_dict, "actions": "s3:GetObject", "effect": "Deny"}, "403"),
    ({"policy_dict": policy_dict, "actions": "s3:DeleteObject", "effect": "Deny"}, "403")
], indirect = ['bucket_with_policy'])
## secure that there are object to be deleted and gotten

#add custom json with deny to this test
def test_access_buckets_with_policies(s3_client, bucket_with_policy, expected_output):
    bucket_name = bucket_with_policy
    
    try:
        s3_client.head_bucket(Bucket = bucket_name)
        pytest.fail("Error not raised")
    except ClientError as e:
        assert e.response['Error']['Code'] == expected_output

