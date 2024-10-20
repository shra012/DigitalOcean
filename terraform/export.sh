#!/usr/bin/env zsh
export TF_LOG=1
export TF_VAR_do_token=$(echo $DIGITALOCEAN_TOKEN)
export TF_VAR_pvt_key=$(cat ~/.ssh/id_rsa)