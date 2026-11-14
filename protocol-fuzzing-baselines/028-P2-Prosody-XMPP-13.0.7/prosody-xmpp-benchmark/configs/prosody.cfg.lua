daemonize = false
pidfile = false
data_path = "/tmp/prosody-data"
log = { { levels = { min = "info" }, to = "console" } }
interfaces = { "127.0.0.1" }
c2s_interfaces = { "127.0.0.1" }
c2s_ports = { 5222 }
s2s_ports = { }
c2s_require_encryption = false
allow_unencrypted_plain_auth = true
authentication = "anonymous"
modules_enabled = {
	"disco";
	"saslauth";
	"tls";
	"ping";
	"version";
	"uptime";
	"time";
	"roster";
	"private";
	"vcard_legacy";
}
modules_disabled = { "s2s" }
ssl = {
	certificate = "/opt/benchmark/configs/localhost.crt";
	key = "/opt/benchmark/configs/localhost.key";
}
VirtualHost "example.test"
