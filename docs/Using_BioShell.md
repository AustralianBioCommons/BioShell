## Using BioShell

This section describes how to launch a virtual machine using BioShell and what functionality is available once the instance is running.

This guide is non-exhaustive. For usage instructions, see the [BioShell Guide](https://sih.tools/bioshell-guide).

### Launching a BioShell VM

Launch a new instance by following the steps in [Launch an Instance](#launch-an-instance).

When you reach the Source section, select Image and choose BioShell instead of a standard Ubuntu image. If the image was built successfully, no other changes are required

Once the instance is active, connect to it via SSH using the selected 
key pair.
```
ssh -i /path/to/your/key <remote_user>@<bioshell_ip>
```

### MOTD / Welcome Banner

Every SSH login to a BioShell VM shows a welcome banner with a live snapshot of the environment: the number of software modules currently available and whether CVMFS is mounted, plus a quick-reference list of common commands (`module avail`, `shelley search`, `shelley interactive`).

The banner is generated dynamically on each login by `/etc/update-motd.d/99-bioshell` (installed via `run-parts`/`pam_motd`), so it always reflects the current state of the instance rather than a static message baked into the image.

To customize the banner's content or styling, edit [build/ansible/roles/motd/files/99-bioshell](build/ansible/roles/motd/files/99-bioshell) and rebuild the image (or copy the updated script onto a running instance for a quick preview).

### Tools Available in BioShell

BioShell includes a curated set of commonly used bioinformatics and workflow tools, exposed through the environment modules system.

#### modules

The image should include the following applications:
- Singularity
- SHPC
- Spack
- Ansible
- Jupyter Notebook
- RStudio
- Nextflow
- Snakemake
- CernVM-FS client

Check available modules with:
```
module avail
```

To use an application, load it with:
```
module load <app>
```
#### CernVM-FS (CVMFS)

This image uses CernVM-FS (CVMFS) to provide access to shared bioinformatics software and datasets without installing them locally on the VM.

Access CVMFS repositories:
```
ls /cvmfs/data.galaxyproject.org
ls /cvmfs/singularity.galaxyproject.org

```
For an explanation of what CVMFS is, how it works, and how it is used in BioShell, see [CVMFS documentation](https://cvmfs.readthedocs.io/en/stable/).

#### R and RStudio
`R` is pre-installed system-wide on the VM and is available without loading a module.

You can run R directly:
```
R
```

The `R` module exists for visibility within the module system and to maintain consistency with other applications. Loading it ensures the correct PATH configuration but is not required to use R.
```
module load R
```
RStudio Server (Recommended Interface) provides a browser-based interface for working with R.

To access RStudio load the module:
```
module load rstudio
```

This will display:
- Login instructions
- URL format for accessing RStudio
- Username and password requirements
- Commands to start the RStudio service

Start RStudio Server
```
sudo rstudio-server start
```
Then open in your browser:
```
http://<server-ip>:8787
```
Login using:
- Username: your Linux username (e.g., ubuntu)
- Password: your Linux account password

If you have not set a password yet:
```
sudo passwd $USER
```

#### shelley

shelley is a command-line assistant built into BioShell to help you find, explore, and install bioinformatics tools. It answers questions in plain language and can locate software available through the image's installed package managers and module system.

shelley is available system-wide and requires no module loading:
```
shelley --help
```

**Key commands:**

| Command | Description |
|---|---|
| `shelley search "<function>"` | Find tools by describing what you want to do |
| `shelley find <tool>` | Look up a specific tool by name |
| `shelley build <tool>` | Install or build a tool |
| `shelley interactive` | Start an interactive session for guided assistance |

**Examples:**
```
# Find tools for quality control
shelley search "quality control"

# Look up samtools
shelley find samtools

# Check available versions of STAR
shelley versions STAR

# Launch interactive mode for guided help
shelley interactive
```
