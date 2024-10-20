output "ipv4" {
  value = digitalocean_droplet.dev_droplet.ipv4_address
}

output "domain" {
  value = digitalocean_record.dev.fqdn
}

output "droplet_id" {
  value = digitalocean_droplet.dev_droplet.id
}

output "droplet_name" {
  value = digitalocean_droplet.dev_droplet.name
}