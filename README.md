# Reference

## Config Directory

```
└ ~/.config/dot-vault
  └ modules
    └ <MODULE_NAME>
      ├ module_config.toml
      └ install_scripts
        ├ `<ENVIRONMENT_1>.sh`
        └ `<ENVIRONMENT_2>.ps1`
```

## Modules

- Some tool or collection of tools
- contains:
    - install_script

### Config

- Each module might contain a `module_config.toml`.
- All fields are optional
- The top level category has to be either `[dot-vault.module]` or nothing

```toml
[dot-vault.module]
dependencies = ["module_1", "module_2"]
shell = "/bin/csh"  # defaults to whatever shell the user is currently running dot-vault from
```

### Install

```bash
dot-vault module install <ENVIRONMENT>
```

- `<ENVIRONMENT>` will match to the start of the script files.
  The file endings may be omitted.
- if only one install script exists, `<ENVIRONMENT>` may be omitted.
