# toggl-hammer
toggl command line interface for lazy people.

![](https://i.imgur.com/EQGRTp8.png)

#### Who this is for:
People who need to quickly create hourly toggl entries without sensitivity for time of day (all entries are at 09:00 or however DST screws that up).

#### Who this is not for:
People who need to specify times and descriptions for their entries.

## Setup:

**Requires python3.**

Get your toggl API key from your account settings page and add it as an environment variable to your `.bashrc` or `.bash_profile` (macOS).

    export TOGGL_API_KEY=[YOUR KEY HERE]

Optionally, add an extra variable to set your time entry as billable:

    export TOGGL_BILLABLE=True

And then install with pip (from parent directory):

    pip3 install toggl_hammer

## Usage:

toggl\_hammer may be invoked with or without a "week range" argument, defaulting to 2 weeks:

    toggl_hammer 4

At the date prompt, you may supply either a single index (i.e., "1"), or a range (i.e., "1-5").

Exit with `ctrl + c`.
