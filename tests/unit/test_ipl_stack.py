import aws_cdk as core
import aws_cdk.assertions as assertions

from ipl.ipl_stack import IplStack


def test_stack_creates():
    app = core.App()
    stack = IplStack(app, "ipl")
    template = assertions.Template.from_stack(stack)
