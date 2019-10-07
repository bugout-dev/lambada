# lambada
Manage AWS Lambda functions using a Simiotics Function Registry

## Install

```
pip install -U simiotics-lambada
```

## Use

This section lets you try out `lambada` using our
[example `hello` function](./examples/hello/hello.py).

First, export your `SIMIOTICS_FUNCTION_REGISTRY` environment variable. This tells `lambada` which
Simiotics Function Registry to work with. If you do not have a private Simiotics account, you can
use our free, public, and totally open registry:
```
export SIMIOTICS_FUNCTION_REGISTRY=registry-alpha.simiotics.com:7011
```

Make sure that your AWS credentials are available either by exporting `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` or by ensuring that the profile you want to use is `default` in your
AWS credentials file, or by exporting `AWS_PROFILE`. If you are not familiar with AWS
authentication, you can read more here:
https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html

Decide on a key under which you would like to register the `hello` function into the Simiotics
Function Registry. For example:
```
HELLO_KEY=hello-$(date -u +%s)
```

Register the function against the Simiotics Function Registry using `lambada`:
```
lambada register --key $HELLO_KEY \
    --code examples/hello/hello.py \
    --handler hello \
    --requirements examples/hello/requirements.txt
```

Check that the function was successfully registered (if the output of the following command is
empty, there is a problem):
```
lambada list | grep "$HELLO_KEY"
```

Create an AWS IAM role capable of executing the `hello` function and logging to CloudWatch:
```
lambada create_role --key $HELLO_KEY --name iam-lambada-demo
```

Deploy the function as an AWS Lambda:
```
lambada deploy --key $HELLO_KEY --name lambda-lambada-demo
```

This should return an AWS Lambda ARN of the form:
```
arn:aws:lambda:<REGION>:<PROJECT ID>:function:lambda-lambada-demo
```

Now you can invoke the deployed Lambda using the AWS command-line interface:
```
OUTFILE=$(mktemp)
aws lambda invoke --function-name lambda-lambada-demo \
    --payload '{"target": "Sophia"}' \
    $OUTFILE
cat $OUTFILE
rm $OUTFILE
```

To take down the AWS Lambda:
```
lambada down --key $HELLO_KEY
```

This only removes the AWS Lambda. It doesn't delete the IAM role. If you would like to get rid of
that, as well:
```
lambada down --key $HELLO_KEY --teardown
```

Kick back, [enjoy some smooth tunes](https://www.youtube.com/watch?v=csaUvkYOkLY), and let the
Lambdas proliferate.

## Support

If you experience any problems with this tool, please add an issue on this repository.
