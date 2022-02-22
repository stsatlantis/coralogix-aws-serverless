import asyncio
import importlib
import os
import sys
from abc import ABC
from asyncio import AbstractEventLoop
from datetime import datetime
from typing import List

from grpclib.client import Channel

from model import SecurityReportTestResult, SecurityReportIngestionServiceStub, SecurityReportContext, SecurityReport, \
    SecurityReportTestResultResult
from model.helper import struct_from_dict

testers_module_names = ['testers.example_tester']
for module in testers_module_names:
    importlib.import_module(module)
del module


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


def _to_model(report: TestReport) -> "SecurityReportTestResult":
    additional_data = struct_from_dict(report.additional_data)
    result = SecurityReportTestResultResult.TEST_FAILED
    if report.passed:
        result = SecurityReportTestResultResult.TEST_PASSED
    return SecurityReportTestResult(
        provider=report.provider,
        service=report.service,
        account=report.account,
        name=report.name,
        start_time=report.start_time,
        end_time=report.end_time,
        item=report.item,
        item_type=report.item_type,
        result=result,
        additional_data=additional_data,
    )


class AutoPostureEvaluatorRunnable:
    def __init__(self):
        endpoint = os.environ.get("CORALOGIX_ENDPOINT_HOST")  # eg.: api.coralogix.net
        port = os.environ.get("CORALOGIX_ENDPOINT_PORT", "443")

        self.channel = Channel(host=endpoint, port=int(port), ssl=True)
        self.client = SecurityReportIngestionServiceStub(channel=self.channel)
        self.api_key = os.environ.get('API_KEY')
        self.private_key = os.environ.get('PRIVATE_KEY')
        self.context = SecurityReportContext(
            private_key=self.private_key,
            application_name=os.environ.get('APPLICATION_NAME', 'NO_APP_NAME'),
            subsystem_name=os.environ.get('SUBSYSTEM_NAME', 'NO_SUB_NAME'),
            computer_name="CoralogixServerlessLambda")
        self.tests: List["TesterInterface"] = []
        for tester_module in testers_module_names:
            if "Tester" in sys.modules[tester_module].__dict__:
                self.tests.append(sys.modules[tester_module].__dict__["Tester"])

    async def run_tests(self):
        for i in range(0, len(self.tests)):
            tester = self.tests[i]
            try:
                cur_tester = tester()
                results = cur_tester.run_tests()
            except Exception as exTesterException:
                print("WARN: The tester " + str(testers_module_names[
                                                    i]) + " has crashed with the following exception during 'run_tests()'. SKIPPED: " + str(
                    exTesterException))
                continue

            error_template = "The result object from the tester " + cur_tester.declare_tested_service() + " does not match the required standard"
            if results is None:
                self.channel.close()
                raise Exception(error_template + " (ResultIsNone). CANNOT CONTINUE.")
            if not isinstance(results, list):
                self.channel.close()
                raise Exception(error_template + " (NotArray). CANNOT CONTINUE.")
            else:
                results = list(map(_to_model, results))
                report = SecurityReport(context=self.context, test_results=results)
                try:
                    print("Sending requests", len(results))
                    await self.client.post_security_report(api_key=self.api_key, security_report=report)
                finally:
                    self.channel.close()
        pass


async def main():
    evaluator = AutoPostureEvaluatorRunnable()
    await evaluator.run_tests()


if __name__ == "__main__":
    loop: AbstractEventLoop = asyncio.get_event_loop()
    loop.run_until_complete(main())
