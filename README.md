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

# TODO

## Flavor

- each module can have flavors
    - f.e. different themes for a terminal
- flavors live in subdirectory `flavors` of module
    - the `flavors` subdirectory essentially mirrors the general module directory
- are simple scripts executed post, pre or instead of install
    - how it behaves depends on the name
    - `arch_pre.sh` runs before regular `arch.sh`
    - `arch.sh` replaces regular `arch.sh`
    - `arch_post.sh` runs after regular `arch.sh`

```text
└ ~/.config/dot-vault/
  └ modules/
    └ <MODULE_NAME>/
      ├ module_config.toml
      ├ install_scripts/
      │ └ arch.sh
      └ flavors/
        └ theme_1/
          └ install_scripts/
            ├ arch_pre.sh
            ├ arch.sh
            └ arch_post.sh
```

- the flavor gets installed via the `--flavor` flag on
  `dot-vault module install <MODULE_NAME> --flavor <FLAVOR_NAME>`
- stuff like the `check_installed` scripts cannot be overridden since there
  is no 'state'
  - we do not know which flavor is installed

## Check installed

- have script to check whether something is installed
- should also be able to provide a name, similar to the install_scripts (ie `arch.sh`)
- should be used when installing dependencies

### Interface for check

- check gets called
- environment variable `DOT_VAULT_RESULT_FILE` contains path to `TOML` file to which
  results are written
- script needs to write `installed = true` or `installed = false` to file
  - generally any valid toml can be passed back to `dot-vault`
  - can be expanded later on

## Check installed - flag force update

- provide flag so modules, which are already installed, can be updated
- only update modules **once**
  - if module is present as multiple dependencies, do not re run them again
