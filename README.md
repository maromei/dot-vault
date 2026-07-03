# Reference

## Config Directory

```
└ ~/.config/dot-vault
  └ modules
    └ <MODULE_NAME>
      ├ module_config.toml
      └ install_scripts
        ├ `<TARGET_1>.sh`
        └ `<TARGET_2>.ps1`
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
dot-vault module install <TARGET>
```

- `<TARGET>` will match to the start of the script files.
  The file endings may be omitted.
- if only one install script exists, `<TARGET>` may be omitted.

## Check installed

- script that checks whether a module is already installed

```bash
dot-vault module check installed `<TARGET>`
```

- `<TARGET>` will match to the start of the script files.
  The file endings may be omitted.
- if only one install script exists, `<TARGET>` may be omitted.

1. The method searches for the script under
   `modules/<MODULE_NAME>/check_installed/<TARGET>*`.
3. Relevant scripts found are executed using the `shell` value in the Modules config file.
4. It passes the `DOT_VAULT_RESULT_FILE` environment variable
   containing a path to a temporary TOML file.
5. The `check_installed` script writes `installed = true` or `installed = false`
   together with other potential information
   to that TOML file and exits with `0`. For more info on the
6. The TOML file is pased for relevant info.

# TODO

## Check installed - flag force update

- provide flag so modules, which are already installed, can be updated
- only update modules **once**
  - if module is present as multiple dependencies, do not re run them again

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

## Refactor: Move get_module_install_script to path module

## Refactor: Make get_module_install_script use the new MoreThanOneFileFound exception

## Refactor: Exception as value using cflow

- f.e. the check_installed workflow has many possible issues
- currently python error gets raised on cli method when module does not exist
- i can catch the method, but prefer to returne exception

# Dev environment

- linting via `ruff`
- typechecking via `basedpyright`
- task runner using `just`
- tests via `pytest`
- all tools listed in dev-dependency section of the `pyproject.toml`
