from datetime import datetime
from typing import List

import boto3

from poc_interface import TesterInterface, TestReport


def _return_default_port_on_rds_engines(db_engine):
    if 'mysql' in db_engine.lower() or 'aurora' in db_engine.lower() or 'maria' in db_engine.lower():
        return 3306
    elif 'postgres' in db_engine.lower():
        return 5432
    elif 'oracle' in db_engine.lower():
        return 1521
    elif 'sql' in db_engine.lower():
        return 1433
    return


class Tester(TesterInterface):
    def __init__(self):
        self.aws_rds_client = boto3.client('rds')
        self.cache = {}
        self.user_id = boto3.client('sts').get_caller_identity().get('UserId')
        self.account_arn = boto3.client('sts').get_caller_identity().get('Arn')
        self.account_id = boto3.client('sts').get_caller_identity().get('Account')
        self.rds_instances = self.aws_rds_client.describe_db_instances()
        self.rds_snapshots = self.aws_rds_client.describe_db_snapshots()
        self.start_time = None

    def declare_tested_service(self) -> str:
        return 'rds'

    def declare_tested_provider(self) -> str:
        return 'aws'

    def run_tests(self) -> List["TestReport"]:
        self.start_time = datetime.now
        return self.detect_rds_instance_encrypted() + \
               self.detect_rds_instance_not_publicly_accessible() + \
               self.detect_rds_instance_not_using_default_port() + \
               self.detect_rds_snapshot_not_publicly_accessible()

    def _append_rds_test_result(self, rds, test_name: str, passed: bool):
        return TestReport(
            provider=self.declare_tested_provider(),
            service=self.declare_tested_service(),
            account=self.account_id,
            name=test_name,
            start_time=self.start_time,
            end_time=datetime.now(),
            item=rds['DBInstanceIdentifier'],
            item_type="rds_db_instance",
            passed=passed,
            user=self.user_id,
            account_arn=self.account_arn
        )

    def _append_rds_snap_test_result(self, rds, test_name: str, passed: bool):
        return TestReport(
            provider=self.declare_tested_provider(),
            service=self.declare_tested_service(),
            account=self.account_id,
            name=test_name,
            start_time=self.start_time,
            end_time=datetime.now(),
            item=rds['DBInstanceIdentifier'],
            item_type="rds_db_instance",
            passed=passed,
            user=self.user_id,
            account_arn=self.account_arn
        )

    def _fetch_snapshot_metadata(self, snapshot_identifier):
        return self.aws_rds_client.describe_db_snapshot_attributes(DBSnapshotIdentifier=snapshot_identifier)

    def detect_rds_instance_encrypted(self) -> List["TestReport"]:
        test_name = "encrypted_rds_db_instances"
        result = []
        for rds in self.rds_instances['DBInstances']:
            if not rds['StorageEncrypted']:
                result.append(self._append_rds_test_result(rds, test_name, passed=False))
            else:
                result.append(self._append_rds_test_result(rds, test_name, passed=True))
        return result

    def detect_rds_instance_not_publicly_accessible(self) -> List["TestReport"]:
        test_name = "not_publicly_accessible_rds_db_instances"
        result = []
        for rds in self.rds_instances['DBInstances']:
            if rds['PubliclyAccessible']:
                result.append(self._append_rds_test_result(rds, test_name, passed=False))
            else:
                result.append(self._append_rds_test_result(rds, test_name, passed=True))
        return result

    def detect_rds_instance_not_using_default_port(self) -> List["TestReport"]:
        test_name = "rds_db_instances_not_using_default_port"
        result = []
        for rds in self.rds_instances['DBInstances']:
            default_db_engine_port = _return_default_port_on_rds_engines(rds['Engine'])
            if default_db_engine_port == rds['Endpoint']['Port']:
                result.append(self._append_rds_test_result(rds, test_name, passed=False))
            else:
                result.append(self._append_rds_test_result(rds, test_name, passed=True))
        return result

    def detect_rds_snapshot_not_publicly_accessible(self) -> List["TestReport"]:
        test_name = "rds_snapshot_not_publicly_accessible"
        result = []
        for rds_snap in self.rds_snapshots['DBSnapshots']:
            issue_found = False
            snap_metadata = self._fetch_snapshot_metadata(rds_snap['DBSnapshotIdentifier'])
            for snap_meta in snap_metadata['DBSnapshotAttributesResult']['DBSnapshotAttributes']:
                if snap_meta['AttributeName'] == 'restore' and 'all' in snap_meta['AttributeValues']:
                    result.append(self._append_rds_snap_test_result(rds_snap, test_name, passed=False))
                    issue_found = True
            if not issue_found:
                result.append(self._append_rds_snap_test_result(rds_snap, test_name, passed=True))
        return result
