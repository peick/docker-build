Vagrant.configure("2") do |config|
  config.ssh.port = 22

  config.vm.provider "docker" do |d|
    d.image = "guilhem/vagrant-ubuntu"
    d.has_ssh = true
    d.remains_running = true
  end

  config.vm.provision :shell, inline: "useradd sample-user"
end
