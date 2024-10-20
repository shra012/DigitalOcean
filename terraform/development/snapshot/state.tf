data "terraform_remote_state" "dev_droplet_state" {
  backend = "remote"
  config = {
    organization = "digitalocean-shra012"
    workspaces = {
      name = "development-droplet"
    }
  }
}