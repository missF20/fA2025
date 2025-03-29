{pkgs}: {
  deps = [
    pkgs.unzip
    pkgs.wget
    pkgs.sqlite
    pkgs.unixODBC
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
