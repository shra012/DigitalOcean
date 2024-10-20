resource "digitalocean_droplet_snapshot" "droplet_snapshot" {
  droplet_id = data.terraform_remote_state.dev_droplet_state.outputs.droplet_id
  name       = "snapshot-${data.terraform_remote_state.dev_droplet_state.outputs.droplet_name}"
}