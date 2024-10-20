variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
}

variable "create_snapshot" {
  description = "Set to true to create a snapshot before destroying the droplet"
  type        = bool
  default     = false
}