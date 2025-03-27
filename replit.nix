{pkgs}: {
  deps = [
    pkgs.unixODBC
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
