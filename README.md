
# Pshaw!

Pshaw is like `ssh-agent` but for passwords -- you enter your password the first time you connect to a host but then nevermore. The passwords are never stored on disk; only in the memory of an `ssh-agent`-like daemon process. The ssh authentication is handled by [sshpass](https://sourceforge.net/projects/sshpass).

This approach is less secure and less convenient than ssh keys, and should only be used if you would otherwise store your password in plaintext on disk.

> :warning: **2020-02-12: I'm retiring this in favor of [pass-sshpass](https://github.com/cooijmanstim/pass-sshpass), which is much simpler and effectively uses `gpg-agent` to avoid frequent password re-entry.**

## Usage

```
pshaw <realm> ssh [...]
```

where `realm` is an arbitrary string used to select a particular password, e.g. the name of the host or network it is associated with.

Example session:

```
$ pshawd &   # ensure the daemon is running
$ pshaw test ssh localhost
test password (will be stored in pshawd): 
Last login: Mon Dec 18 15:51:32 2017 from ::1
user@localhost ~ $ logout
Connection to localhost closed.
$ pshaw test ssh localhost
Last login: Mon Dec 18 15:51:32 2017 from ::1
user@localhost ~ $ logout
Connection to localhost closed.
$ touch /tmp/foo
$ pshaw test rsync /tmp/foo localhost:/tmp/bar
sending incremental file list
foo

sent 92 bytes  received 35 bytes  84.67 bytes/sec
total size is 0  speedup is 0.00
```

## Dependencies

AFAIK, Pshaw requires at least Python 3.3, the `paramiko` package, and the `sshpass` utility. Note `paramiko` requires the `python-gssapi` pip package; it does not require `gssapi`.

## Limitations

  * Exceptional situations such as a wrong password may not be dealt with, and most exceptions will go uncaught. We can deal with things as they come up.
  * There is no way to forget or update a password other than to wait for it to expire or kill/restart `pshawd`. If you mistyped your password, you can store a different one under a different realm name.
  * All the limitations of `sshpass` apply.

## Security considerations

  * You must trust the root user.
  * You must trust your own account; if it is compromised (e.g. you didn't lock your laptop), an attacker can interact with the daemon and extract the password from it.
  * You must trust the `sshpass` binary and the server you are connecting to, because they will process the password in plaintext.
  * `pshaw` communicates with `pshawd` through a local ssh connection which is authenticated using ssh keys.  Ensure these are readable only by you, as anyone who can read them can impersonate either `pshaw` or `pshawd` and get your password.
