from requests import get
from socket import gethostbyname
import CloudFlare
import argparse

# Cloudflare configuration
# Using shell environment variables
#
# $ export CF_API_EMAIL='user@example.com'
# $ export CF_API_KEY='00000000000000000000000000000000'
# $ export CF_API_CERTKEY='v1.0-...'
# $
# These are optional environment variables; however, they do override the values set within a configuration file.
#
# Using configuration file to store email and keys
#
# $ cat ~/.cloudflare/cloudflare.cfg
# [CloudFlare]
# email = user@example.com
# token = 00000000000000000000000000000000
# certtoken = v1.0-...
# extras =


class CloudFlareHelper:

    def __init__(self, zone_name, debug=False):
        self.cf = CloudFlare.CloudFlare(debug=debug)
        self.zone_name = zone_name
        self.zone_id = self.get_zoneid()

    def get_zoneid(self):
        # query for the zone name and expect only one value back
        zones = []
        try:
            zones = self.cf.zones.get(params={'name': self.zone_name, 'per_page': 1})
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones.get {} {} - api call failed'.format(e, e))
        except Exception as e:
            exit('/zones.get - {} - api call failed'.format(e))

        if len(zones) == 0:
            exit('No zones found')

        # extract the zone_id which is needed to process that zone
        zone = zones[0]
        return zone['id']

    def get_hostid(self, hostname):
        # request the DNS records from that zone
        dns_records = []
        try:
            dns_records = self.cf.zones.dns_records.get(self.zone_id)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones/dns_records.get %d %s - api call failed' % (e, e))

        dns_record =  [dr for dr in dns_records if dr['name'] == hostname]
        return dns_record[0]['id']

    def print_cloudflare_zone_info(self):

        # print the results - first the zone name
        print(self.zone_id, self.zone_name)

        # request the DNS records from that zone
        try:
            dns_records = self.cf.zones.dns_records.get(self.zone_id)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit('/zones/dns_records.get %d %s - api call failed' % (e, e))

        # then all the DNS records for that zone
        for dns_record in dns_records:
            r_name = dns_record['name']
            r_type = dns_record['type']
            r_value = dns_record['content']
            r_id = dns_record['id']
            print('\t', r_id, r_name, r_type, r_value)

    def update_dns(self, hostname, ip):
        dns_post_data = {'name': hostname, 'type': 'A', 'content': ip}
        r = self.cf.zones.dns_records.put(self.zone_id, '8782e0bee568cb099b37826e4c53f1b8', data=dns_post_data)
        print(r)


def get_current_external_ip():
    current_ip = get('https://api.ipify.org').text
    return current_ip


def get_dns_ip(hostname):
    configured_ip = gethostbyname(hostname)
    return configured_ip


def process_command_line():
    parser = argparse.ArgumentParser(description='Dynamic DNS Update for CloudFlare')
    parser.add_argument('-z', '--zone_id', required=True, metavar='example.com', help='CloudFlare zone name (your domain)')
    parser.add_argument('-a', '--hostname', required=True, metavar='www.example.com', help='Hostname for dns search/update')
    return parser.parse_args()

def main():
    args = process_command_line()
    current_ip = get('https://api.ipify.org').text
    configured_ip = get_dns_ip('pro.mikenoe.com')
    cloud_flare_helper = CloudFlareHelper(args.zone_id)
    # update_dns('pro.mikenoe.com', current_ip)
    cloud_flare_helper.print_cloudflare_zone_info()
    if current_ip != configured_ip:
        print('Configured ip is incorrect. Updating...')
    print('My public IP address is: {}'.format(current_ip))
    print('My DNS IP address is: {}'.format(configured_ip))


if __name__ == "__main__":
    exit(main())
