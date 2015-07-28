FROM centos:centos6
MAINTAINER sfoger@solutionreach.com
RUN yum -y update && yum -y install epel-release \
	httpd \
	python-devel \
	libffi-devel \
	gcc \
	pyOpenSSL
RUN yum -y install salt-minion
RUN echo "Hello world" > /var/www/html/index.html
RUN echo "DEVICE=eth0:0 \
	BOOTPROTO=static \
	ONBOOT=yes \
	IPADDR=172.17.0.2 \
	NM_CONTROLLED=yes \
	NETMASK=255.255.0.0 \
	TYPE=Ethernet " > /etc/sysconfig/network-scripts/ifcfg-eth0:0
CMD salt-minion
