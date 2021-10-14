import os
import sys
import requests
import CloudFlare

sys.path.insert(0, os.path.abspath('..'))


def my_ip_address():
    """Cloudflare API code - example"""

    ip_address = None
    for url in [
        "https://api.ipify.org",
        "http://myip.dnsomatic.com",
        "http://www.trackip.net/ip",
        "http://myexternalip.com/raw"
    ]:
        try:
            ip_address = requests.get(url).text
        except requests.exceptions:
            exit(f'Error: {url} - failed')
        if ip_address:
            break
    if not ip_address:
        exit('Error: Failed to get ip address')

    if ':' in ip_address:
        ip_address_type = 'AAAA'
    else:
        ip_address_type = 'A'

    return ip_address, ip_address_type


def do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type):
    """Cloudflare API code - example"""

    try:
        params = {'name': dns_name, 'match': 'all', 'type': ip_address_type}
        dns_records = cf.zones.dns_records.get(zone_id, params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit(f'Error: /zones/dns_records {dns_name} - {e} - api call failed')

    updated = False

    # update the record - unless it's already correct
    for dns_record in dns_records:
        old_ip_address = dns_record['content']
        old_ip_address_type = dns_record['type']

        if ip_address_type not in ['A', 'AAAA']:
            # we only deal with A / AAAA records
            continue

        if ip_address_type != old_ip_address_type:
            # only update the correct address type (A or AAAA)
            # we don't see this becuase of the search params above
            print(f'Ignored: {dns_name} {old_ip_address} ; wrong address family')
            continue

        if ip_address == old_ip_address:
            updated = True
            continue

        proxied_state = dns_record['proxied']

        # Yes, we need to update this record - we know it's the same address type

        dns_record_id = dns_record['id']
        dns_record = {
            'name': dns_name,
            'type': ip_address_type,
            'content': ip_address,
            'proxied': proxied_state
        }
        try:
            dns_record = cf.zones.dns_records.put(zone_id, dns_record_id, data=dns_record)
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            exit(f'Error: /zones.dns_records.put {dns_nane} - {e} - api call failed')
        print(f'Updated: {dns_name} {old_ip_address} -> {ip_address}')
        updated = True

    if updated:
        return

    # no exsiting dns record to update - so create dns record
    dns_record = {
        'name': dns_name,
        'type': ip_address_type,
        'content': ip_address
    }
    try:
        dns_record = cf.zones.dns_records.post(zone_id, data=dns_record)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit(f'Error: /zones.dns_records.post {dns_name} - {e} - api call failed')
    print(f'Created: {dns_name} {ip_address}')


def main():
    """Cloudflare API code - example"""

    dns_name = "clicksminuteper.net"

    host_name, zone_name = '.'.join(dns_name.split('.')[:2]), '.'.join(dns_name.split('.')[-2:])

    ip_address, ip_address_type = my_ip_address()

    cf = CloudFlare.CloudFlare(token=os.environ["CLOUDFLARE_API_TOKEN"])

    # grab the zone identifier
    try:
        params = {'name': zone_name}
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        exit(f'Error: /zones {e} - api call failed')
    except Exception as e:
        exit(f'Error: /zones.get - {e} - api call failed')

    if len(zones) == 0:
        exit(f'Error: /zones.get - {zone_name} - zone not found')

    if len(zones) != 1:
        exit(f'Error: /zones.get - {dns_name} - api call returned {len(zones)} items')

    zone = zones[0]

    zone_name = zone['name']
    zone_id = zone['id']

    do_dns_update(cf, zone_name, zone_id, dns_name, ip_address, ip_address_type)
    exit(0)


if __name__ == '__main__':
    main()
