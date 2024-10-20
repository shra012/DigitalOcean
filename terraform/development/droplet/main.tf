resource "digitalocean_droplet" "dev_droplet" {
  # CURL to get the droplet size and region avalability.
  # curl -X GET \
  #   -H "Content-Type: application/json" \
  #   -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  #   "https://api.digitalocean.com/v2/sizes" | jq '.sizes[] | select(.price_monthly <= 6)
  # curl to get the droplet image id or slug.
  #  curl -X GET \
  #   -H "Content-Type: application/json" \
  #   -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  #   "https://api.digitalocean.com/v2/images?type=Ubuntu&page=1&per_page=196" | jq '.images[] | select((.distribution == "Ubuntu") and (.public == true))'
  # curl -X GET \
  #   -H "Content-Type: application/json" \
  #   -H "Authorization: Bearer $DIGITALOCEAN_TOKEN" \
  #   "https://api.digitalocean.com/v2/images?type=Ubuntu&page=1&per_page=196" | jq '[.images[] | select((.distribution == "Ubuntu") and (.public == true))]' | jq '.[] | {id, name, distribution, slug}'
  image = "ubuntu-22-04-x64" # Changed to LTS version for compatibility
  name   = "dev-ubuntu-s-1vcpu-1gb-amd-blr1"
  region = "blr1"
  size   = "s-1vcpu-1gb-amd"
  ssh_keys = [data.digitalocean_ssh_key.macbook_air_ssh_public_key.id]
  tags = ["dev", "docker"]
  user_data = templatefile("${path.module}/cloud-init/cloud-init.yaml", {
    digitalocean_token = var.do_token
  })
}

resource "digitalocean_record" "dev" {
  domain = "shra012.com"
  type   = "A"
  name   = "dev"
  ttl    = 300
  value  = digitalocean_droplet.dev_droplet.ipv4_address
}