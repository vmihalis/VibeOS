#!/usr/bin/env bash
# VibeOS archiso profile definition
# Defines the basic configuration for building the ISO

iso_name="vibeos"
iso_label="VIBEOS_$(date +%Y%m%d)"
iso_publisher="VibeOS Project <https://github.com/vibeos>"
iso_application="VibeOS Live/Installation Medium"
iso_version="0.1.0-alpha"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito' 'uefi-x64.systemd-boot.esp' 'uefi-x64.systemd-boot.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M' '-Xdict-size' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:0400"
  ["/root"]="0:0:750"
)