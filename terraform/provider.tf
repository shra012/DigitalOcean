# This block defines the requirements for the DigitalOcean provider.
# It specifies the provider source and the version constraint.
# The "~> 2.0" constraint means any 2.x.y version, where x and y can be any number.
# It's a common convention in the Terraform community to use this syntax.
# "source" specifies the location of the provider plugin.
# "version" specifies the version constraint for the provider.
terraform {
  cloud {
    organization = "digitalocean-shra012"
    workspaces {
      name = "development"
    }
  }
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.27.0"
    }
  }
}

# This block configures the DigitalOcean provider.
# "token" is the API token used to authenticate with the DigitalOcean API.
# The value of this token is passed from the command line or from a variables file.
provider "digitalocean" {
  # TOKEN is automatically fetched if it is exported as an environment varible `DIGITALOCEAN_TOKEN`. 
  token = var.do_token
}