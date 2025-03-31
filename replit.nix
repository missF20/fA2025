{pkgs}: {
  deps = [
    pkgs.jq
    pkgs.unzip
    pkgs.wget
    pkgs.sqlite
    pkgs.unixODBC
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
