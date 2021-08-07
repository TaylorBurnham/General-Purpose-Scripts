#!/usr/bin/env python3
import os
import sys
import boto3
import logging
from requests import get
from requests.exceptions import RequestException
from dotenv import load_dotenv


def get_public_ip():
    try:
        response = get('https://ifconfig.me/ip')
        ip = response.content.decode()
    except RequestException:
        ip = None
    return ip


class Route53:
    def __init__(self):
        self.client = boto3.client('route53')

    def get_rrsets(self, zone_id):
        response = self.client.list_resource_record_sets(
            HostedZoneId=zone_id
        )
        return response.get('ResourceRecordSets')

    def get_rrset_for_domain(self, zone_id, domain_name, domain_type):
        rrsets = self.get_rrsets(zone_id)
        rrset = next(filter(
            lambda x: (
                x['Name'] == domain_name and
                x['Type'] == domain_type
            ), rrsets), None)
        return rrset

    def get_rrset_value(self, rrset):
        return rrset.get('ResourceRecords').pop().get('Value')

    def set_rrset_value(self, **kwargs):
        zone_id = kwargs.get('zone_id')
        domain_name = kwargs.get('domain_name')
        domain_type = kwargs.get('domain_type')
        domain_ttl = kwargs.get('domain_ttl')
        domain_value = kwargs.get('ip')
        rrset_batch = {
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": domain_name,
                    "Type": domain_type,
                    "TTL": domain_ttl,
                    "ResourceRecords": [{
                        "Value": domain_value
                    }]
                }
            }]
        }
        response = self.client.change_resource_record_sets(
            HostedZoneId=zone_id, ChangeBatch=rrset_batch
        )
        return response.get('ChangeInfo')


if __name__ == "__main__":
    logger = logging.getLogger()
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
    )
    logger.addHandler(streamHandler)
    logger.level = logging.INFO
    logger.info("Loading Environment Variables")
    # Load the config
    load_dotenv()
    dns_zone_id = os.getenv('AWS_HOSTED_ZONE_ID')
    dns_domain_name = os.getenv('AWS_HOSTED_ZONE_DOMAIN_NAME')
    dns_domain_type = os.getenv('AWS_HOSTED_ZONE_DOMAIN_TYPE')
    dns_domain_ttl = int(os.getenv('AWS_HOSTED_ZONE_DOMAIN_TTL'))
    # Connect to AWS
    logger.info("Connecting to AWS and pulling Records")
    r53 = Route53()
    current_dns = r53.get_rrset_for_domain(
        dns_zone_id, dns_domain_name, dns_domain_type
    )
    if current_dns:
        dns_ip = r53.get_rrset_value(current_dns)
    else:
        logger.info(f"No records found for {dns_domain_name}")
        dns_ip = None
    current_ip = get_public_ip()
    if dns_ip != current_ip:
        logger.info(
            f"Current IP {current_ip} doesn't match {dns_ip}. Updating...")
        response = r53.set_rrset_value(
            zone_id=dns_zone_id, domain_name=dns_domain_name,
            domain_type=dns_domain_type, domain_ttl=dns_domain_ttl,
            ip=current_ip
        )
        response_joined = ", ".join([
            f"{k}: {v}" for k, v in response.items()
        ])
        logger.info(f"Completed Request. Status is: {response_joined}")
    else:
        logger.info(f"DNS for {dns_domain_name} matches. No action taken.")
