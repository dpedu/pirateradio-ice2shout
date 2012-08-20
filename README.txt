pirateradio-ice2shout

a utility to mirror an icecast2 stream to shoutcast servers

pirateradio-ice2shout connects to icecast2 streams as ice2shout.py/1.1 and streams content to the target shoutcast server. metadata is updated automatically via shoutcast's web GUI when updates are pushed by icecast2.

developed by dave pedu for use by pirateradio.rit.edu

configuration options (found in header of script):

icecast_host: icecast2 server ip address or hostname
icecast_port: icecast2 server port (icecast default = 8000)
icecast_mount: icecast2 mount name

shoutcast_host: shoutcast server ip address or hostname
shoutcast_port: shoutcast web interface port
shoutcast_password: shoutcast source password
shoutcast_admin_password: shoutcast admin password