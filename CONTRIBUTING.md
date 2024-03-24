# Contributing to Toshy

## Base PRs on the `dev_beta` branch if you can

I do most of my testing in the `dev_beta` branch, and then merge it with `main` if it doesn't seem to be causing any problems. So if you want to submit a pull request rather than just opening an issue, it would be most convenient for me if it were based on the `dev_beta` branch.  

## Testing your modifications before submitting a PR

In testing I try to install Toshy on a "fresh" snapshot (i.e., just installed, updated, no non-default packages installed) of more than one completely different type of Linux distro, in a virtual machine, to verify that a moderate to major change hasn't caused an unforeseen issue. If you have a PR containing more than just a new shortcut remap or new keymap, it would be a really good idea to be able to test your modified branch for completeness before submitting the PR. Other than what happens when the Toshy installer creates the Python virtual environment and installs the `pip` packages, there's no "compiling" to be done with this project, currently. Just download the zip from your new branch like you would from the main Toshy repo, and try to install it on a clean system.  

It's quite difficult to really start with a clean system and be able to test repeatedly from a clean state unless you use something like GNOME Boxes or Virt-Manager, and take snapshots of the clean "just installed" state and after applying system updates (and before attempting to install Toshy). With a snapshot you can just keep revertng the virtual machine state back to before Toshy tried to install any packages, which is a critical part of testing the whole process. 

Less complicated things like a new keymap or app class or shortcut remap don't really need this kind of testing. Just do your best to verify that a new remap actually uses the correct physical equivalent key locations that are used for that combo in macOS, on the equivalent application, on an Apple keyboard.  

§ The End.  
