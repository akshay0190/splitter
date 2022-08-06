import aws_cdk as core
import aws_cdk.assertions as assertions

from csv file splitter.csv file splitter_stack import CsvFileSplitterStack

# example tests. To run these tests, uncomment this file along with the example
# resource in csv file splitter/csv file splitter_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CsvFileSplitterStack(app, "csv-file-splitter")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
