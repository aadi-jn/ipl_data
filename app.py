#!/usr/bin/env python3
import os

import aws_cdk as cdk

from ipl.ipl_stack import IplStack


app = cdk.App()
IplStack(app, "IplStack",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region="ap-south-1"),
)

app.synth()
