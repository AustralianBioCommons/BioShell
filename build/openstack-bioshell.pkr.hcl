packer {
  required_plugins {
    openstack = {
      version = ">= 1.1.2"
      source  = "github.com/hashicorp/openstack"
    }

    ansible = {
      version = ">= 1.1.1"
      source  = "github.com/hashicorp/ansible"
    }
  }
}

variable "flavor" {
  type = string
}

variable "source_image" {
  type = string
}

variable "networks" {
  type    = list(string)
  default = null
}

variable "availability_zone" {
  type    = string
  default = null
}

variable "volume_size" {
  type    = number
  default = 20
}

variable "platform" {
  type = string
}

variable "image_version" {
  type    = string
  default = "1.0.0"
}

source "openstack" "ubuntu" {
  image_name        = "bioshell-v${var.image_version}"
  flavor            = var.flavor
  ssh_username      = "ubuntu"
  volume_size       = var.volume_size
  networks          = var.networks != null ? var.networks : null    
  availability_zone = var.availability_zone != null ? var.availability_zone : null

  source_image_filter {
    filters {
      name       = var.source_image
      visibility = "public"
    }
  }
}

build {
  sources = ["source.openstack.ubuntu"]

  # 1. Install everything
  provisioner "ansible" {
    playbook_file = "ansible/build-bioshell.yml"
    extra_arguments = [
      "--extra-vars", "ansible_user=ubuntu platform=${var.platform}"
    ]
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SCP_IF_SSH=True"
    ]
    use_proxy = false
  }

  # 2. Validate — runs after install, before image is saved
  provisioner "ansible" {
    playbook_file = "ansible/test-bioshell.yml"
    extra_arguments = [
      "--extra-vars", "ansible_user=ubuntu platform=${var.platform}"
    ]
    ansible_env_vars = [
      "ANSIBLE_HOST_KEY_CHECKING=False",
      "ANSIBLE_SCP_IF_SSH=True"
    ]
    use_proxy = false
  }
}