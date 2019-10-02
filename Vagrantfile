# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|

  config.vm.box = "ubuntu/trusty64"

  config.vm.network :private_network, ip: '192.168.50.50'
  config.vm.synced_folder '.', '/vagrant', nfs: true

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 8000 on the guest machine.
  config.vm.network "forwarded_port", guest: 8000, host: 8000

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #

  config.vm.provider "virtualbox" do |v|
    v.customize ["modifyvm", :id, "--memory", "1024"]
  end

  # config.vm.provider "virtualbox" do |vb|
  #   # Don't boot with headless mode
  #   vb.gui = true
  #
  #   # Use VBoxManage to customize the VM. For example to change memory:
  #   vb.customize ["modifyvm", :id, "--memory", "1024"]
  # end

  # Because we want to use the client to provide its own ansible (no installing on host), we
  # need to bootstrap it here
  $provision_script = <<SCRIPT
  apt-get update && apt-get install -y --force-yes python-pip ansible
SCRIPT

  config.vm.provision "shell", inline: $provision_script

  config.vm.provision :ansibleLocal do |ansibleLocal|
    ansibleLocal.playbook = "ansible/django_server.yml"
    ansibleLocal.raw_arguments = "-i 'localhost,'"
  end

end
