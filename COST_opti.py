import boto3

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')

    # Get all EBS snapshots owned by the user
    response = ec2.describe_snapshots(OwnerIds=['self'])

    # Get all running EC2 instance IDs
    instances_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    active_instance_ids = set()

    # Extract all running instance IDs
    for reservation in instances_response['Reservations']:
        for instance in reservation['Instances']:
            active_instance_ids.add(instance['InstanceId'])

    # Iterate through each snapshot
    for snapshot in response['Snapshots']:
        snapshot_id = snapshot['SnapshotId']
        volume_id = snapshot.get('VolumeId')

        if not volume_id:
            # Delete the snapshot if it's not attached to any volume
            try:
                ec2.delete_snapshot(SnapshotId=snapshot_id)
                print(f"Deleted EBS snapshot {snapshot_id} as it was not attached to any volume.")
            except Exception as e:
                print(f"Failed to delete snapshot {snapshot_id}: {e}")
        else:
            # Check if the volume exists and its attachments
            try:
                volume_response = ec2.describe_volumes(VolumeIds=[volume_id])
                volume = volume_response['Volumes'][0]

                # If the volume has no attachments, delete the snapshot
                if not volume['Attachments']:
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        print(f"Deleted EBS snapshot {snapshot_id} as the volume {volume_id} is not attached to any instance.")
                    except Exception as e:
                        print(f"Failed to delete snapshot {snapshot_id}: {e}")

            except ec2.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'InvalidVolume.NotFound':
                    # The volume associated with the snapshot doesn't exist (might have been deleted)
                    try:
                        ec2.delete_snapshot(SnapshotId=snapshot_id)
                        print(f"Deleted EBS snapshot {snapshot_id} as the associated volume {volume_id} was not found.")
                    except Exception as e:
                        print(f"Failed to delete snapshot {snapshot_id}: {e}")
                else:
                    print(f"Error checking volume {volume_id}: {e}")
