#!/bin/bash

# Download the container types that we want
ct=$(pveam avaliable | awk -F "[, ]+" '/debian-10-standard/{print $NF}' | echo $1)
pveam download local $ct

echo "deb http://download.proxmox.com/debian/pve buster pve-no-subscription" > /etc/apt/sources.list.d/pve-enterprise.list
apt update

# Remove the proxmox "no valid subscription" message
sed -Ezi.bak "s/(Ext.Msg.show\(\{\s+title: gettext\('No valid sub)/void\(\{ \/\/\1/g" /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
systemctl restart pveproxy.service
