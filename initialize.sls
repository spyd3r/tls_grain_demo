{% set ip_addr = salt['cmd.run']('echo $ADDR') %}
{% set eth0 = salt['cmd.run']('echo $ETH0') %}

httpd:
  service.running:
    - enable: True
    - reload: True

mod_ssl:
  pkg.installed

#replace_ssl_key:
#  file.replace:
#    - name: /etc/httpd/conf.d/ssl.conf
#    - pattern: |
#        SSLCertificateKeyFile.*
#    - repl: SSLCertificateKeyFile /etc/pki/local_ca/certs/localhost.key
#
#replace_ssl_cert:
#  file.replace:
#    - name: /etc/httpd/conf.d/ssl.conf
#    - pattern: |
#        SSLCertificateFile.*
#    - repl: SSLCertificateFile /etc/pki/local_ca/certs/localhost.crt

remove_default_ssl_conf:
  cmd.run:
    - name: mv /etc/httpd/conf.d/ssl.conf /etc/httpd/conf.d/ssl.conf.orig

install_local_ca:
  cmd.run:
    - name: salt-call tls.create_ca 'local_ca'

#create_csr:
#  cmd.run:
#    - name: salt-call tls.create_csr 'local_ca'
#
#create_self_signed_cert:
#  cmd.run:
#    - name: salt-call tls.create_ca_signed_cert 'local_ca' 'localhost'

create_csr_one:
  cmd.run:
    - name: salt-call tls.create_csr 'local_ca' CN=one.example.com

create_csr_two:
  cmd.run:
    - name: salt-call tls.create_csr 'local_ca' CN=two.example.com

#create_csr_three:
#  cmd.run:
#    - name: salt-call tls.create_csr 'local_ca' CN=three.example.com

create_self_signed_cert_one:
  cmd.run:
    - name: salt-call tls.create_ca_signed_cert 'local_ca' 'one.example.com'

create_self_signed_cert_two:
  cmd.run:
    - name: salt-call tls.create_ca_signed_cert 'local_ca' 'two.example.com'

#create_self_signed_cert_three:
#  cmd.run:
#    - name: salt-call tls.create_ca_signed_cert 'local_ca' 'three.example.com'

test_config:
  file.managed:
    - name: /etc/httpd/conf.d/test.conf
    - source: salt://apache/test.conf

restart_httpd:
  module.run:
    - name: service.restart
    - m_name: httpd
    - source:
      - salt://apache/test.conf
    - order: last

define_interfaces:
  cmd.run:
    - name: echo "DEVICE=eth0:0 BOOTPROTO=static ONBOOT=yes IPADDR=`echo $ADDR` NM_CONTROLLED=yes NETMASK=255.255.0.0 TYPE=Ethernet " > /etc/sysconfig/network-scripts/ifcfg-eth0:0 && echo "DEVICE=eth0 BOOTPROTO=static ONBOOT=yes IPADDR=`echo $ETH0` NM_CONTROLLED=yes NETMASK=255.255.0.0 TYPE=Ethernet " > /etc/sysconfig/network-scripts/ifcfg-eth0

substitue_addr:
  module.run:
    - name: file.replace
    - path: /etc/httpd/conf.d/test.conf
    - pattern: 172.17.0.X
    - repl: {{ip_addr}}

virtual_interface_up:
  cmd.run:
    - name: ifup eth0

update_hosts:
  cmd.run:
    - name: |
        echo {{ip_addr}} two.example.com >> /etc/hosts
        echo 127.0.0.1	one.example.com >> /etc/hosts
