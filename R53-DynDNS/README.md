# Usage

I wanted a quick and dirty script for dynamic DNS via AWS Route53. I didn't want this dependent on anything other than a crontab entry and a remote endpoint for verifying my IP.

## Setup

You can do this one of two ways:

* Create a hosted zone specifically for this script that has an IAM user with a policy to only allow access to that hosted zone.
* Live dangerously and let an IAM user control your hosted zone that contains all your other DNS records.

My steps will cover the first approach assuming you want a subdomain called `server.domain.com` under your primary `domain.com` DNS configuration. Substitute `server.domain.com` and `domain.com` with yours for this.

### AWS Configuration

1. Create a hosted zone for your DNS record, `server.domain.com`, and note the hosted zone ID.
2. Copy the NS records in that newly created hosted zone.
3. In your primary hosted zone, `domain.com`, add an NS record named `server.domain.com` with the values copied in step 2.
4. Go to Services -> IAM -> Policies
5. Create a new policy and click the JSON tab. Copy the contents of `Policy.json` into it and update Line 22 to replace `ZONEID` with the hosted zone ID for your subdomain created in step 1.
6. Go to Services -> IAM -> Users and create a new user and choose **Programmatic access**.
7. On the Permissions page choose **Attach existing policies directly** and attach the policy created in step 5.
8. Add whatever tags you want, review that it's correct, then create the user.
9. Save the keys in a secure place like [1Password](https://1password.com/) or [KeePass](https://keepass.info/).

### Script Configuration

1. Create a Python virtual environment and install the dependencies.

    `pip install boto3 python-dotenv`

2. Save the `r53.py` and `.env.example` file in the same directory, renaming `.env.example` to `.env`.
3. Update `.env` with the following values:

    ```
    AWS_ACCESS_KEY_ID=<Access Key from Step 9>
    AWS_SECRET_ACCESS_KEY=<Secret Access Key from Step 9>
    AWS_HOSTED_ZONE_ID=<Zone ID from Step 1>
    AWS_HOSTED_ZONE_DOMAIN_NAME=server.domain.com
    AWS_HOSTED_ZONE_DOMAIN_TYPE=A
    AWS_HOSTED_ZONE_DOMAIN_TTL=300
    ```

4. Run the script and it should create the record if it doesn't exist, or update it if it's incorrect.

You can also add a crontab entry for this. The example below runs every 12 hours.

```
0 */12 * * * <virtualenvpath> /path/to/script/r53.py
```

Installed Example:

```
0 */12 * * * /opt/scripts/r53/env/bin/python /opt/scripts/r53/r53.py > /dev/null 2>&1
```
