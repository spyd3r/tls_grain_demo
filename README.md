# tls_grain_demo

1. [Build](https://docs.docker.com/reference/commandline/build/ "Build a docker image") an image from the Dockerfile:  
<code>docker build --rm=true -t="salt-apache"</code>
2. Install salt-master and configure it to [auto_accept minion keys](http://docs.saltstack.com/en/latest/ref/configuration/master.html#auto-accept "Auto Accepting Keys")
3. Spin up some docker containers from the <code>salt-apache</code> docker image created in step 1:  
<code>for i in {1..5}; do docker run --privileged --hostname=salt-test-$i --add-host=salt:your_salt_master_ip -p 800$i:443 -p 810$i:80 --name=salt-minion$i -e "ADDR=172.17.0.1$i" -d salt-apache; done</code>
4. Make sure the minions are listed on the Salt master:  
<code>salt-key -L</code>
5. Run the initialize.sls state file on all minions to set up apache to use mod_ssl, create a local certificate authority, generate certificates, create a virtual interface, and get services started:  
<code>salt '**' state.sls apache.initialize</code>  
*** Note: In order for salt to locate apache.initialize, you'll need an apache folder in your Salt master's [file_roots](http://docs.saltstack.com/en/latest/ref/file_server/file_roots.html "File Roots") base directory  
** If your file_roots base is /srv/salt, create a subdirectory called 'apache' and copy initialize.sls into it
6. Create a directory called '_grains' in your file_roots base directory and copy the tls grain file (v4.py) into it:  
<code>mkdir /srv/salt/_grains && cp v4.py /srv/salt/_grains</code>
7. Sync the grain to the minions:  
<code>salt '*' saltutil.sync_grains</code>
8. You're ready to get TLS data back via the grain. Tell salt to get the cert grain from a minion:  
<code>salt 'salt-test-1' grains.get cert</code>
