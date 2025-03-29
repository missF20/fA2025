{pkgs}: {
  deps = [
    pkgs.sqlite
    pkgs.unixODBC
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
