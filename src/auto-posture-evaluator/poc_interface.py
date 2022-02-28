from abc import ABC
from datetime import datetime
from typing import List


class TestReport(ABC):
    def __init__(self, provider: str,
                 service: str,
                 account: str,
                 name: str,
                 start_time: datetime,
                 end_time: datetime,
                 item: str,
                 item_type: str,
                 passed: bool,
                 **kwargs):
        self.provider = provider
        self.service = service
        self.account = account
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.item = item
        self.item_type = item_type
        self.passed = passed
        self.additional_data = kwargs


class TesterInterface:
    def declare_tested_service(self) -> str:
        pass

    def declare_tested_provider(self) -> str:
        pass

    def run_tests(self) -> List["TestReport"]:
        pass
